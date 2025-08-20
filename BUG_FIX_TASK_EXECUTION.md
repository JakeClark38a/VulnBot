# VulnBot Task Execution Bug Fix

## Problem Description

The VulnBot was experiencing a serious bug where the LLM would generate commands for a different task than the one specified in the planner. Specifically:

- **Expected**: Install Tavily search tool (from planner task instruction)
- **Actual**: Generated nmap OS fingerprinting command
- **Root Cause**: Conversation context contamination between different task executions

## Log Evidence

```
2025-08-19 15:28:33.175 | INFO | actions.planner:next_task_details:80 - current_task: ... instruction='Install Tavily search tool to enable vulnerability lookup for the identified stack (Uvicorn, Gradio 4.12.0).' ...

2025-08-19 15:29:22.627 | INFO | actions.write_code:run:21 - LLM Response: <execute>nmap -O 10.0.2.5</execute>
```

## Root Cause Analysis

1. **Conversation Context Pollution**: The `_chat` function uses persistent conversation IDs that accumulate context from previous tasks
2. **Prompt Ambiguity**: The prompts didn't explicitly instruct the LLM to ignore previous conversation context
3. **Task Flow Issues**: Task details from `next_task_details()` were being contaminated by previous conversations

## Changes Made

### 1. Enhanced Prompt Specificity

**File**: `prompts/prompt.py`

- Added explicit instructions to focus ONLY on the current task
- Added warnings against referencing previous conversation context
- Made prompts more specific about task isolation

**Before**:
```python
write_code: str = """You play as an autonomous penetration testing assistant...
Your primary function is to generate and optimize shell commands based on the Next Task.
```

**After**:
```python
write_code: str = """You play as an autonomous penetration testing assistant...
CRITICAL: You must ONLY respond to the specific task described in the "Next Task" section below. 
Do NOT generate commands for any other tasks, regardless of previous conversation context.
```

### 2. Conversation Isolation

**File**: `actions/write_code.py`

- Modified to use fresh conversations (`conversation_id=None`) to prevent contamination
- Added explicit summary=False to avoid unwanted context persistence

**Before**:
```python
response, _ = _chat(query=DeepPentestPrompt.write_code.format(next_task=self.next_task))
```

**After**:
```python
response, _ = _chat(
    query=DeepPentestPrompt.write_code.format(next_task=self.next_task),
    conversation_id=None,  # Fresh conversation to avoid cross-contamination
    summary=False
)
```

### 3. Task-Specific Conversation IDs

**File**: `actions/planner.py`

- Implemented task-specific conversation IDs to prevent cross-task contamination
- Enhanced logging for better debugging

**Before**:
```python
next_task = _chat(
    query=DeepPentestPrompt.next_task_details.format(todo_task=self.current_plan.current_task.instruction),
    conversation_id=self.current_plan.react_chat_id,
    ...
)
```

**After**:
```python
# Use a task-specific conversation ID to avoid cross-contamination
task_conversation_id = f"{self.current_plan.react_chat_id}_task_{self.current_plan.current_task_sequence}"

next_task = _chat(
    query=DeepPentestPrompt.next_task_details.format(todo_task=current_task_instruction),
    conversation_id=task_conversation_id,
    ...
)
```

## Testing Tools Created

### 1. Debug Tool
**File**: `debug_task_flow.py`
- Tests the task execution flow from planner to write_code
- Verifies prompt isolation is working
- Helps identify where task mismatches occur

### 2. Tavily Integration Test
**File**: `test_tavily.py`
- Tests Tavily search functionality
- Validates configuration
- Provides integration verification

## Verification Steps

1. **Run Debug Tool**:
   ```bash
   python debug_task_flow.py
   ```

2. **Test Task Execution**:
   ```bash
   python pentest.py
   ```
   - Start a new session
   - Observe that tasks execute correctly without contamination

3. **Check Logs**:
   - Verify that `next_task_details` output matches the task instruction
   - Verify that `write_code` generates commands for the correct task

## Expected Behavior After Fix

- Each task should generate commands only for the specified instruction
- Previous task context should not contaminate new task execution
- Conversation IDs should be isolated per task or use fresh conversations
- LLM responses should directly correspond to the current task instruction

## Additional Safeguards

- Enhanced prompt engineering with explicit task isolation instructions
- Fresh conversation contexts for critical operations
- Task-specific conversation IDs for better isolation
- Improved logging for debugging task flow issues

## Impact

This fix ensures that VulnBot executes the correct tasks as planned, preventing:
- Execution of unrelated commands
- Security risks from unexpected command execution
- Workflow disruption due to task mismatch
- Confusion in penetration testing results
