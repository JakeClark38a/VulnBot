#!/usr/bin/env python3
"""
Test the conversation ID length fix
"""

import hashlib

def test_conversation_id_generation():
    """Test the new conversation ID generation logic"""
    
    # Simulate the original conversation ID (32 char hex)
    original_id = "a8d141aaa0524f3f9ce7d44efc1b9499"
    task_sequence = 0
    
    print(f"Original conversation ID: {original_id} (length: {len(original_id)})")
    
    # Test the new logic
    task_suffix = f"t{task_sequence}"
    base_id = original_id
    
    print(f"Task suffix: {task_suffix}")
    print(f"Combined length would be: {len(base_id) + len(task_suffix) + 1}")
    
    if len(base_id) + len(task_suffix) + 1 > 32:
        # Create a hash of the original ID and append task suffix
        hash_base = hashlib.md5(base_id.encode()).hexdigest()[:20]
        task_conversation_id = f"{hash_base}_{task_suffix}"
        print(f"Using hash-based ID: {task_conversation_id} (length: {len(task_conversation_id)})")
    else:
        task_conversation_id = f"{base_id}_{task_suffix}"
        print(f"Using direct ID: {task_conversation_id} (length: {len(task_conversation_id)})")
    
    # Test with different task sequences
    for seq in [0, 1, 10, 999]:
        task_suffix = f"t{seq}"
        if len(base_id) + len(task_suffix) + 1 > 32:
            hash_base = hashlib.md5(base_id.encode()).hexdigest()[:20]
            task_conversation_id = f"{hash_base}_{task_suffix}"
        else:
            task_conversation_id = f"{base_id}_{task_suffix}"
        
        print(f"Task {seq}: {task_conversation_id} (length: {len(task_conversation_id)})")
        
        if len(task_conversation_id) > 32:
            print(f"ERROR: ID too long! {len(task_conversation_id)} > 32")

if __name__ == "__main__":
    test_conversation_id_generation()
