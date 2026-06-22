import json
import subprocess
import sys

def get_task_config(task_name):
    with open('registry.json', 'r') as f:
        registry = json.load(f)
    return registry['tasks'].get(task_name, registry['tasks']['default'])

def dispatch_task(task_name, prompt):
    config = get_task_config(task_name)
    workload_id = config['workload']
    
    print(f"[#] Dispatching Task: {task_name}")
    print(f"[#] Routing to Workload: {workload_id}")
    
    # HITL Checkpoint
    if config.get("human_in_the_loop", False):
        print(f"\n[!] SECURITY ALERT: Task '{task_name}' requires human approval.")
        confirm = input("Approve execution? (y/n): ")
        if confirm.lower() != 'y':
            print("[#] Task aborted by user.")
            return

    # Trigger the controller
    subprocess.run(["python", "main.py", workload_id, prompt])

if __name__ == "__main__":
    task = sys.argv[1] if len(sys.argv) > 1 else "default"
    user_prompt = sys.argv[2] if len(sys.argv) > 2 else "Perform a general system health check."
    dispatch_task(task, user_prompt)
