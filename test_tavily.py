#!/usr/bin/env python3
"""
Test script for Tavily Search integration in VulnBot

Usage:
    python test_tavily.py

Make sure to:
1. Set tavily_api_key in model_config.yaml or tavily_config.yaml
2. Enable tavily search in basic_config.yaml (enable_tavily_search: true)
   OR in tavily_config.yaml (enabled: true)
"""

import sys
import os

# Add VulnBot to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_configuration():
    """Test if Tavily is properly configured"""
    print("=== Tavily Configuration Test ===")
    
    try:
        from config.config import Configs
        print(f"Basic config enable_tavily_search: {getattr(Configs.basic_config, 'enable_tavily_search', 'Not set')}")
        print(f"Tavily config enabled: {getattr(Configs.tavily_config, 'enabled', 'Not set')}")
        
        tavily_api_key = getattr(Configs.tavily_config, 'api_key', '') or getattr(Configs.llm_config, 'tavily_api_key', '')
        print(f"API key configured: {'Yes' if tavily_api_key else 'No'}")
        print(f"Max results: {getattr(Configs.tavily_config, 'max_results', 'Not set')}")
        print(f"Search depth: {getattr(Configs.tavily_config, 'search_depth', 'Not set')}")
    except Exception as e:
        print(f"Configuration test failed: {e}")
    print()

def test_search_function():
    """Test the convenience search function"""
    print("=== Testing search_security_intelligence function ===")
    
    try:
        from actions.tavily_search import search_security_intelligence
        test_query = "SQL injection bypass techniques"
        print(f"Searching for: {test_query}")
        
        result = search_security_intelligence(test_query, max_results=2)
        print("Result:")
        print(result)
    except Exception as e:
        print(f"Search function test failed: {e}")
    print()

def test_search_tool():
    """Test the TavilySearch class directly"""
    print("=== Testing TavilySearch class ===")
    
    try:
        from actions.tavily_search import TavilySearch
        search_tool = TavilySearch()
        
        # Test CVE search
        print("Testing CVE search...")
        cve_result = search_tool.search_cve("CVE-2023-1234")
        print(f"CVE search returned {len(cve_result.results)} results")
        
        if cve_result.answer:
            print(f"AI Answer: {cve_result.answer[:200]}...")
        
    except Exception as e:
        print(f"TavilySearch test failed: {e}")
    print()

def main():
    """Run all tests"""
    print("VulnBot Tavily Search Integration Test")
    print("=" * 50)
    
    test_configuration()
    
    # Test basic imports
    try:
        from actions.tavily_search import search_security_intelligence
        print("✓ Tavily search module imports successfully")
        
        from config.config import Configs
        enabled = getattr(Configs.basic_config, 'enable_tavily_search', False) or \
                 getattr(Configs.tavily_config, 'enabled', False)
        api_key = getattr(Configs.tavily_config, 'api_key', '') or \
                 getattr(Configs.llm_config, 'tavily_api_key', '')
        
        if enabled and api_key:
            print("✓ Tavily is properly configured - you can run searches")
            test_search_function()
        else:
            print("⚠ Tavily not fully configured:")
            if not enabled:
                print("  - Enable in basic_config.yaml (enable_tavily_search: true)")
                print("  - OR in tavily_config.yaml (enabled: true)")
            if not api_key:
                print("  - Set API key in model_config.yaml (tavily_api_key)")
                print("  - OR in tavily_config.yaml (api_key)")
                
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        print("Install dependencies: pip install -r requirements.txt")
    except Exception as e:
        print(f"✗ Configuration error: {e}")

if __name__ == "__main__":
    main()
