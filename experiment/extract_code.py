
from pydantic import BaseModel, Field

from actions.execute_task import ExecuteTask
from experiment.execute import Execute
from prompts.prompt import DeepPentestPrompt
from server.chat.chat import _chat
from utils.log_common import build_logger

logger = build_logger()

class ExtractCode(BaseModel):

    next_task: str

    agent: object


    def run(self):

        extract_code = """You play as an autonomous penetration testing assistant running on Kali Linux 2023.
        You are proficient in using the command line for all penetration testing tools and have an in-depth understanding of their parameters.
        Your task is to generate shell commands based on the Next Task, and wrap them in <execute></execute> tags.
        
        CRITICAL PLACEHOLDER REPLACEMENT RULES:
        - Replace ALL placeholders with ACTUAL values found in the task description
        - Placeholders like <target-ip>, <username>, <password>, <port> MUST be replaced with real values
        - Extract actual IP addresses, usernames, ports from the task context
        - NEVER output commands with angle bracket placeholders like <target-ip>
        
        ## Next Task:
        {next_task}
        ## Example Cases:
        ### Example1:
        Input: Next task: Perform OS fingerprinting on the target machine 10.0.0.5. You can follow the instructions below to complete the tasks. Sure, I can provide the next task for the junior penetration tester to perform OS fingerprinting on the target machine. Here's the task: Task: Perform OS fingerprinting on the target machine. Command: nmap -O 10.0.0.5.
        Output: <execute>nmap -O 10.0.0.5</execute>
        ### Example2:
        Input: Next task: Description: Investigate the SSH service on port 22 on target 192.168.1.100, attempt to establish a connection using username 'admin', and perform a basic enumeration of available files. Command: 
        ```bash
        ssh admin@192.168.1.100
        password123
        ls -la
        cat /etc/passwd
        ```
        Output: <execute>ssh admin@192.168.1.100</execute> <execute>password123</execute> <execute>ls -la</execute> <execute>cat /etc/passwd</execute>
        """
        logger.info(f"next_task: {self.next_task}")

        response, _ = self.agent.send_new_message(extract_code.format(next_task=self.next_task))
        logger.info(f"LLM Response: {response}")

        code_executor = Execute(instruction=response, code=[])

        result = code_executor.run()

        return result
