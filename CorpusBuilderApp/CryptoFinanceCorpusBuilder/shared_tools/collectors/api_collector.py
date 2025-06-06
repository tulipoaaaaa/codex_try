# sources/api_collector.py
from CryptoFinanceCorpusBuilder.shared_tools.collectors.base_collector import BaseCollector
import json
import requests
import time
from typing import Optional, Dict, Union, Any
from pathlib import Path

class ApiCollector(BaseCollector):
    """Base class for API-based collectors"""
    
    def __init__(self, 
                 config: Union[str, 'ProjectConfig'],
                 api_base_url: Optional[str] = None,
                 delay_range: tuple = (5, 10)):
        """Initialize the API collector.
        
        Args:
            config: ProjectConfig instance or path to config file
            api_base_url: Base URL for the API
            delay_range: Tuple of (min_delay, max_delay) in seconds between requests
        """
        super().__init__(config)
        self.api_base_url = api_base_url
        self.delay_range = delay_range
        self.api_key = None  # Ensure attribute exists
        self.last_request_time = {}
        self.rate_limits = {}  # Format: {'domain': {'requests': 10, 'period': 60}}
    
    def api_request(self, 
                   endpoint: str,
                   params: Optional[Dict[str, Any]] = None,
                   headers: Optional[Dict[str, str]] = None,
                   method: str = 'GET',
                   domain: Optional[str] = None) -> Optional[Union[Dict[str, Any], str]]:
        """Make an API request with rate limiting.
        
        Args:
            endpoint: API endpoint to call
            params: Query parameters
            headers: Request headers
            method: HTTP method (GET or POST)
            domain: Domain for rate limiting
            
        Returns:
            API response as JSON dict or text, or None if request failed
        """
        if not domain and self.api_base_url:
            domain = self.api_base_url
        
        # Apply rate limiting if configured for this domain
        if domain in self.rate_limits:
            self._apply_rate_limit(domain)
        
        url = f"{self.api_base_url}/{endpoint}" if self.api_base_url else endpoint
        
        # Add API key to parameters if provided
        if self.api_key:
            if params is None:
                params = {}
            params['api_key'] = self.api_key
        
        # Set default headers
        if headers is None:
            headers = {}
        headers['User-Agent'] = self._get_random_user_agent()
        
        # Make the request
        self.logger.debug(f"Making API request to {url}")
        try:
            self.last_request_time[domain] = time.time()
            
            if method.upper() == 'GET':
                response = self.session.get(url, params=params, headers=headers)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=params, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            
            # Try to parse JSON response
            try:
                return response.json()
            except json.JSONDecodeError:
                return response.text
        
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API request to {url} failed: {e}")
            return None
    
    def _apply_rate_limit(self, domain: str) -> None:
        """Apply domain-specific rate limiting.
        
        Args:
            domain: Domain to apply rate limiting for
        """
        current_time = time.time()
        rate_config = self.rate_limits.get(domain, {})
        requests_allowed = rate_config.get('requests', 10)
        period = rate_config.get('period', 60)  # in seconds
        
        if domain in self.last_request_time:
            elapsed = current_time - self.last_request_time[domain]
            min_interval = period / requests_allowed
            
            if elapsed < min_interval:
                wait_time = min_interval - elapsed
                self.logger.debug(f"Rate limiting: waiting {wait_time:.2f}s for {domain}")
                time.sleep(wait_time)

if __name__ == "__main__":
    import argparse
    from dotenv import load_dotenv
    import os
    
    parser = argparse.ArgumentParser(description="Collect data from an API")
    parser.add_argument("--config", required=True, help="Path to config file")
    parser.add_argument("--endpoint", required=True, help="API endpoint to call (relative or absolute URL)")
    parser.add_argument("--params", type=str, help="Query parameters as JSON string (e.g., '{\"q\": \"bitcoin\"}')")
    parser.add_argument("--api-key", type=str, help="API key for authentication (overrides .env)")
    parser.add_argument("--base-url", type=str, help="Base URL for the API (if needed)")
    parser.add_argument("--method", type=str, default="GET", help="HTTP method: GET or POST (default: GET)")
    
    args = parser.parse_args()
    
    load_dotenv()
    api_key = args.api_key or os.getenv("API_KEY")
    api_base_url = args.base_url or os.getenv("API_BASE_URL")
    
    collector = ApiCollector(args.config, api_base_url=api_base_url)
    
    params = None
    if args.params:
        try:
            params = json.loads(args.params)
        except Exception as e:
            print(f"[ERROR] Failed to parse --params JSON: {e}")
            exit(1)
            
    print(f"[DEBUG] CLI args: {args}")
    print(f"[DEBUG] Using API key: {api_key}")
    print(f"[DEBUG] Using base URL: {api_base_url}")
    print(f"[DEBUG] Endpoint: {args.endpoint}")
    print(f"[DEBUG] Params: {params}")
    print(f"[DEBUG] Method: {args.method}")
    
    response = collector.api_request(args.endpoint, params=params, method=args.method)
    
    # Save response to file
    output_file = Path(collector.output_dir) / "api_response.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(response, f, indent=2, ensure_ascii=False)
        
    print(f"[DEBUG] Saved API response to {output_file}")
    print(f"Collected 1 API record. Output dir: {collector.output_dir}")