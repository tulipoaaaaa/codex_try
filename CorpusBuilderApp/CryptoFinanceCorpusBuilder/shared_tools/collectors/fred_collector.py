# sources/specific_collectors/fred_collector.py
import os
import json
import time
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional, Union, Any
from CryptoFinanceCorpusBuilder.shared_tools.collectors.base_collector import BaseCollector
from dotenv import load_dotenv
import requests

class FREDCollector(BaseCollector):
    """Collector for FRED (Federal Reserve Economic Data)"""
    
    def __init__(self, 
                 config: Union[str, 'ProjectConfig'],
                 api_key: Optional[str] = None,
                 delay_range: tuple = (2, 5)):
        """Initialize the FRED collector.
        
        Args:
            config: ProjectConfig instance or path to config file
            api_key: FRED API key
            delay_range: Tuple of (min_delay, max_delay) in seconds between requests
        """
        super().__init__(config, delay_range=delay_range)
        self.api_key = api_key or os.getenv("FRED_API_KEY")
        if not self.api_key:
            raise ValueError("FRED API key is required. Set it in .env file as FRED_API_KEY")
        self.api_base_url = 'https://api.stlouisfed.org/fred'
        self.rate_limits = {'api.stlouisfed.org': {'requests': 20, 'period': 60}}  # Max 20 requests per minute
        
        # Set up FRED-specific directory using ProjectConfig paths
        self.fred_dir = self.config.raw_data_dir / 'FRED'
            
        # Create FRED directory if it doesn't exist
        self.fred_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"FREDCollector initialized with output directory: {self.fred_dir}")
    
    def api_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Make a request to the FRED API.
        
        Args:
            endpoint: API endpoint to call
            params: Query parameters for the request
            
        Returns:
            Response data as dictionary or None if request failed
        """
        if not self.api_key:
            self.logger.error("API key is required for FRED API")
            return None
            
        # Add API key to params
        if params is None:
            params = {}
        params['api_key'] = self.api_key
        
        # Build full URL
        url = f"{self.api_base_url}/{endpoint}"
        
        try:
            # Apply rate limiting
            self._respect_rate_limits(url)
            
            # Make request
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            return data
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error making FRED API request to {endpoint}: {e}")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing FRED API response from {endpoint}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error in FRED API request to {endpoint}: {e}")
            return None
    
    def collect(self, 
                series_ids: Optional[List[str]] = None,
                search_terms: Optional[List[str]] = None,
                categories: Optional[List[str]] = None,
                max_results: int = 100) -> List[Dict[str, Any]]:
        """Collect data from FRED.
        
        Args:
            series_ids: List of FRED series IDs to collect
            search_terms: List of search terms to find series
            categories: List of category IDs to collect series from
            max_results: Maximum number of results to collect per search
            
        Returns:
            List of dictionaries containing metadata about collected files
        """
        self.logger.info("FREDCollector.collect called with series_ids: %s, search_terms: %s, categories: %s, max_results: %d", 
                        series_ids, search_terms, categories, max_results)
        collected_data = []
        
        # Get series by IDs if provided
        if series_ids:
            for series_id in series_ids:
                series_data = self._get_series(series_id)
                if series_data:
                    collected_data.append(series_data)
        
        # Search for series by terms
        if search_terms:
            for term in search_terms:
                search_results = self._search_series(term, max_results=max_results)
                
                # Get data for each series
                for series in search_results[:min(len(search_results), max_results)]:
                    series_id = series.get('id')
                    if series_id:
                        series_data = self._get_series(series_id)
                        if series_data:
                            collected_data.append(series_data)
        
        # Search by category
        if categories:
            for category_id in categories:
                category_series = self._get_category_series(category_id, max_results=max_results)
                
                # Get data for each series
                for series in category_series[:min(len(category_series), max_results)]:
                    series_id = series.get('id')
                    if series_id:
                        series_data = self._get_series(series_id)
                        if series_data:
                            collected_data.append(series_data)
        
        # Write collected data to files
        saved_files = self._save_series_data(collected_data)
        
        return saved_files
    
    def _search_series(self, search_text: str, max_results: int = 100) -> List[Dict[str, Any]]:
        """Search for series in FRED.
        
        Args:
            search_text: Text to search for
            max_results: Maximum number of results to return
            
        Returns:
            List of series information dictionaries
        """
        if not self.api_key:
            self.logger.error("API key is required for FRED API")
            return []
        
        # Build API request
        endpoint = f"series/search"
        params = {
            'search_text': search_text,
            'api_key': self.api_key,
            'file_type': 'json',
            'limit': max_results
        }
        
        # Make the request
        response = self.api_request(endpoint, params=params)
        
        if not response or 'seriess' not in response:
            return []
        
        return response['seriess']
    
    def _get_series(self, series_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information and observations for a series.
        
        Args:
            series_id: FRED series ID to get data for
            
        Returns:
            Dictionary containing series information and observations, or None if failed
        """
        if not self.api_key:
            self.logger.error("API key is required for FRED API")
            return None
        
        # Get series info
        info_endpoint = f"series"
        info_params = {
            'series_id': series_id,
            'api_key': self.api_key,
            'file_type': 'json'
        }
        
        info_response = self.api_request(info_endpoint, params=info_params)
        
        if not info_response or 'seriess' not in info_response or not info_response['seriess']:
            return None
        
        series_info = info_response['seriess'][0]
        
        # Get observations
        obs_endpoint = f"series/observations"
        obs_params = {
            'series_id': series_id,
            'api_key': self.api_key,
            'file_type': 'json',
            'observation_start': '1900-01-01'  # Get all available data
        }
        
        obs_response = self.api_request(obs_endpoint, params=obs_params)
        
        if not obs_response or 'observations' not in obs_response:
            observations = []
        else:
            observations = obs_response['observations']
        
        # Combine info and observations
        return {
            'series_id': series_id,
            'info': series_info,
            'observations': observations
        }
    
    def _get_category_series(self, category_id: str, max_results: int = 100) -> List[Dict[str, Any]]:
        """Get series for a specific category.
        
        Args:
            category_id: FRED category ID to get series for
            max_results: Maximum number of series to return
            
        Returns:
            List of series information dictionaries
        """
        if not self.api_key:
            self.logger.error("API key is required for FRED API")
            return []
        
        # Build API request
        endpoint = f"category/series"
        params = {
            'category_id': category_id,
            'api_key': self.api_key,
            'file_type': 'json',
            'limit': max_results
        }
        
        # Make the request
        response = self.api_request(endpoint, params=params)
        
        if not response or 'seriess' not in response:
            return []
        
        return response['seriess']
    
    def _save_series_data(self, series_data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Save series data to CSV and JSON files.
        
        Args:
            series_data_list: List of series data dictionaries
            
        Returns:
            List of dictionaries containing metadata about saved files
        """
        saved_files = []
        
        for series_data in series_data_list:
            series_id = series_data.get('series_id')
            if not series_id:
                continue
                
            # Create clean title for files
            title = series_data.get('info', {}).get('title', series_id)
            clean_title = ''.join(c if c.isalnum() or c in ['-', '_', ' '] else '_' for c in title)
            clean_title = clean_title[:50]  # Limit length
            domain = 'valuation_models'  # Default domain for FRED data
            
            # Save JSON with all data
            json_filename = f"{series_id}_{clean_title}.json"
            json_path = self.fred_dir / json_filename
            with open(json_path, 'w') as f:
                json.dump(series_data, f, indent=2)
            # Save .meta file for JSON
            meta_json_path = json_path.with_suffix('.meta')
            meta_json = {
                'series_id': series_id,
                'title': title,
                'domain': domain,
                'filetype': 'json',
                'datafile': str(json_path)
            }
            with open(meta_json_path, 'w') as f:
                json.dump(meta_json, f, indent=2)
            saved_files.append({
                'series_id': series_id,
                'title': title,
                'filepath': str(json_path),
                'domain': domain
            })
            
            # Save observations as CSV
            observations = series_data.get('observations', [])
            if observations:
                # Convert to pandas DataFrame
                df = pd.DataFrame(observations)
                # Save as CSV
                csv_filename = f"{series_id}_{clean_title}.csv"
                csv_path = self.fred_dir / csv_filename
                df.to_csv(csv_path, index=False)
                # Save .meta file for CSV
                meta_csv_path = csv_path.with_suffix('.meta')
                meta_csv = {
                    'series_id': series_id,
                    'title': title,
                    'domain': domain,
                    'filetype': 'csv',
                    'datafile': str(csv_path)
                }
                with open(meta_csv_path, 'w') as f:
                    json.dump(meta_csv, f, indent=2)
                saved_files.append({
                    'series_id': series_id,
                    'title': title,
                    'filepath': str(csv_path),
                    'domain': domain
                })
                
        return saved_files
    
    def _determine_domain(self, series_data: Dict[str, Any]) -> str:
        """Determine the domain for a series based on its category or title.
        
        Args:
            series_data: Dictionary containing series information
            
        Returns:
            Domain name for the series
        """
        # Default to valuation_models if no better match is found
        default_domain = "valuation_models"
        
        # Get series info
        info = series_data.get('info', {})
        title = info.get('title', '').lower()
        notes = info.get('notes', '').lower()
        
        # Check for domain-specific keywords
        if any(term in title.lower() or term in notes.lower() for term in ['volatility', 'risk', 'uncertainty']):
            return "risk_management"
        elif any(term in title.lower() or term in notes.lower() for term in ['portfolio', 'allocation', 'weight']):
            return "portfolio_construction"
        elif any(term in title.lower() or term in notes.lower() for term in ['regulation', 'compliance', 'legal']):
            return "regulation_compliance"
        elif any(term in title.lower() or term in notes.lower() for term in ['defi', 'decentralized', 'blockchain']):
            return "decentralized_finance"
        elif any(term in title.lower() or term in notes.lower() for term in ['hft', 'high frequency', 'algorithmic']):
            return "high_frequency_trading"
        elif any(term in title.lower() or term in notes.lower() for term in ['microstructure', 'order book', 'liquidity']):
            return "market_microstructure"
        elif any(term in title.lower() or term in notes.lower() for term in ['derivative', 'futures', 'options']):
            return "crypto_derivatives"
        
        return default_domain
    
    def collect_by_series(self, series_ids: Union[str, List[str]]) -> List[Dict[str, Any]]:
        """Collect data for specific series IDs.
        
        Args:
            series_ids: Single series ID or list of series IDs
            
        Returns:
            List of dictionaries containing metadata about collected files
        """
        if isinstance(series_ids, str):
            series_ids = [series_ids]
            
        return self.collect(series_ids=series_ids)
    
    def _check_file_validity(self, filepath: str) -> bool:
        """Check if a file is valid.
        
        Args:
            filepath: Path to the file to check
            
        Returns:
            True if file is valid, False otherwise
        """
        try:
            path = Path(filepath)
            if not path.exists():
                return False
                
            # Check file size
            if path.stat().st_size < 1000:  # Less than 1KB
                return False
                
            # Check file content based on extension
            if path.suffix == '.json':
                with open(path, 'r') as f:
                    json.load(f)
            elif path.suffix == '.csv':
                pd.read_csv(path)
                
            return True
        except Exception as e:
            self.logger.error(f"Error validating file {filepath}: {str(e)}")
            return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Collect data from FRED")
    parser.add_argument("--config", required=True, help="Path to config file")
    parser.add_argument("--series-ids", nargs="*", help="List of FRED series IDs to collect")
    parser.add_argument("--search-terms", nargs="*", help="List of search terms to find series")
    parser.add_argument("--categories", nargs="*", help="List of category IDs to collect series from")
    parser.add_argument("--max-results", type=int, default=100, help="Maximum number of results per search")
    
    args = parser.parse_args()
    
    load_dotenv()
    api_key = os.getenv("FRED_API_KEY")
    
    collector = FREDCollector(args.config, api_key=api_key)
    results = collector.collect(
        series_ids=args.series_ids,
        search_terms=args.search_terms,
        categories=args.categories,
        max_results=args.max_results
    )
    
    print(f"Collected {len(results)} FRED records. Output dir: {collector.fred_dir}")