"""
Simplified VulnBot Configuration System
Single YAML file configuration with minimal Python wrapper
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict
import yaml
from enum import StrEnum

# Get the project root
PENTEST_ROOT = Path(os.environ.get("PENTEST_ROOT", ".")).resolve()
CONFIG_FILE = PENTEST_ROOT / "config.yaml"


class Mode(StrEnum):
    Auto = "auto"
    Manual = "manual" 
    SemiAuto = "semi"

    def __missing__(self, key):
        return self.Auto


class Config:
    """Simple configuration class that loads from a single YAML file"""
    
    def __init__(self, config_file: Path = CONFIG_FILE):
        self.config_file = config_file
        self._config = {}
        self.load()
    
    def load(self):
        """Load configuration from YAML file"""
        if not self.config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_file}")
        
        with open(self.config_file, 'r') as f:
            self._config = yaml.safe_load(f)
    
    def reload(self):
        """Reload configuration from file"""
        self.load()
    
    def get(self, key_path: str, default=None):
        """
        Get configuration value using dot notation
        Example: config.get('basic.log_verbose') -> True
        """
        keys = key_path.split('.')
        value = self._config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, key_path: str, value: Any):
        """
        Set configuration value using dot notation
        Example: config.set('basic.log_verbose', False)
        """
        keys = key_path.split('.')
        config = self._config
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        config[keys[-1]] = value
    
    def save(self):
        """Save current configuration to YAML file"""
        with open(self.config_file, 'w') as f:
            yaml.dump(self._config, f, default_flow_style=False, indent=2)
    
    # Convenience properties for common settings
    @property
    def basic(self) -> Dict[str, Any]:
        return self._config.get('basic', {})
    
    @property
    def database(self) -> Dict[str, Any]:
        return self._config.get('database', {})
    
    @property
    def knowledge_base(self) -> Dict[str, Any]:
        return self._config.get('knowledge_base', {})
    
    @property
    def llm(self) -> Dict[str, Any]:
        return self._config.get('llm', {})
    
    @property
    def tavily(self) -> Dict[str, Any]:
        return self._config.get('tavily', {})
    
    # Commonly used values
    @property
    def mode(self) -> str:
        return Mode(self.get('basic.mode', 'auto'))
    
    @property
    def log_verbose(self) -> bool:
        return self.get('basic.log_verbose', True)
    
    @property
    def enable_tavily_search(self) -> bool:
        return self.get('basic.enable_tavily_search', False)
    
    @property
    def tavily_enabled(self) -> bool:
        return self.get('tavily.enabled', False)
    
    @property
    def tavily_api_key(self) -> str:
        return self.get('tavily.api_key', '')
    
    @property
    def log_path_resolved(self) -> Path:
        log_path = self.get('basic.log_path', 'logs')
        return PENTEST_ROOT / log_path
    
    @property
    def kb_root_path_resolved(self) -> Path:
        kb_path = self.get('basic.kb_root_path', 'data/knowledge_base')
        return PENTEST_ROOT / kb_path
    
    def make_dirs(self):
        """Create necessary directories"""
        self.log_path_resolved.mkdir(parents=True, exist_ok=True)
        self.kb_root_path_resolved.mkdir(parents=True, exist_ok=True)


# Global configuration instance
config = Config()

# Backward compatibility - create objects that mimic the old structure
class BasicConfig:
    def __init__(self, config_instance: Config):
        self._config = config_instance
    
    @property
    def mode(self):
        return self._config.mode
    
    @property
    def log_verbose(self):
        return self._config.log_verbose
    
    @property
    def enable_tavily_search(self):
        return self._config.enable_tavily_search
    
    @property
    def LOG_PATH_RESOLVED(self):
        return self._config.log_path_resolved
    
    def make_dirs(self):
        return self._config.make_dirs()
    
    def __getattr__(self, name):
        # Dynamic attribute access for basic config
        return self._config.get(f'basic.{name}')


class DBConfig:
    def __init__(self, config_instance: Config):
        self._config = config_instance
    
    @property
    def mysql(self):
        return self._config.get('database.mysql', {})


class KBConfig:
    def __init__(self, config_instance: Config):
        self._config = config_instance
    
    def __getattr__(self, name):
        # Dynamic attribute access for KB config
        return self._config.get(f'knowledge_base.{name}')


class LLMConfig:
    def __init__(self, config_instance: Config):
        self._config = config_instance
    
    @property
    def tavily_api_key(self):
        # Check both locations for backward compatibility
        return self._config.get('tavily.api_key') or self._config.get('llm.tavily_api_key', '')
    
    def __getattr__(self, name):
        # Dynamic attribute access for LLM config
        return self._config.get(f'llm.{name}')


class TavilyConfig:
    def __init__(self, config_instance: Config):
        self._config = config_instance
    
    @property
    def enabled(self):
        return self._config.tavily_enabled
    
    @property
    def api_key(self):
        return self._config.tavily_api_key
    
    def __getattr__(self, name):
        # Dynamic attribute access for Tavily config
        return self._config.get(f'tavily.{name}')


# Backward compatibility object
class Configs:
    def __init__(self):
        self.PENTEST_ROOT = PENTEST_ROOT
        self.basic_config = BasicConfig(config)
        self.db_config = DBConfig(config)
        self.kb_config = KBConfig(config)
        self.llm_config = LLMConfig(config)
        self.tavily_config = TavilyConfig(config)


# Global instance for backward compatibility
Configs = Configs()
