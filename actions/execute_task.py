import re
import time
from typing import List

from click import prompt
from pydantic import BaseModel

from actions.run_code import RunCode
from actions.shell_manager import ShellManager
from actions.tavily_search import search_security_intelligence
from actions.remote_shell import sanitize_ansi_concealed_payload
from config.config import Configs, Mode

from utils.log_common import build_logger
from prompt_toolkit import prompt

logger = build_logger()


class ExecuteResult(BaseModel):
    context: object
    response: str


class ExecuteTask(BaseModel):
    action: str
    instruction: str
    code: List[str]

    def parse_response(self) -> list[str]:
        # Remove reasoning blocks before extracting actionable directives
        cleaned_instruction = re.sub(r'<think>.*?</think>', '', self.instruction, flags=re.DOTALL | re.IGNORECASE)

        tag = "search" if self.action == "Search" else "execute"
        pattern = rf'<{tag}>\s*(.*?)\s*</{tag}>'
        initial_matches = re.findall(pattern, cleaned_instruction, re.DOTALL)

        # Fallback for legacy outputs that might still use <execute> tags for search actions
        if not initial_matches and tag == "search":
            initial_matches = re.findall(r'<execute>\s*(.*?)\s*</execute>', cleaned_instruction, re.DOTALL)

        cleaned_matches = []
        for match in initial_matches:
            cleaned_matches.append(match.strip())

        return cleaned_matches

    @staticmethod
    def _is_command_like(query: str) -> bool:
        lowered = query.strip().lower()
        if not lowered:
            return False

        command_delimiters = [';', '&&', '|', '`', '$(', '>>', '<<']
        if any(delim in lowered for delim in command_delimiters):
            return True

        command_keywords = {
            'nmap', 'curl', 'wget', 'ssh', 'sudo', 'ls', 'cat', 'chmod', 'chown', 'rm',
            'python', 'perl', 'bash', 'sh', 'ftp', 'smbclient', 'gcc', 'apt', 'pip',
            'dirb', 'gobuster', 'nikto', 'sqlmap', 'hydra', 'nc', 'netcat', 'telnet'
        }

        first_token = lowered.split()[0]
        return first_token in command_keywords

    def run(self) -> ExecuteResult:
        if Configs.basic_config.mode == Mode.SemiAuto:
            if self.action == "Shell":
                result = self.shell_operation()
            elif self.action == "Search":
                result = self.search_operation()
            else:
                result = prompt("Please enter the manual run command and enter the result.\n> ")
        elif Configs.basic_config.mode == Mode.Manual:
            result = prompt("Please enter the manual run command and enter the result.\n> ")
        else:
            if self.action == "Search":
                result = self.search_operation()
            else:
                result = self.shell_operation()

        return ExecuteResult(context={
            "action": self.action,
            "instruction": self.instruction,
            "code": self.code,
        }, response=result)

    def search_operation(self):
        """Handle Tavily search operations"""
        result = ""
        search_queries = self.parse_response()
        if not search_queries:
            logger.warning("No Tavily search queries parsed from instruction")
            return "No search queries provided."

        executable_queries = []
        logger.info(f"Running Tavily searches: {search_queries}")
        
        try:
            for i, raw_query in enumerate(search_queries, 1):
                query = raw_query.strip()
                if not query:
                    continue

                if self._is_command_like(query):
                    warning = f"Rejected query {i}: looks like a shell command -> {query}"
                    logger.warning(warning)
                    result += warning + "\n"
                    continue

                executable_queries.append(query)
                result += f'Search Query {len(executable_queries)}: {query}\n'
                search_result = search_security_intelligence(query, max_results=3)
                result += f'Search Results:\n{search_result}\n\n'
        except Exception as e:
            logger.error(f"Tavily search failed: {e}")
            result = f"Search operation failed: {str(e)}"
            executable_queries = []

        self.code = executable_queries
        return result

    def shell_operation(self):
        result = ""
        thought = self.parse_response()
        self.code = thought
        logger.info(f"Running {thought}")
        # Execute command list
        shell = ShellManager.get_instance().get_shell()
        try:
            SMB_PROMPTS = [
                'command not found',
                '?Invalid command.'
            ]

            PASSWORD_PROMPTS = [
                'password:',
                'Password for'
                '[sudo] password for',
            ]

            skip_next = False

            for i, command in enumerate(self.code):
                # 添加跳过标记
                if skip_next:
                    skip_next = False
                    continue

                result += f'Action:{command}\nObservation: '
                output = shell.execute_cmd(command)
                result += output + '\n'
                out_line = output.strip().split('\n')

                last_line = out_line[-1]

                if any(prompt in last_line for prompt in PASSWORD_PROMPTS):
                    if i + 1 < len(self.code):
                        result += f'Action:{self.code[i + 1]}\nObservation: '
                        next_output = shell.execute_cmd(self.code[i + 1])
                        result += next_output + '\n'
                        skip_next = True
                        if any(prompt in next_output.strip().split('\n')[-1] for prompt in PASSWORD_PROMPTS):
                            shell.shell.send('\x03')  # Send Ctrl+C
                            time.sleep(0.5)  # Wait for Ctrl+C to take effect
                            # Clear the previous result
                            result = result.rsplit('Action:', 1)[0] + f'Action:{self.code[i + 1]}\nObservation: '
                            # Resend the second command
                            new_output = shell.execute_cmd(self.code[i + 1])
                            result += new_output + '\n'
                    else:
                        shell.shell.send('\x03')  # Send Ctrl+C for single command case

                if any(prompt in last_line for prompt in ['smb:', 'ftp>']):
                    if len(out_line) > 1 and any(prompt in out_line[-2] for prompt in SMB_PROMPTS):
                        shell.execute_cmd('exit')
                        time.sleep(0.5)
                        result = result.rsplit('Action:', 1)[0] + f'Action:{command}\nObservation: '
                        new_output = shell.execute_cmd(command)
                        result += new_output + '\n'

        except Exception as e:
            print(e)
            result = "Before sending a remote command you need to set-up an SSH connection."
        
        # Apply ANSI payload sanitization to the complete result
        result = sanitize_ansi_concealed_payload(result)
        return result
