import json
import re
from typing import List, Dict, Optional

from pydantic import BaseModel

from config.config import Configs
from prompts.prompt import DeepPentestPrompt
from db.models.plan_model import Plan
from db.models.task_model import TaskModel, Task
from server.chat.chat import _chat, is_rate_limit_error
from actions.content_summarizer import ContentSummarizer


class WritePlan(BaseModel):
    plan_chat_id: str
    target_host: str = "target"
    user_instruction: str = ""

    def _extract_json_block(self, rsp: str) -> Optional[str]:
        """Extract JSON payload wrapped in <json> tags if present.
        Returns the inner JSON string or None if not found or rsp empty/error.
        """
        if not rsp:
            return None
        # Propagate upstream LLM / transport errors (they start with **ERROR**)
        if rsp.strip().startswith("**ERROR**"):
            return None
        match = re.search(r'<json>(.*?)</json>', rsp, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        # Fallback: try to find the first JSON array in the text
        fallback = re.search(r'(\[\s*{.*}\s*\])', rsp, re.DOTALL)
        if fallback:
            return fallback.group(1).strip()
        return None

    def run(self, init_description) -> Optional[str]:
        prompt_text = (DeepPentestPrompt.write_plan
                       .replace("{target_host}", self.target_host)
                       .replace("{user_instruction}", self.user_instruction or init_description))
        rsp = _chat(query=prompt_text,
                    conversation_id=self.plan_chat_id,
                    kb_name=Configs.kb_config.kb_name,
                    kb_query=init_description)
        return self._extract_json_block(rsp)

    def update(self, task_result, success_task, fail_task, init_description) -> Optional[str]:
        # Check if any content needs summarization
        content_to_check = f"{task_result.result}{str(success_task)}{str(fail_task)}"
        
        if ContentSummarizer.needs_summarization(content_to_check):
            # Summarize the task result if too long
            if ContentSummarizer.needs_summarization(task_result.result):
                task_result.result = ContentSummarizer.summarize_content(
                    content=task_result.result,
                    conversation_id=f"{self.plan_chat_id}_update",
                    context=f"Task result for: {task_result.instruction}"
                )
        
        prompt_text = DeepPentestPrompt.update_plan.format(
            current_task=task_result.instruction,
            init_description=init_description,
            current_code=task_result.code,
            task_result=task_result.result,
            success_task=success_task,
            fail_task=fail_task,
            user_instruction=self.user_instruction or init_description,
            target_host=self.target_host
        )

        rsp = _chat(
            query=prompt_text,
            conversation_id=self.plan_chat_id,
            kb_name=Configs.kb_config.kb_name,
            kb_query=task_result.instruction
        )
        
        # Check for rate limit error in response
        if rsp and is_rate_limit_error(rsp):
            # Attempt one more time with heavily summarized content
            short_result = task_result.result[:500] + "..." if len(task_result.result) > 500 else task_result.result
            retry_prompt = DeepPentestPrompt.update_plan.format(
                current_task=task_result.instruction,
                init_description=init_description[:300],
                current_code=str(task_result.code)[:200],
                task_result=short_result,
                success_task=str(success_task)[:200],
                fail_task=str(fail_task)[:200],
                user_instruction=self.user_instruction or init_description,
                target_host=self.target_host
            )

            rsp = _chat(
                query=retry_prompt,
                conversation_id=f"{self.plan_chat_id}_retry",
                kb_name=Configs.kb_config.kb_name,
                kb_query=task_result.instruction[:100]
            )
        
        return self._extract_json_block(rsp)


def parse_tasks(response: Optional[str], current_plan: Plan):
    if not response:
        raise ValueError("Empty plan response: LLM returned no JSON (upstream error or offline endpoint).")
    try:
        response_json = json.loads(response)
    except Exception as e:
        # Attempt to clean common escape issues then retry once
        cleaned = preprocess_json_string(response)
        if cleaned != response:
            try:
                response_json = json.loads(cleaned)
            except Exception:
                raise ValueError(f"Failed to parse plan JSON after cleanup: {e}. Snippet: {response[:200]}")
        else:
            raise ValueError(f"Failed to parse plan JSON: {e}. Snippet: {response[:200]}")

    tasks = import_tasks_from_json(current_plan.id, response_json)
    current_plan.tasks = tasks
    return current_plan

def preprocess_json_string(json_str):
     # Use a regular expression to find invalid escape sequences
    json_str = re.sub(r'\\([@!])', r'\\\\\1', json_str)

    return json_str

def merge_tasks(response: Optional[str], current_plan: Plan):
    if not response:
        # Nothing to merge (likely upstream error). Keep existing tasks.
        return current_plan
    processed_response = preprocess_json_string(response)
    try:
        response_json = json.loads(processed_response)
    except Exception as e:
        raise ValueError(f"Failed to parse updated plan JSON: {e}. Snippet: {response[:200]}")

    tasks = merge_tasks_from_json(current_plan.id, response_json, current_plan.tasks)
    current_plan.tasks = tasks
    return current_plan


def import_tasks_from_json(plan_id: str, tasks_json: List[Dict]) -> List[TaskModel]:
    tasks = []
    for idx, task_data in enumerate(tasks_json):
        task = Task(
            plan_id=plan_id,
            sequence=idx,
            action=task_data['action'],
            instruction=task_data['instruction'],
            dependencies=[i for i, t in enumerate(tasks_json)
                          if t['id'] in task_data['dependent_task_ids']]
        )

        tasks.append(task)
    return tasks


def merge_tasks_from_json(plan_id: str, new_tasks_json: List[Dict], old_tasks: List[Task]) -> List[Task]:
    # Get all completed and successful tasks
    completed_tasks_map = {
        task.instruction: task
        for task in old_tasks
        if task.is_finished and task.is_success
    }

    merged_tasks = []

    for instruction, completed_task in completed_tasks_map.items():
        found = False
        for task_data in new_tasks_json:
            if task_data['instruction'] == instruction:
                found = True
                break
        if not found:
            completed_task.sequence = len(merged_tasks)
            completed_task.dependencies = []
            merged_tasks.append(completed_task)

    new_task_id_to_idx = {
        task_data.get('id'): idx+len(merged_tasks)
        for idx, task_data in enumerate(new_tasks_json)
    }
    for idx, task_data in enumerate(new_tasks_json):
        instruction = task_data['instruction']
        sequence = len(merged_tasks)

        if instruction in completed_tasks_map:
            existing_task = completed_tasks_map[instruction]
            existing_task.sequence = sequence
            existing_task.dependencies = [
                new_task_id_to_idx[dep_id]
                for dep_id in task_data['dependent_task_ids']
                if dep_id in new_task_id_to_idx
            ]
            merged_tasks.append(existing_task)
        else:
            new_task = Task(
                plan_id=plan_id,
                sequence=sequence,
                action=task_data['action'],
                instruction=task_data['instruction'],
                dependencies=[
                    new_task_id_to_idx[dep_id]
                    for dep_id in task_data['dependent_task_ids']
                    if dep_id in new_task_id_to_idx
                ],
            )
            merged_tasks.append(new_task)

    return merged_tasks