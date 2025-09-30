import re
from typing import Dict, List, Optional
from server.chat.chat import _chat
from config.config import Configs


class ContentSummarizer:
    """Handles content summarization for managing token limits in LLM requests."""

    # Approximate token count (4 chars = 1 token for most models)
    CHARS_PER_TOKEN = 4
    MAX_TOKENS_SAFE = 4000  # Leave buffer for deepseek-r1-distill-llama-70b limit of 6000

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Estimate token count for given text."""
        return len(text) // ContentSummarizer.CHARS_PER_TOKEN

    @staticmethod
    def needs_summarization(text: str) -> bool:
        """Check if text exceeds safe token limit."""
        return ContentSummarizer.estimate_tokens(text) > ContentSummarizer.MAX_TOKENS_SAFE

    @staticmethod
    def extract_key_information(text: str) -> Dict[str, str]:
        """Extract key information from command output for better summarization."""
        key_info = {
            "vulnerabilities": [],
            "open_ports": [],
            "services": [],
            "errors": [],
            "recommendations": []
        }

        # Extract vulnerabilities
        vuln_patterns = [
            r"vulnerability|exploit|CVE-\d{4}-\d+|SQL injection|XSS|CSRF",
            r"potential.*vulnerability|security.*issue|weak.*password"
        ]
        for pattern in vuln_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            key_info["vulnerabilities"].extend(matches[:5])  # Limit to 5

        # Extract open ports
        port_matches = re.findall(r"(\d+/tcp|port \d+).*open", text, re.IGNORECASE)
        key_info["open_ports"] = port_matches[:10]  # Limit to 10

        # Extract services
        service_matches = re.findall(r"(http|https|ssh|ftp|mysql|apache|nginx|php).*version.*[\d\.]+", text, re.IGNORECASE)
        key_info["services"] = service_matches[:10]

        # Extract errors
        error_matches = re.findall(r"error:.*|failed.*|timeout.*|connection.*refused", text, re.IGNORECASE)
        key_info["errors"] = error_matches[:5]

        return key_info

    @staticmethod
    def summarize_content(content: str, conversation_id: str, context: str = "") -> str:
        """
        Summarize long content while preserving key security information.
        
        Args:
            content: The content to summarize
            conversation_id: Chat conversation ID for the summarization
            context: Additional context about what the content represents
        
        Returns:
            Summarized content
        """
        if not ContentSummarizer.needs_summarization(content):
            return content

        # Extract key information first
        key_info = ContentSummarizer.extract_key_information(content)

        # Create summarization prompt
        summarize_prompt = f"""
Please provide a concise summary of the following security testing output. Focus on:
1. Key findings (vulnerabilities, exploits, exposed services)
2. Important technical details (ports, versions, configurations)
3. Security implications and recommendations
4. Any errors or failures that occurred

Context: {context}

Key Information Extracted:
- Vulnerabilities: {', '.join(key_info['vulnerabilities'][:3]) if key_info['vulnerabilities'] else 'None detected'}
- Open Ports: {', '.join(key_info['open_ports'][:5]) if key_info['open_ports'] else 'None found'}
- Services: {', '.join(key_info['services'][:3]) if key_info['services'] else 'None identified'}
- Errors: {', '.join(key_info['errors'][:2]) if key_info['errors'] else 'None reported'}

Content to summarize (showing first 2000 characters):
{content[:2000]}{'...' if len(content) > 2000 else ''}

Provide a structured summary that maintains all critical security information while being concise.
"""

        try:
            summary = _chat(
                query=summarize_prompt,
                conversation_id=f"{conversation_id}_summarize",
                kb_name=Configs.kb_config.kb_name if hasattr(Configs, 'kb_config') else None,
                kb_query=context
            )
            
            # If summarization fails, use fallback
            if not summary or summary.startswith("**ERROR**"):
                return ContentSummarizer._fallback_summarize(content, key_info)
            
            return summary
            
        except Exception as e:
            print(f"Summarization failed: {e}")
            return ContentSummarizer._fallback_summarize(content, key_info)

    @staticmethod
    def _fallback_summarize(content: str, key_info: Dict) -> str:
        """Fallback summarization when LLM is unavailable."""
        summary_parts = []
        
        if key_info["vulnerabilities"]:
            summary_parts.append(f"VULNERABILITIES: {', '.join(key_info['vulnerabilities'][:3])}")
        
        if key_info["open_ports"]:
            summary_parts.append(f"OPEN PORTS: {', '.join(key_info['open_ports'][:5])}")
        
        if key_info["services"]:
            summary_parts.append(f"SERVICES: {', '.join(key_info['services'][:3])}")
        
        if key_info["errors"]:
            summary_parts.append(f"ERRORS: {', '.join(key_info['errors'][:2])}")
        
        # Add first and last 300 characters
        summary_parts.append(f"CONTENT PREVIEW: {content[:300]}...")
        if len(content) > 600:
            summary_parts.append(f"CONTENT ENDING: ...{content[-300:]}")
        
        return "\n".join(summary_parts)

    @staticmethod
    def create_clean_chat_context(user_description: str, system_prompt: str, 
                                summary: str, current_task: str = "") -> str:
        """
        Create a clean chat context for reinitialization.
        
        Args:
            user_description: Original user description/task
            system_prompt: System prompt for the agent
            summary: Summarized context from previous operations
            current_task: Current task being worked on
        
        Returns:
            Clean context string for chat reinitialization
        """
        context = f"""# PENETRATION TESTING SESSION CONTEXT

## Original User Request:
{user_description}

## System Instructions:
{system_prompt}

## Previous Operations Summary:
{summary}

## Current Focus:
{current_task if current_task else "Continue with next planned task"}

## Instructions:
Based on the above context and summary, continue the penetration testing process. Focus on the current task while being aware of previous findings.
"""
        return context