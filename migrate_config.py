#!/usr/bin/env python3
"""
Configuration Migration Script
Migrate from multiple YAML config files to single config.yaml
"""

import os
import yaml
from pathlib import Path

def migrate_configs():
    """Migrate old configuration files to new single config.yaml"""
    
    root = Path(".")
    config_files = {
        "basic_config.yaml": "basic",
        "db_config.yaml": "database", 
        "kb_config.yaml": "knowledge_base",
        "model_config.yaml": "llm",
        "tavily_config.yaml": "tavily"
    }
    
    merged_config = {}
    
    for old_file, section in config_files.items():
        file_path = root / old_file
        if file_path.exists():
            print(f"Migrating {old_file} -> config.yaml[{section}]")
            with open(file_path, 'r') as f:
                data = yaml.safe_load(f)
                if data:
                    merged_config[section] = data
        else:
            print(f"Skipping {old_file} (not found)")
    
    # Special handling for database config structure
    if "database" in merged_config and isinstance(merged_config["database"], dict):
        # No changes needed, structure is already correct
        pass
    
    # Write the merged configuration
    output_file = root / "config.yaml"
    with open(output_file, 'w') as f:
        yaml.dump(merged_config, f, default_flow_style=False, indent=2)
    
    print(f"✅ Migration complete! New config saved to {output_file}")
    print("\nYou can now:")
    print("1. Test the new configuration")
    print("2. Remove old config files if everything works:")
    for old_file in config_files.keys():
        if (root / old_file).exists():
            print(f"   rm {old_file}")


def validate_new_config():
    """Validate the new configuration file"""
    try:
        from config.simple_config import config
        print("✅ New configuration loads successfully!")
        print(f"Mode: {config.mode}")
        print(f"Tavily enabled: {config.tavily_enabled}")
        print(f"Log verbose: {config.log_verbose}")
        return True
    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
        return False


if __name__ == "__main__":
    print("VulnBot Configuration Migration")
    print("=" * 40)
    
    # Check if new config already exists
    if Path("config.yaml").exists():
        response = input("config.yaml already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("Migration cancelled.")
            exit(0)
    
    # Perform migration
    migrate_configs()
    
    # Validate new configuration
    print("\nValidating new configuration...")
    if validate_new_config():
        print("\n🎉 Migration successful!")
    else:
        print("\n⚠️  Please check the configuration manually.")
