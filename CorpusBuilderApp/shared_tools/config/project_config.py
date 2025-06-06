"""
Project configuration module for managing corpus builder settings.
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
import logging

logger = logging.getLogger(__name__)

class ProjectConfig:
    """Project configuration manager for corpus builder."""
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """Initialize project configuration.
        
        Args:
            config_path: Path to project configuration file (YAML or JSON)
        """
        self.config_path = Path(config_path) if config_path else None
        self.config = self._load_config() if config_path else {}
        
        # Set up logging
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize default paths
        self.raw_data_dir = self._get_path('raw_data_dir', 'raw_data')
        self.processed_dir = self._get_path('processed_dir', 'processed')
        self.output_dir = self._get_path('output_dir', 'output')
        self.temp_dir = self._get_path('temp_dir', 'temp')
        
        # Initialize processor configurations
        self.processors = self.config.get('processors', {})
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        try:
            if self.config_path.suffix.lower() == '.yaml':
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
            else:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            raise ValueError(f"Error loading configuration from {self.config_path}: {str(e)}")
    
    def _get_path(self, key: str, default: str) -> Path:
        """Get path from config or use default."""
        path_str = self.config.get(key, default)
        return Path(path_str)
    
    def get_processor_config(self, processor_name: str) -> Dict[str, Any]:
        """Get configuration for a specific processor.
        
        Args:
            processor_name: Name of the processor
            
        Returns:
            Dict containing processor configuration
        """
        return self.processors.get(processor_name, {})
    
    def get_input_dir(self) -> Path:
        """Get input directory path."""
        return self.raw_data_dir
    
    def get_output_dir(self) -> Path:
        """Get output directory path."""
        return self.output_dir
    
    def get_processed_dir(self) -> Path:
        """Get processed directory path."""
        return self.processed_dir
    
    def get_temp_dir(self) -> Path:
        """Get temporary directory path."""
        return self.temp_dir
    
    def save(self, path: Optional[Union[str, Path]] = None) -> None:
        """Save configuration to file.
        
        Args:
            path: Optional path to save configuration to
        """
        save_path = Path(path) if path else self.config_path
        if not save_path:
            raise ValueError("No path specified for saving configuration")
        
        try:
            if save_path.suffix.lower() == '.yaml':
                with open(save_path, 'w', encoding='utf-8') as f:
                    yaml.dump(self.config, f, default_flow_style=False)
            else:
                with open(save_path, 'w', encoding='utf-8') as f:
                    json.dump(self.config, f, indent=2)
        except Exception as e:
            raise ValueError(f"Error saving configuration to {save_path}: {str(e)}")
    
    @classmethod
    def load(cls, config_path: Union[str, Path]) -> 'ProjectConfig':
        """Load project configuration from file.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            ProjectConfig instance
        """
        return cls(config_path)
    
    def update(self, updates: Dict[str, Any]) -> None:
        """Update configuration with new values.
        
        Args:
            updates: Dictionary of configuration updates
        """
        self.config.update(updates)
        
        # Update paths if changed
        if 'raw_data_dir' in updates:
            self.raw_data_dir = self._get_path('raw_data_dir', 'raw_data')
        if 'processed_dir' in updates:
            self.processed_dir = self._get_path('processed_dir', 'processed')
        if 'output_dir' in updates:
            self.output_dir = self._get_path('output_dir', 'output')
        if 'temp_dir' in updates:
            self.temp_dir = self._get_path('temp_dir', 'temp')
        
        # Update processor configs if changed
        if 'processors' in updates:
            self.processors = updates['processors'] 