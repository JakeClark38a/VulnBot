# Tavily Search Integration for VulnBot

This document describes how to configure and use the Tavily search integration in VulnBot for enhanced security intelligence gathering.

## Overview

The Tavily search integration allows VulnBot to perform web searches for:
- CVE research and vulnerability information
- Security advisories and patches  
- Exploit development guidance
- General security intelligence gathering

## Configuration

### 1. Enable Tavily Search

Add to `basic_config.yaml`:
```yaml
enable_tavily_search: true
```

OR add to `tavily_config.yaml`:
```yaml
enabled: true
```

### 2. Set API Key

Get a Tavily API key from [https://tavily.com](https://tavily.com) and add it to either:

**Option A: In `model_config.yaml`:**
```yaml
tavily_api_key: "your_api_key_here"
```

**Option B: In `tavily_config.yaml`:**
```yaml
api_key: "your_api_key_here"
```

### 3. Advanced Configuration (Optional)

Create or modify `tavily_config.yaml`:
```yaml
enabled: true
api_key: "your_api_key_here"
search_depth: "advanced"  # "basic" or "advanced"
max_results: 5
timeout: 30
include_answer: true
include_raw_content: true
truncate_content: 500

# Security-focused domains (automatically used for security searches)
security_domains:
  - "cve.mitre.org"
  - "nvd.nist.gov"
  - "github.com"
  - "security.snyk.io"
  - "cvedetails.com"
  - "exploit-db.com"

# Always include these domains
include_domains: []

# Always exclude these domains  
exclude_domains:
  - "ads.google.com"
  - "facebook.com"
```

## Usage

### 1. In VulnBot Tasks

VulnBot will automatically use Tavily search when the action is set to "Search". Example task instruction:

```xml
<execute>CVE-2024-1234 vulnerability details</execute>
```

### 2. Programmatic Usage

```python
from actions.tavily_search import TavilySearch, search_security_intelligence

# Quick search function
result = search_security_intelligence("SQL injection bypass WAF", max_results=3)
print(result)

# Advanced usage
search_tool = TavilySearch()

# CVE-specific search
cve_results = search_tool.search_cve("CVE-2024-1234")

# Exploit technique search
technique_results = search_tool.search_exploit_techniques("buffer overflow", "Linux")

# Custom search
custom_results = search_tool.search(
    "XSS payload encoding techniques",
    max_results=5,
    security_focused=True
)
```

### 3. Search Response Format

The search returns structured results:

```python
class TavilySearchResponse:
    query: str                          # Original search query
    results: List[TavilySearchResult]   # Search results
    answer: Optional[str]               # AI-generated summary
    images: List[str]                   # Related images (if any)
    response_time: float                # API response time

class TavilySearchResult:
    title: str              # Page title
    url: str               # Page URL
    content: str           # Page content/snippet
    score: float           # Relevance score
    published_date: str    # Publication date (if available)
```

## Security Features

### Domain Filtering
- **Security-focused domains**: Automatically prioritizes security-related sources
- **Include domains**: Force inclusion of specific domains
- **Exclude domains**: Block unwanted domains (ads, social media)

### Content Processing
- **Answer summaries**: AI-generated summaries of search results
- **Content truncation**: Limit content length for better processing
- **Raw content**: Option to include full page content

## Example Use Cases

### 1. CVE Research
```python
# Search for specific CVE
results = search_tool.search_cve("CVE-2024-1234")

# Get formatted summary
summary = search_tool.search_and_summarize("CVE-2024-1234 exploit proof of concept")
```

### 2. Exploit Development
```python
# Research exploitation techniques
results = search_tool.search_exploit_techniques("SQL injection", "MySQL")

# Find bypass techniques
bypass_info = search_security_intelligence("WAF bypass XSS techniques")
```

### 3. Vulnerability Assessment
```python
# Research specific technologies
results = search_tool.search("Apache Struts vulnerabilities 2024", security_focused=True)

# Find patches and mitigations
patch_info = search_security_intelligence("CVE-2024-1234 patch mitigation")
```

## Testing

Run the test script to verify configuration:

```bash
cd VulnBot
python test_tavily.py
```

## Error Handling

The integration includes robust error handling:

- **Missing API key**: Clear error messages with configuration instructions
- **API failures**: Graceful degradation with logged errors
- **Network issues**: Timeout handling and retry logic
- **Disabled service**: Informative messages when search is disabled

## Dependencies

Add to `requirements.txt`:
```
tavily-python==0.3.3
```

Install with:
```bash
pip install tavily-python
```

## Logging

Search activities are logged with the following information:
- Search queries performed
- Number of results returned
- API response times
- Any errors or failures

Check logs in the configured log directory for troubleshooting.

## Security Considerations

- **API Key Protection**: Store API keys securely, never commit to version control
- **Rate Limiting**: Tavily has rate limits; the integration respects these
- **Content Filtering**: Results are filtered for security relevance
- **Privacy**: Search queries are sent to Tavily's external service

## Troubleshooting

### Common Issues

1. **"Tavily search is disabled"**
   - Check `enable_tavily_search` in `basic_config.yaml` 
   - Or `enabled` in `tavily_config.yaml`

2. **"API key not configured"**
   - Set `tavily_api_key` in `model_config.yaml`
   - Or `api_key` in `tavily_config.yaml`

3. **"Import tavily could not be resolved"**
   - Install: `pip install tavily-python`

4. **API errors**
   - Verify API key is valid
   - Check Tavily service status
   - Review rate limits

### Debug Mode

Enable verbose logging to see detailed search operations:

```yaml
# In basic_config.yaml
log_verbose: true
```

This will log all search queries, responses, and timing information.
