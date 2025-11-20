"""
Multi-Provider LLM Client with Auto-Failover and Budget Tracking
Supports Groq (primary) and OllamaFreeAPI (fallback via Python package)

MODEL SELECTION RATIONALE:
- Llama 3.3 70B: Best open-source model for reasoning and analysis
  * 70B parameters = smart enough for market analysis
  * Trained on diverse data including finance/news
  * Excellent at sentiment analysis and reasoning
  * Fast on Groq infrastructure (400+ tok/s)
  * Better than GPT-3.5, competitive with GPT-4
  
- Alternative models available on Groq:
  * Mixtral 8x7B: Mixture of experts, very fast, good quality
  * Gemma 2 9B: Google's model, fast but smaller
  * Choose Llama 3.3 70B for best accuracy vs speed balance

WHY MULTI-PROVIDER:
- Different APIs = true redundancy (if one down, other works)
- Separate rate limits = stay under free tiers
- Groq (14.4k/day) + OllamaFreeAPI (100/hr free tier) = plenty for trading

BUDGET TRACKING:
- Automatic usage tracking per provider and model
- Respects free-tier limits from config.py
- Prevents hitting rate limits
- Saves usage to llm_usage.json
- Daily and hourly limit enforcement
"""

import os
import json
import requests
import time
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from collections import deque
from threading import Lock

# Import config for rate limits
try:
    from config import get_llm_limits, LLM_USAGE_FILE
except ImportError:
    # Fallback if config.py not available
    def get_llm_limits(provider, model):
        return {'requests_per_day': 1000, 'requests_per_minute': 30}
    LLM_USAGE_FILE = 'llm_usage.json'


class LLMUsageTracker:
    """Tracks LLM usage to stay within free-tier limits"""
    
    def __init__(self, usage_file=None):
        self.usage_file = usage_file or LLM_USAGE_FILE
        self.lock = Lock()
        self.usage = self._load_usage()
    
    def _load_usage(self):
        """Load usage from file"""
        try:
            if os.path.exists(self.usage_file):
                with open(self.usage_file, 'r') as f:
                    data = json.load(f)
                    # Reset if it's a new day
                    if data.get('date') != datetime.now().strftime('%Y-%m-%d'):
                        return self._init_usage()
                    return data
        except Exception as e:
            print(f"⚠ Error loading usage file: {e}")
        return self._init_usage()
    
    def _init_usage(self):
        """Initialize usage structure"""
        return {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'providers': {},
            'last_reset': datetime.now().isoformat()
        }
    
    def _save_usage(self):
        """Save usage to file"""
        try:
            with open(self.usage_file, 'w') as f:
                json.dump(self.usage, f, indent=2)
        except Exception as e:
            print(f"⚠ Error saving usage file: {e}")
    
    def check_budget(self, provider, model):
        """Check if we have budget remaining for this provider/model"""
        with self.lock:
            # Reset if new day
            if self.usage.get('date') != datetime.now().strftime('%Y-%m-%d'):
                self.usage = self._init_usage()
                self._save_usage()
            
            # Get limits
            limits = get_llm_limits(provider, model)
            
            # Get current usage
            provider_key = f"{provider}:{model}"
            if provider_key not in self.usage['providers']:
                self.usage['providers'][provider_key] = {
                    'requests_today': 0,
                    'requests_this_hour': 0,
                    'hour_start': datetime.now().isoformat()
                }
            
            usage = self.usage['providers'][provider_key]
            
            # Check hourly reset
            hour_start = datetime.fromisoformat(usage['hour_start'])
            if datetime.now() - hour_start > timedelta(hours=1):
                usage['requests_this_hour'] = 0
                usage['hour_start'] = datetime.now().isoformat()
            
            # Check limits
            if usage['requests_today'] >= limits.get('requests_per_day', float('inf')):
                return False, f"Daily limit reached ({usage['requests_today']}/{limits['requests_per_day']})"
            
            if 'requests_per_hour' in limits:
                if usage['requests_this_hour'] >= limits['requests_per_hour']:
                    return False, f"Hourly limit reached ({usage['requests_this_hour']}/{limits['requests_per_hour']})"
            
            if 'requests_per_minute' in limits:
                # Check minute limit (simplified - could be more precise)
                recent_requests = usage.get('requests_this_minute', 0)
                if recent_requests >= limits['requests_per_minute']:
                    return False, f"Minute limit reached ({recent_requests}/{limits['requests_per_minute']})"
            
            return True, "Budget available"
    
    def record_request(self, provider, model):
        """Record a request"""
        with self.lock:
            provider_key = f"{provider}:{model}"
            if provider_key not in self.usage['providers']:
                self.usage['providers'][provider_key] = {
                    'requests_today': 0,
                    'requests_this_hour': 0,
                    'hour_start': datetime.now().isoformat()
                }
            
            usage = self.usage['providers'][provider_key]
            usage['requests_today'] += 1
            usage['requests_this_hour'] += 1
            usage['requests_this_minute'] = usage.get('requests_this_minute', 0) + 1
            
            self._save_usage()
    
    def get_remaining_budget(self, provider, model):
        """Get remaining budget for provider/model"""
        with self.lock:
            limits = get_llm_limits(provider, model)
            provider_key = f"{provider}:{model}"
            usage = self.usage['providers'].get(provider_key, {
                'requests_today': 0,
                'requests_this_hour': 0
            })
            
            remaining_day = limits.get('requests_per_day', float('inf')) - usage['requests_today']
            remaining_hour = limits.get('requests_per_hour', float('inf')) - usage['requests_this_hour']
            
            return {
                'daily': remaining_day,
                'hourly': remaining_hour,
                'used_today': usage['requests_today'],
                'limits': limits
            }


class MultiProviderLLMClient:
    """
    Multi-provider LLM client with automatic failover and budget tracking.
    
    Provider Priority:
    1. Groq (llama-3.3-70b-versatile) - Primary, fastest
    2. OllamaFreeAPI (deepseek-r1:7b) - Fallback, free distributed API
    
    Features:
    - Auto-retry with exponential backoff
    - Health tracking per provider
    - Smart provider selection based on error history
    - Detailed logging of failures and successes
    - Budget tracking to stay within free-tier limits
    """
    
    def __init__(self):
        # Try to import ollamafreeapi (fallback provider)
        self.ollama_client = None
        try:
            print("⏳ Initializing OllamaFreeAPI fallback...")
            from ollamafreeapi import OllamaFreeAPI
            self.ollama_client = OllamaFreeAPI()
            print("✓ OllamaFreeAPI loaded")
        except Exception as e:
            print(f"⚠ OllamaFreeAPI unavailable: {str(e)[:100]}")
        
        # Provider configurations
        self.providers = {
            'groq': {
                'name': 'Groq',
                'api_key': os.getenv('GROQ_API_KEY'),
                'base_url': 'https://api.groq.com/openai/v1',
                'model': os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile'),
                'success_count': 0,
                'error_count': 0,
                'total_time': 0.0,
                'avg_time': 0.0,
                'last_error': None,
                'type': 'rest_api'
            },
            'ollamafree': {
                'name': 'OllamaFreeAPI',
                'api_key': 'available' if self.ollama_client else None,
                'base_url': None,
                'model': 'deepseek-r1:7b',  # Better model - more reliable and powerful
                'success_count': 0,
                'error_count': 0,
                'total_time': 0.0,
                'avg_time': 0.0,
                'last_error': None,
                'type': 'python_package'
            }
        }
        
        self.request_history = {
            'groq': deque(maxlen=100),
            'ollamafree': deque(maxlen=100)
        }
        
        self.lock = Lock()
        
        # Initialize budget tracker
        self.usage_tracker = LLMUsageTracker()
        
        # Validate at least one provider is configured
        if not any(p['api_key'] for p in self.providers.values()):
            raise ValueError("No LLM providers configured! Set GROQ_API_KEY")
        
        print(f"✓ Multi-Provider LLM Client initialized")
        print(f"  - Primary: {self.providers['groq']['name']} ({self.providers['groq']['model']})")
        if self.ollama_client:
            print(f"  - Fallback: {self.providers['ollamafree']['name']} ({self.providers['ollamafree']['model']})")
        
        # Show budget status
        for provider_id, provider in self.providers.items():
            if provider['api_key']:
                budget = self.usage_tracker.get_remaining_budget(provider_id, provider['model'])
                print(f"  - {provider['name']} budget: {budget['used_today']}/{budget['limits']['requests_per_day']} used today")
    
    def _get_provider_order(self):
        """Get provider order based on health (prefer providers with fewer errors)"""
        providers = []
        for pid, prov in self.providers.items():
            if prov['api_key']:
                error_rate = prov['error_count'] / (prov['success_count'] + prov['error_count'] + 1)
                providers.append((pid, error_rate))
        
        # Sort by error rate (ascending)
        providers.sort(key=lambda x: x[1])
        return [p[0] for p in providers]
    
    def _mark_provider_success(self, provider_id, elapsed_time):
        """Mark a successful request for a provider"""
        with self.lock:
            provider = self.providers[provider_id]
            provider['success_count'] += 1
            provider['total_time'] += elapsed_time
            provider['avg_time'] = provider['total_time'] / provider['success_count']
            provider['last_error'] = None
    
    def _mark_provider_error(self, provider_id, error_msg=None):
        """Mark an error for a provider"""
        with self.lock:
            provider = self.providers[provider_id]
            provider['error_count'] += 1
            if error_msg:
                provider['last_error'] = error_msg
    
    def chat(self, prompt=None, messages=None, temperature=0.7, max_tokens=1000, max_retries=2, timeout=3, **kwargs):
        """
        Send a chat request to LLM with automatic failover and budget tracking.
        
        Args:
            messages: List of chat messages OR None if using raw prompt
            prompt: Raw prompt string (will be wrapped automatically if provided)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            max_retries: Retry attempts per provider
            timeout: Request timeout in seconds
            
        Returns:
            str: LLM response text
            
        Raises:
            Exception: If all providers fail or budget exhausted
        """
        # Normalize input
        if prompt is not None and messages is None:
            messages = [
                {"role": "system", "content": "You are a helpful cryptocurrency analysis assistant."},
                {"role": "user", "content": prompt}
            ]
        if messages is None:
            raise ValueError("Either 'messages' or 'prompt' must be provided")

        providers_to_try = self._get_provider_order()
        all_errors = []
        
        for provider_id in providers_to_try:
            provider = self.providers[provider_id]
            
            # Skip if no API key
            if not provider['api_key']:
                continue
            
            # Check budget before attempting (only for free providers to prevent waste)
            # For Groq, let it fail naturally with rate limit errors
            if provider_id != 'groq':
                can_use, budget_msg = self.usage_tracker.check_budget(provider_id, provider['model'])
                if not can_use:
                    print(f"⚠ {provider['name']} budget exhausted: {budget_msg}")
                    all_errors.append(f"{provider['name']}: {budget_msg}")
                    continue
            
            print(f"\n🤖 Trying {provider['name']} ({provider['model']})...")
            
            for attempt in range(max_retries):
                try:
                    start_time = time.time()
                    
                    # Handle OllamaFreeAPI - simple direct call
                    if provider['type'] == 'python_package' and provider_id == 'ollamafree':
                        if not self.ollama_client:
                            raise Exception("OllamaFreeAPI not available")
                        
                        # Convert messages to prompt
                        prompt_text = "\n".join([msg['content'] for msg in messages if msg['role'] == 'user']) if messages else prompt
                        
                        # Simple direct call as per docs - FIXED parameter name
                        content = self.ollama_client.chat(
                            prompt=prompt_text,
                            model='deepseek-r1:7b',
                            temperature=temperature
                        )
                        
                        if not content:
                            raise Exception("Empty response from OllamaFreeAPI")
                        
                        elapsed = time.time() - start_time
                        self.usage_tracker.record_request(provider_id, provider['model'])
                        self._mark_provider_success(provider_id, elapsed)
                        
                        print(f"✓ {provider['name']} responded in {elapsed:.2f}s")
                        
                        return content
                    
                    # Handle REST API providers (Groq)
                    response = requests.post(
                        f"{provider['base_url']}/chat/completions",
                        headers={
                            'Authorization': f"Bearer {provider['api_key']}",
                            'Content-Type': 'application/json'
                        },
                        json={
                            'model': provider['model'],
                            'messages': messages,
                            'temperature': temperature,
                            'max_tokens': max_tokens
                        },
                        timeout=timeout
                    )
                    
                    elapsed = time.time() - start_time
                    
                    if response.status_code == 200:
                        data = response.json()
                        content = ''
                        # Try common response formats
                        if isinstance(data, dict):
                            if 'choices' in data and data['choices']:
                                choice0 = data['choices'][0]
                                if 'message' in choice0 and 'content' in choice0['message']:
                                    content = choice0['message']['content']
                                elif 'text' in choice0:
                                    content = choice0['text']
                            elif 'response' in data:
                                content = data['response']
                        if not content:
                            content = response.text.strip()
                        
                        # Record successful request
                        self.usage_tracker.record_request(provider_id, provider['model'])
                        self._mark_provider_success(provider_id, elapsed)
                        
                        # Show updated budget
                        budget = self.usage_tracker.get_remaining_budget(provider_id, provider['model'])
                        print(f"✓ {provider['name']} responded in {elapsed:.2f}s (Daily: {budget['used_today']}/{budget['limits']['requests_per_day']})")
                        
                        return content
                    else:
                        error_msg = f"HTTP {response.status_code}: {response.text[:200]}"
                        print(f"✗ {provider['name']} error: {error_msg}")
                        all_errors.append(f"{provider['name']}: {error_msg}")
                        
                        # Don't retry on certain errors
                        if response.status_code in [401, 403, 429]:
                            break
                        
                        if attempt < max_retries - 1:
                            wait_time = 2 ** attempt
                            print(f"  Retrying in {wait_time}s...")
                            time.sleep(wait_time)
                
                except RuntimeError as e:
                    # OllamaFreeAPI raises RuntimeError when no servers available or all fail
                    error_msg = f"OllamaFreeAPI unavailable: {str(e)}"
                    print(f"✗ {provider['name']} error: {error_msg}")
                    all_errors.append(f"{provider['name']}: {error_msg}")
                    # Don't retry RuntimeError - indicates fundamental server/library issues
                    break
                
                except TypeError as e:
                    # OllamaFreeAPI has internal bugs (like string indexing errors)
                    error_msg = f"OllamaFreeAPI library error: {str(e)}"
                    print(f"✗ {provider['name']} error: {error_msg}")
                    all_errors.append(f"{provider['name']}: {error_msg}")
                    # Don't retry TypeError - indicates library bugs
                    break
                
                except requests.exceptions.Timeout:
                    error_msg = f"Timeout after {timeout}s"
                    print(f"✗ {provider['name']}: {error_msg}")
                    all_errors.append(f"{provider['name']}: {error_msg}")
                    
                    if attempt < max_retries - 1:
                        print(f"  Retrying...")
                        time.sleep(1)
                
                except Exception as e:
                    error_msg = str(e)
                    print(f"✗ {provider['name']} error: {error_msg}")
                    all_errors.append(f"{provider['name']}: {error_msg}")
                    
                    if attempt < max_retries - 1:
                        print(f"  Retrying...")
                        time.sleep(1)
            
            # Mark provider as having errors after all retries failed
            self._mark_provider_error(provider_id)
        
        # All providers failed
        error_summary = "\n".join(all_errors)
        raise Exception(f"All LLM providers failed:\n{error_summary}")
    
    def get_stats(self):
        """Get statistics for all providers including budget info"""
        stats = {}
        for provider_id, provider in self.providers.items():
            budget = self.usage_tracker.get_remaining_budget(provider_id, provider['model'])
            stats[provider_id] = {
                'name': provider['name'],
                'model': provider['model'],
                'success_count': provider['success_count'],
                'error_count': provider['error_count'],
                'avg_time': provider['avg_time'],
                'last_error': provider['last_error'],
                'budget': budget
            }
        return stats
    
    def get_budget_status(self):
        """Get detailed budget status for all providers"""
        status = {}
        for provider_id, provider in self.providers.items():
            budget = self.usage_tracker.get_remaining_budget(provider_id, provider['model'])
            status[provider_id] = {
                'provider': provider['name'],
                'model': provider['model'],
                'used_today': budget['used_today'],
                'daily_limit': budget['limits']['requests_per_day'],
                'daily_remaining': budget['daily'],
                'hourly_remaining': budget['hourly'],
                'percentage_used': (budget['used_today'] / budget['limits']['requests_per_day'] * 100) if budget['limits']['requests_per_day'] else 0
            }
        return status
