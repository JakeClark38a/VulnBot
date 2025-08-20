"""
VulnBot Configuration System
Now simplified to use a single YAML configuration file
"""

# Re-export the simplified configuration system
from .simple_config import (
    Config,
    config,
    Configs,
    Mode,
    PENTEST_ROOT
)

# Backward compatibility exports
__all__ = [
    'Config',
    'config', 
    'Configs',
    'Mode',
    'PENTEST_ROOT'
]
