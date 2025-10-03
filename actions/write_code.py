
from pydantic import BaseModel, Field

from actions.execute_task import ExecuteTask
from prompts.prompt import DeepPentestPrompt
from server.chat.chat import _chat
from utils.log_common import build_logger

logger = build_logger()

class WriteCode(BaseModel):

    next_task: str
    action: str
    target_host: str = Field(default="target")
    user_instruction: str = Field(default="")

    def run(self):

        logger.info(f"next_task: {self.next_task}")
        logger.info(f"target_host: {self.target_host}")
        
        # Select prompt based on action type and use a fresh conversation ID
        if self.action == "Search":
            prompt_template = DeepPentestPrompt.write_search
        else:
            prompt_template = DeepPentestPrompt.write_code

        response, _ = _chat(
            query=prompt_template.format(
                next_task=self.next_task,
                target_host=self.target_host,
                user_instruction=self.user_instruction
            ),
            conversation_id=None,  # Fresh conversation to avoid cross-contamination
            summary=False
        )
        logger.info(f"LLM Response: {response}")

        code_executor = ExecuteTask(action=self.action, instruction=response, code=[])

        result = code_executor.run()
        return result
