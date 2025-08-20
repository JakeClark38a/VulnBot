#!/usr/bin/env python3
"""
Debug tool for testing VulnBot task execution flow

This tool helps debug the issue where the wrong task is being executed
by testing the planner -> write_code -> execute flow.
"""

import sys
import os

# Add VulnBot to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_task_execution_flow():
    """Test the task execution flow to identify where task mismatch occurs"""
    
    try:
        from actions.planner import Planner
        from actions.write_code import WriteCode
        from db.models.plan_model import Plan
        from db.models.task_model import Task
        
        print("=== Testing Task Execution Flow ===\n")
        
        # Create a mock task for testing
        test_task = Task(
            plan_id="test_plan",
            sequence=1,
            action="Shell",
            instruction="Install Tavily search tool to enable vulnerability lookup for the identified stack (Uvicorn, Gradio 4.12.0).",
            code=[],
            result="",
            is_success=False,
            is_finished=False,
            dependencies=[]
        )
        
        print(f"Original Task Instruction: {test_task.instruction}")
        print(f"Task Action: {test_task.action}")
        print()
        
        # Create a mock plan with the test task
        test_plan = Plan(
            id="test_plan_id",
            goal="Test Tavily installation",
            current_task_sequence=1,
            plan_chat_id="test_chat_plan",
            react_chat_id="test_chat_react",
            tasks=[test_task]
        )
        
        # Test the planner next_task_details method
        print("=== Testing Planner.next_task_details() ===")
        planner = Planner(current_plan=test_plan, init_description="Test")
        
        try:
            next_task_details = planner.next_task_details()
            print(f"Next Task Details Output: {next_task_details}")
            print()
            
            # Test the WriteCode with the output
            print("=== Testing WriteCode.run() ===")
            writer = WriteCode(next_task=next_task_details, action=test_task.action)
            
            # This would normally call the LLM, but we'll simulate to avoid actual execution
            print(f"WriteCode input next_task: {writer.next_task}")
            print(f"WriteCode action: {writer.action}")
            
            # Note: Actual run() would call LLM and execute - we'll just show the inputs
            print("\n✓ Task flow tested - check if next_task_details matches original task")
            
        except Exception as e:
            print(f"Error in planner flow: {e}")
            
    except ImportError as e:
        print(f"Import error: {e}")
        print("Make sure dependencies are installed and paths are correct")
    except Exception as e:
        print(f"Unexpected error: {e}")

def test_prompt_isolation():
    """Test if conversation isolation is working"""
    print("\n=== Testing Prompt Isolation ===")
    
    try:
        from server.chat.chat import _chat
        from prompts.prompt import DeepPentestPrompt
        
        # Test with fresh conversation
        test_task = "Install Tavily search tool to enable vulnerability lookup"
        
        print("Testing with conversation_id=None (fresh conversation):")
        response, conv_id = _chat(
            query=DeepPentestPrompt.write_code.format(next_task=test_task),
            conversation_id=None,
            summary=False
        )
        
        print(f"Response: {response[:200]}...")
        print(f"New conversation ID: {conv_id}")
        
    except Exception as e:
        print(f"Error testing prompt isolation: {e}")

def main():
    """Run all debug tests"""
    print("VulnBot Task Execution Debug Tool")
    print("=" * 50)
    
    test_task_execution_flow()
    test_prompt_isolation()
    
    print("\n" + "=" * 50)
    print("Debug complete. Check outputs above for task flow integrity.")

if __name__ == "__main__":
    main()
