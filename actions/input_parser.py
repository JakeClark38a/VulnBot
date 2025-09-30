"""
Input Parser for VulnBot
Extracts target information, attack specifications, and other parameters from user descriptions
"""
import re
import json
from typing import Dict, List, Optional, Union, ClassVar
from pydantic import BaseModel, Field

from server.chat.chat import _chat
from utils.log_common import build_logger

logger = build_logger()


class TargetInfo(BaseModel):
    """Target information extracted from user input"""
    host: Optional[str] = None
    ip: Optional[str] = None
    ports: List[int] = Field(default_factory=list)
    url: Optional[str] = None
    domain: Optional[str] = None
    
    @property
    def primary_target(self) -> str:
        """Returns the primary target identifier (IP, host, or domain)"""
        return self.ip or self.host or self.domain or "target"


class AttackInfo(BaseModel):
    """Attack specifications extracted from user input"""
    allowed_attacks: List[str] = Field(default_factory=list)
    forbidden_attacks: List[str] = Field(default_factory=list)
    specific_goals: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)


class ParsedInput(BaseModel):
    """Complete parsed user input"""
    target: TargetInfo = Field(default_factory=TargetInfo)
    attacks: AttackInfo = Field(default_factory=AttackInfo)
    original_description: str = ""
    cleaned_description: str = ""


class InputParser(BaseModel):
    """LLM-based parser to extract structured information from user input"""
    
    PARSE_PROMPT: ClassVar[str] = """You are an expert at parsing penetration testing task descriptions. Extract ONLY the target host/IP address from the user's input.

**Your task**: Parse the following penetration testing description and extract:
1. Target information (ONLY the main target IP address or hostname that should be attacked)
2. Attack specifications (allowed attacks, forbidden attacks, goals, constraints)
3. A cleaned description for system use

**IMPORTANT RULES**:
- Extract ONLY the primary target host/IP that should be attacked
- IGNORE localhost, 127.0.0.1, or any local addresses (these are destinations, not targets)
- IGNORE ports mentioned in "NOT ALLOWED" or forbidden sections
- IGNORE ports that are for outbound requests (like sending data TO somewhere)
- Focus on the main target that the penetration testing should be performed AGAINST

**Input Description**:
{user_input}

**Output Format** (JSON only, no additional text):
```json
{{
    "target": {{
        "host": "hostname or null",
        "ip": "IP address or null", 
        "ports": [],
        "url": "URL or null",
        "domain": "domain name or null"
    }},
    "attacks": {{
        "allowed_attacks": ["list of allowed attack types"],
        "forbidden_attacks": ["list of forbidden attack types"],
        "specific_goals": ["list of specific goals mentioned"],
        "constraints": ["list of constraints or limitations"]
    }},
    "cleaned_description": "A clean, concise description suitable for system prompts, focusing on the target and main objectives"
}}
```

**Important**:
- Extract the PRIMARY target host/IP that should be penetration tested
- Do NOT include localhost or 127.x.x.x addresses as targets
- Do NOT include ports that are forbidden or in "NOT ALLOWED" sections
- The cleaned_description should be 1-2 sentences focusing on target and main goals
- Use null for missing information, don't guess

**Example**:
Input: "Test target 192.168.1.100 for SQL injection, database access. Send results to localhost:8000. NOT ALLOWED: brute force attacks, SSH port 22 interaction."

Output:
```json
{{
    "target": {{
        "host": null,
        "ip": "192.168.1.100",
        "ports": [],
        "url": null,
        "domain": null
    }},
    "attacks": {{
        "allowed_attacks": ["SQL injection", "database access"],
        "forbidden_attacks": ["brute force attacks", "SSH interaction"],
        "specific_goals": ["database access", "send results to localhost:8000"],
        "constraints": ["no port 22 interaction"]
    }},
    "cleaned_description": "Perform penetration testing on target 192.168.1.100 focusing on web application security and database access."
}}
```
"""

    def parse_input(self, user_input: str) -> ParsedInput:
        """Parse user input using LLM and return structured information"""
        try:
            logger.info(f"Parsing user input: {user_input[:100]}...")
            
            # Use LLM to parse the input
            response, _ = _chat(
                query=self.PARSE_PROMPT.format(user_input=user_input),
                conversation_id=None,  # Fresh conversation for parsing
                summary=False
            )
            
            logger.info(f"LLM parse response: {response}")
            
            # Extract JSON from response
            parsed_data = self._extract_json_from_response(response)
            
            # Create structured objects
            target_info = TargetInfo(**parsed_data.get("target", {}))
            attack_info = AttackInfo(**parsed_data.get("attacks", {}))
            cleaned_description = parsed_data.get("cleaned_description", user_input)
            
            result = ParsedInput(
                target=target_info,
                attacks=attack_info,
                original_description=user_input,
                cleaned_description=cleaned_description
            )
            
            logger.info(f"Successfully parsed input. Target: {target_info.primary_target}")
            return result
            
        except Exception as e:
            logger.error(f"Error parsing input: {e}")
            # Fallback: try regex-based parsing
            return self._fallback_parse(user_input)
    
    def _extract_json_from_response(self, response: str) -> Dict:
        """Extract JSON from LLM response"""
        # Try to find JSON block in response
        json_pattern = r'```json\s*(\{.*?\})\s*```'
        match = re.search(json_pattern, response, re.DOTALL)
        
        if match:
            json_str = match.group(1)
        else:
            # Try to find JSON without markdown
            json_pattern = r'\{.*\}'
            match = re.search(json_pattern, response, re.DOTALL)
            if match:
                json_str = match.group(0)
            else:
                raise ValueError("No JSON found in response")
        
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            logger.error(f"JSON string: {json_str}")
            raise
    
    def _fallback_parse(self, user_input: str) -> ParsedInput:
        """Fallback regex-based parsing when LLM fails"""
        logger.info("Using fallback regex parsing")
        
        # Extract IP addresses (but filter out localhost)
        ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        ips = re.findall(ip_pattern, user_input)
        # Filter out localhost IPs
        ips = [ip for ip in ips if not ip.startswith('127.') and not ip.startswith('localhost')]
        
        # Extract hostnames (avoid localhost)
        hostname_pattern = r'target[:\s]+([a-zA-Z0-9.-]+)'
        hostname_matches = re.findall(hostname_pattern, user_input, re.IGNORECASE)
        hostnames = [h for h in hostname_matches if h != 'localhost']
        
        # Extract ports mentioned with target (not forbidden ones)
        # Look for ports that are NOT in forbidden context
        forbidden_section = re.search(r'not\s+allowed.*?(?=\n\n|\Z)', user_input, re.IGNORECASE | re.DOTALL)
        forbidden_text = forbidden_section.group(0) if forbidden_section else ""
        
        port_pattern = r'(?:target.*?)?(?:port\s+(\d+)|:(\d+))'
        port_matches = re.findall(port_pattern, user_input, re.IGNORECASE)
        ports = []
        for match in port_matches:
            port = match[0] or match[1]
            if port and port not in forbidden_text:
                ports.append(int(port))
        
        # Extract forbidden attacks
        forbidden_pattern = r'not\s+allowed[:\s]*(.+?)(?:\n\n|$)'
        forbidden_match = re.search(forbidden_pattern, user_input, re.IGNORECASE | re.DOTALL)
        forbidden_attacks = []
        if forbidden_match:
            forbidden_text = forbidden_match.group(1)
            # Split by common delimiters
            forbidden_attacks = [item.strip().rstrip('.') for item in re.split(r'[,\n\d+\.]', forbidden_text) if item.strip()]
        
        # Choose primary target
        primary_ip = ips[0] if ips else None
        primary_host = hostnames[0] if hostnames else None
        
        # Create basic parsed result
        target_info = TargetInfo(
            ip=primary_ip,
            host=primary_host,
            ports=ports[:3] if ports else []  # Limit to first 3 relevant ports
        )
        
        attack_info = AttackInfo(
            forbidden_attacks=forbidden_attacks
        )
        
        # Create a basic cleaned description
        target_identifier = primary_ip or primary_host or "target"
        cleaned_description = f"Perform penetration testing on target {target_identifier}"
        
        return ParsedInput(
            target=target_info,
            attacks=attack_info,
            original_description=user_input,
            cleaned_description=cleaned_description
        )


def parse_user_input(user_input: str) -> ParsedInput:
    """Convenience function to parse user input"""
    parser = InputParser()
    return parser.parse_input(user_input)


def create_enhanced_description(parsed_input: ParsedInput) -> str:
    """Create an enhanced description that includes target information for prompts"""
    base_desc = parsed_input.cleaned_description
    target = parsed_input.target
    
    # Add explicit target information
    if target.primary_target != "target":
        enhanced = f"Target: {target.primary_target}. {base_desc}"
    else:
        enhanced = base_desc
    
    # Add port information if available
    if target.ports:
        enhanced += f" Focus on ports: {', '.join(map(str, target.ports))}."
    
    # Add constraints if any
    if parsed_input.attacks.forbidden_attacks:
        enhanced += f" FORBIDDEN: {', '.join(parsed_input.attacks.forbidden_attacks)}."
    
    return enhanced