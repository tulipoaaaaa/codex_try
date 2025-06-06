from typing import Dict, Any, List, Optional
import camelot
import pandas as pd
from pathlib import Path
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

class TableMixin:
    """Mixin for table extraction functionality using Camelot."""
    
    def __init__(self, table_timeout: int = 30):
        """Initialize the table mixin.
        
        Args:
            table_timeout: Timeout in seconds for table extraction
        """
        self.table_timeout = table_timeout
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def extract_tables(self, file_path: Path) -> List[Dict[str, Any]]:
        """Extract tables from a PDF file using Camelot.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            List of dictionaries containing table data and metadata
        """
        try:
            # Use ThreadPoolExecutor to handle timeout
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(self._extract_tables_internal, file_path)
                try:
                    return future.result(timeout=self.table_timeout)
                except TimeoutError:
                    self.logger.warning(f"Table extraction timed out after {self.table_timeout} seconds for {file_path}")
                    return []
        except Exception as e:
            self.logger.error(f"Error extracting tables from {file_path}: {str(e)}")
            return []
    
    def _extract_tables_internal(self, file_path: Path) -> List[Dict[str, Any]]:
        """Internal method for table extraction.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            List of dictionaries containing table data and metadata
        """
        tables = []
        try:
            # Extract tables using Camelot
            camelot_tables = camelot.read_pdf(
                str(file_path),
                pages='all',
                flavor='lattice',
                suppress_stdout=True,
                copy_text=['v']
            )
            
            for idx, table in enumerate(camelot_tables):
                try:
                    # Convert table to DataFrame
                    df = table.df
                    
                    # Clean up the table
                    df = self._clean_table(df)
                    
                    # Convert to dictionary format
                    table_dict = {
                        'table_id': f"table_{idx + 1}",
                        'page': table.page,
                        'accuracy': float(table.accuracy),
                        'whitespace': float(table.whitespace),
                        'order': idx + 1,
                        'data': df.to_dict(orient='records'),
                        'shape': df.shape,
                        'extraction_method': 'camelot_lattice'
                    }
                    
                    tables.append(table_dict)
                except Exception as e:
                    self.logger.warning(f"Error processing table {idx + 1} in {file_path}: {str(e)}")
                    continue
            
            return tables
            
        except Exception as e:
            self.logger.error(f"Error in table extraction for {file_path}: {str(e)}")
            return []
    
    def _clean_table(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean up extracted table data.
        
        Args:
            df: DataFrame containing table data
            
        Returns:
            Cleaned DataFrame
        """
        # Remove empty rows and columns
        df = df.dropna(how='all').dropna(axis=1, how='all')
        
        # Clean up cell values
        df = df.applymap(lambda x: str(x).strip() if isinstance(x, str) else x)
        
        # Remove duplicate rows
        df = df.drop_duplicates()
        
        return df 