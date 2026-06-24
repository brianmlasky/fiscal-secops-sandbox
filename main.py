"""
Serverless Agentic Governance Controller - Production Ready
-----------------------------------------------------------
Identity Agnostic: Relies on GOOGLE_APPLICATION_CREDENTIALS environment variable.
Dynamically enforces budgets via policy.json.
Logs telemetry to audit_log.json.
"""

import json
import sys
import datetime
from google import genai
from google.genai import types

# Initialize client using automatic credential discovery.
client = genai.Client(vertexai=True)

def load_policy(workload_name="default"):
    """Reads the policy.json file to extract the fiscal guardrails."""
    try:
        with open("policy.json", "r") as f:
            policy = json.load(f)
        workloads = policy.get("workloads", {})
        return workloads.get(workload_name, workloads.get("default", {"budget": 150, "model": "gemini-3.5-flash"}))
    except (FileNotFoundError, json.JSONDecodeError):
        # Fail-closed default if policy is missing or corrupted
        return {"budget": 150, "model": "gemini-3.5-flash"}

def run_governed_agent(prompt_text, workload_name="default"):
    """Executes the agent call governed by the policy-defined budget."""
    # 1. Evaluate Policy-as-Code
    profile = load_policy(workload_name)
    budget = profile.get("budget", 150)
    target_model = profile.get("model", "gemini-3.5-flash")
    
    # 2. Establish the fiscal guardrail dynamically
    config = types.GenerateContentConfig(
        max_output_tokens=budget,  
        temperature=0.2,        
    )
    
    print(f"[+] Routing workload '{workload_name}' with a strictly enforced {budget}-token fiscal guardrail...")
    print(f"[+] Sending prompt to {target_model} using ADC identity...\n")

    response = client.models.generate_content(
        model=target_model, 
        contents=prompt_text,
        config=config
    )
    
    # 3. Infrastructure Governor Diagnostic
    candidate = response.candidates[0] if response.candidates else None
    if candidate and candidate.finish_reason.name == 'MAX_TOKENS':
        print("[!] INFRASTRUCTURE GOVERNOR TRIGGERED: Agent hit budget limit.\n")
    
    # 4. Parse output
    try:
        print(f"--- Agent Response ---\n{response.text}\n")
    except ValueError:
        print("--- Agent Response ---\n[Payload cut off by governor]\n")
    
    # 5. FinOps Hook: Telemetry Audit & Logging
    if response.usage_metadata:
        usage = response.usage_metadata
        print(f"--- Fiscal Audit ---")
        print(f"Total Tokens: {usage.total_token_count} (Thoughts: {usage.thoughts_token_count})")
        
        # Telemetry Logging
        log_entry = {
            "workload": workload_name,
            "total_tokens": usage.total_token_count,
            "thought_tokens": usage.thoughts_token_count,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        with open('audit_log.json', 'a') as f:
            f.write(json.dumps(log_entry) + '\n')

if __name__ == "__main__":
    # Allows passing the workload name via terminal (e.g., `python main.py dr-architect`)
    target_workload = sys.argv[1] if len(sys.argv) > 1 else "dr-architect"
    
    run_governed_agent(
        prompt_text="Explain why an active-passive DR topology is safer than an active-active one.", 
        workload_name=target_workload
    )