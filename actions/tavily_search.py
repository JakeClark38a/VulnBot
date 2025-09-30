"""
Tavily Search Tool for VulnBot

Provides web search capabilities using Tavily API for:
- CVE research and vulnerability information
- Security advisories and patches
- Exploit development guidance
- General security intelligence gathering
"""

import json
from typing import List, Dict, Optional
from pydantic import BaseModel, Field

try:
    from tavily import TavilyClient
    TAVILY_AVAILABLE = True
except ImportError:
    TAVILY_AVAILABLE = False
    TavilyClient = None

from config.config import Configs
from utils.log_common import build_logger

logger = build_logger()


class TavilySearchResult(BaseModel):
    """Individual search result from Tavily"""
    title: str
    url: str
    content: str
    score: float = 0.0
    published_date: Optional[str] = None


class TavilySearchResponse(BaseModel):
    """Complete response from Tavily search"""
    query: str
    results: List[TavilySearchResult]
    answer: Optional[str] = None
    images: List[str] = []
    response_time: float = 0.0


class TavilySearch(BaseModel):
    """
    Tavily Search Tool for security research and vulnerability intelligence
    
    Usage:
        search = TavilySearch()
        results = search.search("CVE-2024-1234 exploit")
        summary = search.search_and_summarize("buffer overflow techniques")
    """
    
    api_key: str = Field(default_factory=lambda: Configs.tavily_config.api_key or Configs.llm_config.tavily_api_key)
    max_results: int = Field(default_factory=lambda: Configs.tavily_config.max_results)
    search_depth: str = Field(default_factory=lambda: Configs.tavily_config.search_depth)
    include_domains: List[str] = Field(default_factory=lambda: Configs.tavily_config.include_domains or [])
    exclude_domains: List[str] = Field(default_factory=lambda: Configs.tavily_config.exclude_domains or [])
    
    class Config:
        arbitrary_types_allowed = True
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not TAVILY_AVAILABLE:
            raise ImportError("tavily-python library not installed. Run: pip install tavily-python")
        if not self.api_key:
            raise ValueError("Tavily API key not configured. Set tavily_api_key in model_config.yaml")
        self._client = TavilyClient(api_key=self.api_key)
    
    @property
    def client(self):
        """Get the Tavily client instance"""
        if not hasattr(self, '_client'):
            self._client = TavilyClient(api_key=self.api_key)
        return self._client
    
    def search(self, 
               query: str, 
               max_results: Optional[int] = None,
               include_answer: bool = True,
               include_raw_content: bool = True,
               security_focused: bool = True) -> TavilySearchResponse:
        """
        Perform web search using Tavily API
        
        Args:
            query: Search query (e.g., "CVE-2024-1234", "SQL injection bypass techniques")
            max_results: Number of results to return (default: self.max_results)
            include_answer: Include AI-generated answer summary
            include_raw_content: Include full content of pages
            security_focused: Add security-focused domains to search
            
        Returns:
            TavilySearchResponse with search results
        """
        if not Configs.tavily_config.enabled and not Configs.basic_config.enable_tavily_search:
            logger.warning("Tavily search is disabled in configuration")
            return TavilySearchResponse(query=query, results=[])
        
        if not self.api_key:
            logger.error("Tavily API key not configured")
            return TavilySearchResponse(query=query, results=[])
        
        max_results = max_results or self.max_results
        
        # Security-focused domains for vulnerability research
        security_domains = Configs.tavily_config.security_domains if security_focused else []
        security_domains = security_domains or []  # Handle None case
        
        # Handle None values for include_domains and exclude_domains
        include_domains_list = self.include_domains or []
        include_domains = list(set(include_domains_list + security_domains))
        
        logger.info(f"Searching Tavily for: {query}")
        
        try:
            # Use the tavily client for search
            exclude_domains_list = self.exclude_domains or []
            response = self.client.search(
                query=query,
                search_depth=self.search_depth,
                max_results=max_results,
                include_answer=include_answer,
                include_raw_content=include_raw_content,
                include_domains=include_domains,
                exclude_domains=exclude_domains_list
            )
            
            results = []
            for item in response.get("results", []):
                result = TavilySearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    content=item.get("content", ""),
                    score=item.get("score", 0.0),
                    published_date=item.get("published_date")
                )
                results.append(result)
            
            tavily_response = TavilySearchResponse(
                query=query,
                results=results,
                answer=response.get("answer"),
                images=response.get("images", []),
                response_time=response.get("response_time", 0.0)
            )
            
            logger.info(f"Found {len(results)} results for '{query}'")
            return tavily_response
            
        except Exception as e:
            logger.error(f"Tavily search failed for '{query}': {e}")
            return TavilySearchResponse(query=query, results=[])
    
    def search_and_summarize(self, query: str, focus: str = "security") -> str:
        """
        Search and return a formatted summary suitable for penetration testing context
        
        Args:
            query: Search query
            focus: Focus area ("security", "exploits", "patches", "general")
            
        Returns:
            Formatted text summary of search results
        """
        response = self.search(query, include_answer=True)
        
        if not response.results:
            return f"No search results found for: {query}"
        
        summary_parts = []
        
        # Add AI answer if available
        if response.answer:
            summary_parts.append(f"**Summary:** {response.answer}\n")
        
        # Add search results
        summary_parts.append(f"**Search Results for '{query}':**\n")
        
        for i, result in enumerate(response.results[:3], 1):  # Top 3 results
            summary_parts.append(f"{i}. **{result.title}**")
            summary_parts.append(f"   URL: {result.url}")
            if result.content:
                # Truncate content for readability
                content = result.content[:300] + "..." if len(result.content) > 300 else result.content
                summary_parts.append(f"   Content: {content}")
            summary_parts.append("")
        
        return "\n".join(summary_parts)
    
    def search_cve(self, cve_id: str) -> TavilySearchResponse:
        """
        Search for specific CVE information
        
        Args:
            cve_id: CVE identifier (e.g., "CVE-2024-1234")
            
        Returns:
            TavilySearchResponse with CVE-specific results
        """
        query = f"{cve_id} vulnerability details exploit poc"
        return self.search(query, security_focused=True)
    
    def search_exploit_techniques(self, technique: str, target_tech: str = "") -> TavilySearchResponse:
        """
        Search for exploit techniques and methodologies
        
        Args:
            technique: Exploit technique (e.g., "SQL injection", "buffer overflow")
            target_tech: Target technology (e.g., "MySQL", "Apache", "Windows")
            
        Returns:
            TavilySearchResponse with technique-specific results
        """
        query = f"{technique} exploit technique"
        if target_tech:
            query += f" {target_tech}"
        query += " penetration testing methodology"
        
        return self.search(query, security_focused=True)


def search_security_intelligence(query: str, max_results: int = 3) -> str:
    """
    Convenience function for quick security intelligence searches
    
    Args:
        query: Search query
        max_results: Number of results to include
        
    Returns:
        Formatted search summary
    """
    if not Configs.tavily_config.enabled and not Configs.basic_config.enable_tavily_search:
        return "Tavily search is disabled in configuration."
    
    try:
        search_tool = TavilySearch(max_results=max_results)
        return search_tool.search_and_summarize(query)
    except Exception as e:
        logger.error(f"Security intelligence search failed: {e}")
        return f"Search failed: {str(e)}"


# Example usage and testing
if __name__ == "__main__":
    # Test the search functionality
    search = TavilySearch()
    
    # Test CVE search
    print("=== CVE Search Test ===")
    cve_results = search.search_cve("CVE-2024-1234")
    print(f"Found {len(cve_results.results)} results")
    
    # Test general security search
    print("\n=== General Security Search Test ===")
    summary = search.search_and_summarize("SQL injection bypass techniques")
    print(summary)
