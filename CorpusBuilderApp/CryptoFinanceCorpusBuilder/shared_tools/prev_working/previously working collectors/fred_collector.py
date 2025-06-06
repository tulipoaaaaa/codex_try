# sources/specific_collectors/fred_collector.py
import os
import json
import time
import pandas as pd
from pathlib import Path
from CryptoFinanceCorpusBuilder.shared_tools.collectors.api_collector import ApiCollector
from dotenv import load_dotenv

class FREDCollector(ApiCollector):
    """Collector for FRED (Federal Reserve Economic Data)"""
    
    def __init__(self, output_dir, api_key=None, delay_range=(2, 5)):
        super().__init__(output_dir, api_key=api_key, api_base_url='https://api.stlouisfed.org/fred', delay_range=delay_range)
        self.rate_limits = {'api.stlouisfed.org': {'requests': 20, 'period': 60}}  # Max 20 requests per minute
    
    def collect(self, series_ids=None, search_terms=None, categories=None, max_results=100):
        """Collect data from FRED"""
        print(f"[DEBUG] FREDCollector.collect called with:")
        print(f"  series_ids: {series_ids}")
        print(f"  search_terms: {search_terms}")
        print(f"  categories: {categories}")
        print(f"  max_results: {max_results}")
        print(f"  api_key: {self.api_key}")
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
    
    def _search_series(self, search_text, max_results=100):
        """Search for series in FRED"""
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
    
    def _get_series(self, series_id):
        """Get detailed information and observations for a series"""
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
    
    def _get_category_series(self, category_id, max_results=100):
        """Get series for a specific category"""
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
    
    def _save_series_data(self, series_data_list):
        """Save series data to CSV and JSON files"""
        saved_files = []
        
        for series_data in series_data_list:
            series_id = series_data.get('series_id')
            if not series_id:
                continue
                
            # Create clean title for files
            title = series_data.get('info', {}).get('title', series_id)
            clean_title = ''.join(c if c.isalnum() or c in ['-', '_', ' '] else '_' for c in title)
            clean_title = clean_title[:50]  # Limit length
            
            # Save JSON with all data
            json_path = self.output_dir / f"{series_id}_{clean_title}.json"
            
            with open(json_path, 'w') as f:
                json.dump(series_data, f, indent=2)
                
            saved_files.append(str(json_path))
            
            # Save observations as CSV
            observations = series_data.get('observations', [])
            if observations:
                # Convert to pandas DataFrame
                df = pd.DataFrame(observations)
                
                # Save as CSV
                csv_path = self.output_dir / f"{series_id}_{clean_title}.csv"
                df.to_csv(csv_path, index=False)
                
                saved_files.append(str(csv_path))
                
        return saved_files

if __name__ == "__main__":
    import argparse
    from dotenv import load_dotenv
    import os
    parser = argparse.ArgumentParser(description="Collect data from FRED")
    parser.add_argument("--output-dir", required=True, help="Output directory for collected data")
    parser.add_argument("--series-ids", nargs="*", help="List of FRED series IDs to collect (e.g. VIXCLS DTWEXBGS)")
    parser.add_argument("--search-terms", nargs="*", help="List of search terms (e.g. volatility inflation)")
    parser.add_argument("--categories", nargs="*", help="List of FRED categories")
    parser.add_argument("--max-results", type=int, default=100, help="Maximum number of results to collect")
    args = parser.parse_args()
    from pathlib import Path
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    load_dotenv()
    api_key = os.getenv("FRED_API_KEY")
    print(f"[DEBUG] Loaded FRED_API_KEY: {api_key}")
    collector = FREDCollector(output_dir, api_key=api_key)
    print(f"[DEBUG] CLI args: {args}")
    results = collector.collect(
        series_ids=args.series_ids if args.series_ids else None,
        search_terms=args.search_terms if args.search_terms else None,
        categories=args.categories if args.categories else None,
        max_results=args.max_results
    )
    print(f"Collected {len(results)} FRED records. Output dir: {output_dir}")