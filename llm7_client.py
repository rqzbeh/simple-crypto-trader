"""
LLM7.io API Client
A lightweight wrapper for the llm7.io API that provides a similar interface to OllamaFreeAPI
"""

import requests
import json
from typing import Optional, Dict, Any

class LLM7Client:
    """
    Client for llm7.io API
    Provides a chat() method compatible with the existing codebase
    """
    
    def __init__(self, api_token: str, base_url: str = "https://llm7.io/v1/chat/completions"):
        """
        Initialize LLM7 client
        
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
    
    def chat(self, model_name: str, prompt: str, temperature: float = 0.7, 
             num_predict: int = 500, **kwargs) -> Optional[str]:
        """
        Send a chat completion request to llm7.io
        
        Args:
            model_name: Name of the model to use (e.g., 'deepseek-chat', 'gpt-4o-mini')
            prompt: The prompt/question to send to the model
            temperature: Sampling temperature (0.0 to 2.0)
            num_predict: Maximum number of tokens to generate
            **kwargs: Additional parameters to pass to the API
        
        Returns:
            The model's response as a string, or None if the request fails
        """
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
