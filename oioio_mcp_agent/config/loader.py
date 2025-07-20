"""
Configuration loader for YAML-based configuration files.
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import logging
from dotenv import load_dotenv

from oioio_mcp_agent.config.schema import Config
from oioio_mcp_agent.utils.dict_utils import deep_merge

logger = logging.getLogger(__name__)


class ConfigLoader:
    """Config loader for YAML files and environment variables."""

    def __init__(self, config_dir: Union[str, Path] = "configs"):
        """
        Initialize the config loader.
        
        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = Path(config_dir)
        self.loaded_config: Optional[Config] = None
        self.env_prefix = "MCP_"

    def load_config(self, 
                   config_name: str = "config.yaml", 
                   env_file: Optional[str] = None,
                   env_name: Optional[str] = None) -> Config:
        """
        Load configuration from YAML files and environment.
        
        Args:
            config_name: Base configuration file name
            env_file: Path to .env file for loading environment variables
            env_name: Environment name for loading environment-specific config
            
        Returns:
            Complete configuration object
        """
        # Load environment variables if specified
        if env_file:
            self._load_env_file(env_file)
            
        # Load base config
        base_config_path = self.config_dir / config_name
        if not base_config_path.exists():
            raise FileNotFoundError(f"Config file not found: {base_config_path}")
        
        config_data = self._load_yaml_file(base_config_path)
        
        # Load environment-specific config if specified
        if env_name:
            env_config_path = self.config_dir / f"config.{env_name}.yaml"
            if env_config_path.exists():
                logger.info(f"Loading environment config: {env_config_path}")
                env_config_data = self._load_yaml_file(env_config_path)
                config_data = deep_merge(config_data, env_config_data)
        
        # Override with environment variables
        config_data = self._apply_env_overrides(config_data)
        
        # Create and validate the config object
        self.loaded_config = Config(**config_data)
        logger.info(f"Loaded configuration: {len(config_data)} top-level keys")
        
        return self.loaded_config
    
    def _load_yaml_file(self, file_path: Path) -> Dict[str, Any]:
        """Load YAML file and return as dict."""
        try:
            with open(file_path, "r") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"Failed to load YAML file {file_path}: {e}")
            raise
    
    def _load_env_file(self, env_file: str) -> None:
        """Load variables from .env file."""
        env_path = Path(env_file)
        if not env_path.exists():
            logger.warning(f".env file not found: {env_path}")
            return
        
        load_dotenv(env_path)
        logger.info(f"Loaded environment variables from {env_path}")
    
    def _apply_env_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Override configuration with environment variables.
        
        Environment variables should be prefixed with MCP_ and use double underscore
        to represent nested config keys.
        
        Example:
            MCP_CORE__KNOWLEDGE_DIR=/path/to/knowledge
            
        Returns:
            Updated configuration dict
        """
        result = config.copy()
        
        for key, value in os.environ.items():
            if not key.startswith(self.env_prefix):
                continue
                
            # Remove prefix and split into parts
            config_path = key[len(self.env_prefix):].lower()
            if not config_path:
                continue
                
            parts = config_path.split('__')
            if len(parts) == 1:
                # Top-level key
                result[parts[0]] = self._convert_env_value(value)
            else:
                # Nested key
                current = result
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                current[parts[-1]] = self._convert_env_value(value)
        
        return result
    
    def _convert_env_value(self, value: str) -> Any:
        """Convert environment variable string to appropriate Python type."""
        if value.lower() == 'true':
            return True
        elif value.lower() == 'false':
            return False
        elif value.isdigit():
            return int(value)
        elif value.replace('.', '', 1).isdigit() and value.count('.') == 1:
            return float(value)
        else:
            return value