# VulnBot Simplified Configuration System

## Overview

VulnBot now uses a **single YAML configuration file** (`config.yaml`) instead of multiple configuration files. This simplifies configuration management and reduces complexity.

## Migration from Old System

### Before (Multiple Files)
```
basic_config.yaml    -> Basic settings
db_config.yaml       -> Database configuration  
kb_config.yaml       -> Knowledge base settings
model_config.yaml    -> LLM model configuration
tavily_config.yaml   -> Tavily search settings
```

### After (Single File)
```
config.yaml          -> All settings in one file
```

## Configuration Structure

The new `config.yaml` is organized into logical sections:

```yaml
# Basic application settings
basic:
  mode: auto
  log_verbose: true
  enable_tavily_search: true
  # ... more basic settings

# Database configuration
database:
  mysql:
    host: localhost
    port: 3306
    # ... more database settings

# Knowledge base settings
knowledge_base:
  kb_name: vulnbot_knowledge
  chunk_size: 750
  # ... more KB settings

# LLM model configuration
llm:
  llm_model: openai
  llm_model_name: Qwen3-32B
  # ... more LLM settings

# Tavily search configuration
tavily:
  enabled: true
  api_key: "your-api-key"
  # ... more Tavily settings
```

## Usage Examples

### 1. Direct Access (Recommended)
```python
from config.config import config

# Get values using dot notation
mode = config.get('basic.mode')
api_key = config.get('tavily.api_key')
mysql_host = config.get('database.mysql.host')

# Set values
config.set('basic.mode', 'manual')
config.save()  # Save changes to file
```

### 2. Convenience Properties
```python
from config.config import config

# Common settings have convenience properties
print(f"Mode: {config.mode}")
print(f"Tavily enabled: {config.tavily_enabled}")
print(f"Log path: {config.log_path_resolved}")
```

### 3. Section Access
```python
from config.config import config

# Access entire sections
basic_settings = config.basic
tavily_settings = config.tavily
llm_settings = config.llm
```

### 4. Backward Compatibility
```python
from config.config import Configs

# Old code still works!
mode = Configs.basic_config.mode
api_key = Configs.tavily_config.api_key
mysql = Configs.db_config.mysql
```

## Benefits

### ✅ Advantages of New System
- **Single file**: All configuration in one place
- **Easier management**: No need to track multiple files
- **Better organization**: Logical grouping by functionality
- **Simpler deployment**: Only one file to copy/manage
- **Dot notation**: Easy hierarchical access (`basic.mode`)
- **Dynamic updates**: Change and save settings at runtime
- **Backward compatible**: Existing code continues to work

### ❌ Old System Problems (Solved)
- Multiple files to manage and sync
- Duplicated settings across files
- Complex Python classes with defaults
- Hard to see all configuration at once
- Pydantic complexity for simple YAML loading

## Migration Steps

1. **Automatic Migration** (if starting fresh):
   ```bash
   python migrate_config.py
   ```

2. **Manual Setup** (recommended):
   - Copy your settings from old files to `config.yaml`
   - Follow the structure shown above
   - Test with: `python config_example.py`

3. **Clean Up** (after testing):
   ```bash
   # Remove old config files (optional)
   rm basic_config.yaml db_config.yaml kb_config.yaml model_config.yaml tavily_config.yaml
   ```

## Key Features

### Environment Path Resolution
- Automatically resolves paths relative to `PENTEST_ROOT`
- Creates directories as needed (`logs/`, `data/knowledge_base/`)

### Dynamic Configuration
```python
# Runtime changes
config.set('basic.log_verbose', False)
config.reload()  # Reload from file
config.save()    # Save current state
```

### Default Values
- Built-in sensible defaults for all settings
- Missing values return `None` or specified defaults
- No crashes on missing configuration keys

## Configuration Validation

Test your configuration:
```bash
python config_example.py
```

This will show all access methods and validate the configuration loads correctly.

## Environment Variables

Set custom config location:
```bash
export PENTEST_ROOT=/path/to/vulnbot
# Will look for config.yaml in this directory
```

## Security Notes

- Keep `config.yaml` secure (contains API keys)
- Use environment variables for sensitive values in production
- The simplified system makes it easier to audit all settings

---

**Result**: Configuration management is now much simpler with a single, well-organized YAML file that's easy to understand, modify, and deploy!
