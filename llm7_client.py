"""
LLM7.io API Client
A lightweight wrapper for the llm7.io API that provides a similar interface to OllamaFreeAPI
"""

import requests
import json
import time
from typing import Optional, Dict, Any
from collections import deque
from threading import Lock

class LLM7Client:
    """
    Client for llm7.io API
    Provides a chat() method compatible with the existing codebase
    
    Rate Limits (enforced):
    - 128k chars/req: Maximum request size
    - 1,500 req/h: Maximum requests per hour
    - 60 req/min: Maximum requests per minute
    - 5 req/s: Maximum requests per second
    """
    
    # Rate limit constants
    MAX_CHARS_PER_REQUEST = 128000
    MAX_REQUESTS_PER_HOUR = 1500
    MAX_REQUESTS_PER_MINUTE = 60
    MAX_REQUESTS_PER_SECOND = 5
    
    def __init__(self, api_token: str, base_url: str = "https://llm7.io/v1/chat/completions"):
        """
        Initialize LLM7 client with rate limiting
        
        Args:
            api_token: API token for authentication
            base_url: Base URL for the API endpoint
        """
        self.api_token = api_token
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        
        # Rate limiting state
        self._lock = Lock()
        self._request_times_hour = deque()  # Track requests in last hour
        self._request_times_minute = deque()  # Track requests in last minute
        self._request_times_second = deque()  # Track requests in last second
        self._last_request_time = 0
    
    def _cleanup_old_requests(self):
        """Remove old request timestamps that are outside rate limit windows"""
        current_time = time.time()
        
        # Clean up hourly requests (older than 1 hour)
        while self._request_times_hour and current_time - self._request_times_hour[0] > 3600:
            self._request_times_hour.popleft()
        
        # Clean up minute requests (older than 1 minute)
        while self._request_times_minute and current_time - self._request_times_minute[0] > 60:
            self._request_times_minute.popleft()
        
        # Clean up second requests (older than 1 second)
        while self._request_times_second and current_time - self._request_times_second[0] > 1:
            self._request_times_second.popleft()
    
    def _wait_for_rate_limit(self):
        """
        Wait if necessary to respect rate limits
        Returns True if wait was needed, False otherwise
        """
        with self._lock:
            self._cleanup_old_requests()
            current_time = time.time()
            wait_time = 0
            
            # Check per-second limit (5 req/s)
            if len(self._request_times_second) >= self.MAX_REQUESTS_PER_SECOND:
                oldest_second = self._request_times_second[0]
                wait_time = max(wait_time, 1.0 - (current_time - oldest_second))
            
            # Check per-minute limit (60 req/min)
            if len(self._request_times_minute) >= self.MAX_REQUESTS_PER_MINUTE:
                oldest_minute = self._request_times_minute[0]
                wait_time = max(wait_time, 60.0 - (current_time - oldest_minute))
            
            # Check per-hour limit (1500 req/h)
            if len(self._request_times_hour) >= self.MAX_REQUESTS_PER_HOUR:
                oldest_hour = self._request_times_hour[0]
                wait_time = max(wait_time, 3600.0 - (current_time - oldest_hour))
            
            if wait_time > 0:
                print(f"[LLM7] Rate limit reached. Waiting {wait_time:.2f}s...")
                time.sleep(wait_time)
                return True
            
            return False
    
    def _record_request(self):
        """Record a request timestamp for rate limiting"""
        current_time = time.time()
        self._request_times_second.append(current_time)
        self._request_times_minute.append(current_time)
        self._request_times_hour.append(current_time)
        self._last_request_time = current_time
    
    def _validate_request_size(self, prompt: str) -> bool:
        """
        Validate that the request size doesn't exceed the limit
        
        Args:
            prompt: The prompt to validate
        
        Returns:
            True if valid, False if exceeds limit
        """
        if len(prompt) > self.MAX_CHARS_PER_REQUEST:
            print(f"[LLM7] Request too large: {len(prompt)} chars (max: {self.MAX_CHARS_PER_REQUEST})")
            return False
        return True
    
    def chat(self, model_name: str, prompt: str, temperature: float = 0.7, 
             num_predict: int = 500, **kwargs) -> Optional[str]:
        """
        Send a chat completion request to llm7.io with rate limiting
        
        Args:
            model_name: Name of the model to use (e.g., 'deepseek-chat', 'gpt-4o-mini')
            prompt: The prompt/question to send to the model
            temperature: Sampling temperature (0.0 to 2.0)
            num_predict: Maximum number of tokens to generate
            **kwargs: Additional parameters to pass to the API
        
        Returns:
            The model's response as a string, or None if the request fails
        """
        # Validate request size (128k chars/req limit)
        if not self._validate_request_size(prompt):
            return None
        
        # Wait if necessary to respect rate limits
        self._wait_for_rate_limit()
        
        # Construct the request payload in OpenAI-compatible format
        payload = {
            "model": model_name,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": num_predict
        }
        
        # Add any additional parameters
        for key, value in kwargs.items():
            if key not in payload:
                payload[key] = value
        
        try:
            # Record request for rate limiting
            with self._lock:
                self._record_request()
            
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            # Check for successful response
            if response.status_code == 200:
                data = response.json()
                
                # Extract the message content from the response
                if 'choices' in data and len(data['choices']) > 0:
                    message = data['choices'][0].get('message', {})
                    content = message.get('content', '')
                    return content
                else:
                    print(f"[LLM7] Unexpected response format: {data}")
                    return None
            
            elif response.status_code == 401:
                print(f"[LLM7] Authentication failed. Check API token.")
                return None
            
            elif response.status_code == 429:
                print(f"[LLM7] Rate limit exceeded. Please wait and try again.")
                return None
            
            else:
                print(f"[LLM7] API error {response.status_code}: {response.text[:200]}")
                return None
        
        except requests.exceptions.Timeout:
            print(f"[LLM7] Request timed out after 30 seconds")
            return None
        
        except requests.exceptions.ConnectionError as e:
            print(f"[LLM7] Connection error: {e}")
            return None
        
        except Exception as e:
            print(f"[LLM7] Unexpected error: {e}")
            return None
    
    def test_connection(self) -> bool:
        """
        Test the API connection with a simple request
        
        Returns:
            True if the connection is successful, False otherwise
        """
        try:
            response = self.chat(
                model_name="gpt-4o-mini",  # Use a lightweight model for testing
                prompt="Say 'OK' if you can read this.",
                temperature=0.0,
                num_predict=10
            )
            return response is not None
        except Exception as e:
            print(f"[LLM7] Connection test failed: {e}")
            return False
