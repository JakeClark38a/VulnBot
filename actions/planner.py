import hashlib
import re
from typing import Optional

from pydantic import BaseModel

from actions.write_plan import WritePlan, parse_tasks, merge_tasks
from config.config import Configs
from db.models.task_model import TaskModel, Task
from prompts.prompt import DeepPentestPrompt
from db.models.plan_model import Plan
from server.chat.chat import _chat, is_rate_limit_error, reset_conversation_with_context
from actions.content_summarizer import ContentSummarizer
from utils.log_common import build_logger

logger = build_logger()


def _parse_success_flag(response: Optional[str]) -> Optional[bool]:
    """Extract the final yes/no decision from an LLM response, ignoring thinking blocks."""
    if not response:
        return None

    cleaned = re.sub(r'<think>.*?</think>', '', response, flags=re.IGNORECASE | re.DOTALL)
    matches = re.findall(r'\b(yes|no)\b', cleaned.lower())
    if matches:
        return matches[-1] == 'yes'
    return None


class Planner(BaseModel):
    current_plan: Plan = None
    init_description: str = ""
    target_host: str = "target"

    def plan(self):
        if self.current_plan.current_task:
            next_task = self.next_task_details()
            return next_task

        response = WritePlan(
            plan_chat_id=self.current_plan.plan_chat_id,
            target_host=self.target_host,
            user_instruction=self.init_description
        ).run(self.init_description)

        logger.info(f"plan (raw): {response}")

        try:
            self.current_plan = parse_tasks(response, self.current_plan)
        except Exception as e:
            logger.error(f"Failed to build plan: {e}")
            # Abort planning; caller will see None and can decide to retry or terminate.
            return None

        next_task = self.next_task_details()

        return next_task

    def update_plan(self, result):

        # Check if result needs summarization due to size
        if ContentSummarizer.needs_summarization(result):
            logger.info("Result is too long, summarizing before processing...")
            result = ContentSummarizer.summarize_content(
                content=result,
                conversation_id=self.current_plan.react_chat_id,
                context="Command execution result for penetration testing"
            )

        check_success = _chat(
            query=DeepPentestPrompt.check_success.format(result=result),
            conversation_id=self.current_plan.react_chat_id
        )

        logger.info(f"check_success: {check_success}")

        # Check if we got a rate limit error
        if check_success and is_rate_limit_error(check_success):
            logger.warning("Rate limit error detected, attempting summarization and chat reset...")
            return self._handle_rate_limit_error(result)

        success_flag = _parse_success_flag(check_success)

        if success_flag is None:
            logger.warning(f"Unable to determine task success from response: {check_success}")
            success_flag = False

        if success_flag:
            task_result = self.update_task_status(self.current_plan.id, self.current_plan.current_task_sequence,
                                                  True, True, result)
        else:
            task_result = self.update_task_status(self.current_plan.id, self.current_plan.current_task_sequence,
                                                  True, False, result)

        # 更新
        updated_response = (WritePlan(
            plan_chat_id=self.current_plan.plan_chat_id,
            target_host=self.target_host,
            user_instruction=self.init_description
        ).update(task_result,
                 self.current_plan.finished_success_tasks,
                 self.current_plan.finished_fail_tasks,
                 self.init_description))

        logger.info(f"updated_plan: {updated_response}")

        # Check if update response has rate limit error
        if updated_response and is_rate_limit_error(updated_response):
            logger.warning("Rate limit error in plan update, attempting recovery...")
            return self._handle_rate_limit_error(result)

        if not updated_response:
            logger.error("Plan update failed: empty or error response from LLM. Keeping existing tasks.")
            return self.next_task_details()

        try:
            merge_tasks(updated_response, self.current_plan)
        except Exception as e:
            logger.error(f"Failed to merge updated plan: {e}")
            return self.next_task_details()

        next_task = self.next_task_details()

        return next_task

    def next_task_details(self):
        logger.info(f"current_task: {self.current_plan.current_task}")
        if self.current_plan.current_task is None:
            return None

        self.current_plan.current_task_sequence = self.current_plan.current_task.sequence
        
        # Create a more explicit prompt that focuses only on the current task
        current_task_instruction = self.current_plan.current_task.instruction
        
        # Use a task-specific conversation ID to avoid cross-contamination
        # Keep it short to fit in the conversation_id column (32 chars max)
        task_suffix = f"t{self.current_plan.current_task_sequence}"
        base_id = self.current_plan.react_chat_id
        
        # If the combined ID would be too long, create a shorter hash-based ID
        if len(base_id) + len(task_suffix) + 1 > 32:
            # Create a hash of the original ID and append task suffix
            hash_base = hashlib.md5(base_id.encode()).hexdigest()[:20]
            task_conversation_id = f"{hash_base}_{task_suffix}"
        else:
            task_conversation_id = f"{base_id}_{task_suffix}"
        
        next_task = _chat(
            query=DeepPentestPrompt.next_task_details.format(
                todo_task=current_task_instruction,
                user_instruction=self.init_description
            ),
            conversation_id=task_conversation_id,
            kb_name=Configs.kb_config.kb_name,
            kb_query=current_task_instruction
        )
        return next_task

    def update_task_status(self, plan_id: str, task_sequence: int,
                           is_finished: bool, is_success: bool, result: Optional[str] = None) -> Task:
        """更新任务状态"""

        task = next((
            task for task in self.current_plan.tasks
            if task.plan_id == plan_id and task.sequence == task_sequence
        ), None)

        if task:
            task.is_finished = is_finished
            task.is_success = is_success
            if result:
                task.result = result

        # 返回更新后的计划
        return task

    def _handle_rate_limit_error(self, result: str):
        """
        Handle rate limit errors by summarizing content and resetting chat context.
        
        Args:
            result: The command result that caused the token limit issue
        
        Returns:
            Next task details with clean context
        """
        try:
            logger.info("Handling rate limit error with summarization and chat reset...")
            
            # Summarize the problematic result
            summary = ContentSummarizer.summarize_content(
                content=result,
                conversation_id=f"{self.current_plan.react_chat_id}_emergency",
                context="Emergency summarization due to token limits"
            )
            
            # Get current task for context
            current_task = self.current_plan.tasks[self.current_plan.current_task_sequence] if self.current_plan.tasks else None
            current_task_desc = current_task.instruction if current_task else "Continue penetration testing"
            
            # Create clean context
            clean_context = ContentSummarizer.create_clean_chat_context(
                user_description=self.init_description,
                system_prompt="You are a penetration testing expert assistant. Continue with the planned tasks.",
                summary=summary,
                current_task=current_task_desc
            )
            
            # Reset conversation with clean context
            response, new_conversation_id = reset_conversation_with_context(
                self.current_plan.react_chat_id,
                clean_context
            )
            
            # Update chat IDs
            self.current_plan.react_chat_id = new_conversation_id
            self.current_plan.plan_chat_id = f"{new_conversation_id}_plan"
            
            logger.info("Successfully reset chat context due to rate limit")
            
            # Mark current task as completed with summary
            if current_task:
                self.update_task_status(
                    self.current_plan.id,
                    self.current_plan.current_task_sequence,
                    True,
                    True,
                    f"Task completed. Summary: {summary[:500]}..."
                )
            
            # Return next task details
            return self.next_task_details()
            
        except Exception as e:
            logger.error(f"Failed to handle rate limit error: {e}")
            # Fallback: just continue with next task
            return self.next_task_details()
