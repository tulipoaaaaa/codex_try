# sources/api_collector.py
from .base_collector import BaseCollector
import json
import requests
import time

class ApiCollector(BaseCollector):
    """Base class for API-based collectors"""
    
    def __init__(self, output_dir, api_key=None, api_base_url=None, delay_range=(2, 5)):
        super().__init__(output_dir, delay_range)
        self.api_key = api_key
        self.api_base_url = api_base_url
        self.last_request_time = {}
        self.rate_limits = {}  # Format: {'domain': {'requests': 10, 'period': 60}}
    
    def api_request(self, endpoint, params=None, headers=None, method='GET', domain=None):
        """Make an API request with rate limiting"""
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
    
    def _apply_rate_limit(self, domain):
        """Apply domain-specific rate limiting"""
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