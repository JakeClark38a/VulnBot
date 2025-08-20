"""
Example usage of the new simplified configuration system
"""

from config.config import config, Configs

def example_usage():
    print("=== VulnBot Simplified Configuration Usage ===\n")
    
    # Method 1: Direct access using dot notation
    print("1. Direct access:")
    print(f"   Mode: {config.get('basic.mode')}")
    print(f"   Tavily enabled: {config.get('tavily.enabled')}")
    print(f"   API key: {config.get('tavily.api_key', 'Not set')[:10]}...")
    
    # Method 2: Using convenience properties
    print("\n2. Convenience properties:")
    print(f"   Mode: {config.mode}")
    print(f"   Log verbose: {config.log_verbose}")
    print(f"   Tavily enabled: {config.tavily_enabled}")
    
    # Method 3: Section access
    print("\n3. Section access:")
    print(f"   Basic config: {list(config.basic.keys())}")
    print(f"   LLM model: {config.llm.get('llm_model_name', 'Not set')}")
    
    # Method 4: Backward compatibility (old-style access)
    print("\n4. Backward compatibility:")
    print(f"   Mode: {Configs.basic_config.mode}")
    print(f"   Tavily API key: {Configs.tavily_config.api_key[:10]}...")
    print(f"   MySQL host: {Configs.db_config.mysql.get('host')}")
    
    # Method 5: Dynamic updates
    print("\n5. Dynamic updates:")
    old_mode = config.get('basic.mode')
    config.set('basic.mode', 'manual')
    print(f"   Changed mode from '{old_mode}' to '{config.get('basic.mode')}'")
    config.set('basic.mode', old_mode)  # Restore
    print(f"   Restored mode to '{config.get('basic.mode')}'")
    
    # Method 6: Environment-specific paths
    print("\n6. Path handling:")
    print(f"   Log path: {config.log_path_resolved}")
    print(f"   KB path: {config.kb_root_path_resolved}")


if __name__ == "__main__":
    example_usage()
