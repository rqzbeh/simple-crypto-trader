"""
Multi-Provider LLM Client with Auto-Failover and Budget Tracking
Supports Groq (primary) and Cloudflare AI Workers (fallback)
Both providers use OpenAI-compatible API for standardization

MODEL SELECTION RATIONALE:
- Llama 3.3 70B Versatile: Superior reasoning for complex trading analysis
  * 70B parameters = excellent for nuanced sentiment and market psychology
  * Versatile variant = balances accuracy and speed
  * Outstanding at news-driven reasoning and avoiding hallucinations
  * Reliable on Groq infrastructure for real-time signals
  
- Cloudflare AI Workers (Fallback):
  * Free tier with models like @cf/meta/llama-3.2-3b-instruct
  * Fast edge computing for backup when Groq limits hit
  * Cost-effective redundancy for 24/7 trading
  * Uses OpenAI-compatible Gateway API

WHY MULTI-PROVIDER:
- Groq primary for speed/accuracy, Cloudflare free fallback for limits
- Automatic failover prevents downtime during high-volume news
- Budget tracking ensures cost control
- Optimized for short-term crypto trades (2h duration)
- Unified OpenAI-compatible API reduces code complexity

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
    Uses OpenAI-compatible API for all providers (standardized interface).
    
    Provider Priority:
    1. Groq (llama-3.1-8b-instant) - Primary, superior speed & quality
    2. Cloudflare AI Workers (@cf/meta/llama-3.2-3b-instruct) - Backup, fast & free
    
    Features:
    - OpenAI-compatible API for all providers (simplified, standardized)
    - Auto-retry with exponential backoff
    - Health tracking per provider
    - Smart provider selection based on error history
    - Detailed logging of failures and successes
    - Budget tracking to stay within free-tier limits
    """
    
    def __init__(self):
        # Provider configurations - both use OpenAI-compatible API
        # Reference: https://developers.cloudflare.com/workers-ai/configuration/open-ai-compatibility/
        cloudflare_account_id = os.getenv('CLOUDFLARE_ACCOUNT_ID', '')
        cloudflare_api_token = os.getenv('CLOUDFLARE_API_TOKEN')
        
        self.providers = {
            'groq': {
                'name': 'Groq',
                'api_key': os.getenv('GROQ_API_KEY'),
                'base_url': 'https://api.groq.com/openai/v1',
                'model': os.getenv('GROQ_MODEL', 'llama-3.1-8b-instant'),
                'success_count': 0,
                'error_count': 0,
                'total_time': 0.0,
                'avg_time': 0.0,
                'last_error': None
            }
        }
        
        # Only add Cloudflare if account ID is provided (required for endpoint URL)
        if cloudflare_account_id:
            self.providers['cloudflare'] = {
                'name': 'Cloudflare AI Workers',
                'api_key': cloudflare_api_token,  # May be None for free tier
                # Cloudflare Workers AI with OpenAI-compatible endpoint
                # Format: https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/v1
                'base_url': f'https://api.cloudflare.com/client/v4/accounts/{cloudflare_account_id}/ai/v1',
                'model': '@cf/meta/llama-3.2-3b-instruct',  # Fast 3B model
                'success_count': 0,
                'error_count': 0,
                'total_time': 0.0,
                'avg_time': 0.0,
                'last_error': None,
                'requires_auth': cloudflare_api_token is not None  # Track if auth is available
            }
        
        self.request_history = {
            'groq': deque(maxlen=100)
        }
        if 'cloudflare' in self.providers:
            self.request_history['cloudflare'] = deque(maxlen=100)
        
        self.lock = Lock()
        
        # Initialize budget tracker
        self.usage_tracker = LLMUsageTracker()
        
        # Validate at least one provider is configured
        if not self.providers:
            raise ValueError("No LLM providers configured! Set GROQ_API_KEY")
        
        groq_configured = self.providers.get('groq', {}).get('api_key') is not None
        if not groq_configured and 'cloudflare' not in self.providers:
            raise ValueError("No LLM providers configured! Set GROQ_API_KEY or (CLOUDFLARE_ACCOUNT_ID + CLOUDFLARE_API_TOKEN)")
        
        print(f"✓ Multi-Provider LLM Client initialized (OpenAI-compatible API)")
        provider_order = self._get_provider_order()
        if provider_order:
            primary_id = provider_order[0]
            print(f"  - Primary: {self.providers[primary_id]['name']} ({self.providers[primary_id]['model']})")
            if len(provider_order) > 1:
                fallback_id = provider_order[1]
                print(f"  - Fallback: {self.providers[fallback_id]['name']} ({self.providers[fallback_id]['model']})")
        
        # Show budget status
        for provider_id, provider in self.providers.items():
            # Groq always requires API key; Cloudflare may work without (free tier)
            if provider.get('api_key') or (provider_id == 'cloudflare' and not provider.get('requires_auth')):
                budget = self.usage_tracker.get_remaining_budget(provider_id, provider['model'])
                auth_status = "authenticated" if provider.get('api_key') else "unauthenticated"
                print(f"  - {provider['name']} budget: {budget['used_today']}/{budget['limits']['requests_per_day']} used today ({auth_status})")
    
    def _get_provider_order(self):
        """Get provider order based on health (prefer providers with fewer errors)"""
        providers = []
        for pid, prov in self.providers.items():
            # Groq requires API key; Cloudflare may work without for free tier
            has_auth = prov.get('api_key') is not None
            requires_auth = prov.get('requires_auth', True)  # Default True for backwards compat
            
            if has_auth or not requires_auth:
                error_rate = prov['error_count'] / (prov['success_count'] + prov['error_count'] + 1)
                providers.append((pid, error_rate))
        
        # Sort by error rate (ascending), but prioritize Groq (better quality)
        providers.sort(key=lambda x: (0 if x[0] == 'groq' else 1, x[1]))
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
            timeout: Request timeout in seconds (default: 3 seconds for fast trading)
            
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
            
            # Skip if authentication required but not available
            requires_auth = provider.get('requires_auth', True)
            has_auth = provider.get('api_key') is not None
            
            if requires_auth and not has_auth:
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
                    
                    # Use OpenAI-compatible API for all providers
                    headers = {'Content-Type': 'application/json'}
                    if provider.get('api_key'):
                        headers['Authorization'] = f"Bearer {provider['api_key']}"
                    
                    response = requests.post(
                        f"{provider['base_url']}/chat/completions",
                        headers=headers,
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
                        
                        # Parse OpenAI-compatible response format
                        # Standard format: data['choices'][0]['message']['content']
                        if isinstance(data, dict) and 'choices' in data and data['choices']:
                            content = data['choices'][0]['message']['content']
                        else:
                            # If response doesn't match OpenAI format, log and raise error
                            raise Exception(f"Unexpected response format from {provider['name']}: {str(data)[:200]}")
                        
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
