"""
Serverless Agentic Governance Controller - Production Ready
-----------------------------------------------------------
Identity Agnostic: Relies on GOOGLE_APPLICATION_CREDENTIALS environment variable.
Dynamically enforces budgets via policy.json.
Logs telemetry to audit_log.json.
"""

import json
import sys
from google import genai
from google.genai import types

# Initialize client using automatic credential discovery.
# This respects the GOOGLE_APPLICATION_CREDENTIALS environment variable 
# if set, otherwise falls back to standard gcloud identity.
client = genai.Client(vertexai=True)

def get_budget_for_workload(workload_id):
    """Loads policy.json and returns the budget for a specific workload ID."""
    try:
        with open('policy.json', 'r') as f:
            policy = json.load(f)
        workload = policy['workloads'].get(workload_id, policy['workloads']['default'])
        return workload['budget']
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return 150

def run_governed_agent(workload_id, prompt_text):
    """Executes the agent call governed by the policy-defined budget."""
    budget = get_budget_for_workload(workload_id)
    
    config = types.GenerateContentConfig(
        max_output_tokens=budget,  
        temperature=0.2,        
    )
    
    print(f"[+] Routing workload '{workload_id}' with {budget}-token fiscal guardrail...")
    
    response = client.models.generate_content(
        model="gemini-3.5-flash", 
        contents=prompt_text,
        config=config
    )
    
    # 1. Infrastructure Governor Diagnostic
    candidate = response.candidates[0] if response.candidates else None
    if candidate and candidate.finish_reason.name == 'MAX_TOKENS':
        print("\n[!] INFRASTRUCTURE GOVERNOR TRIGGERED: Agent hit budget limit.")
    
    # 2. Parse output
    try:
        print(f"\n--- Agent Response ---\n{response.text}")
    except ValueError:
        print("\n--- Agent Response ---\n[Payload cut off by governor]")
    
    # 3. FinOps Hook: Telemetry Audit
    if response.usage_metadata:
        usage = response.usage_metadata
        print(f"\n--- Fiscal Audit ---")
        print(f"Total Tokens: {usage.total_token_count} (Thoughts: {usage.thoughts_token_count})")
        
        # 4. Telemetry Logging
        log_entry = {
            "workload": workload_id,
            "total_tokens": usage.total_token_count,
            "thought_tokens": usage.thoughts_token_count,
            "timestamp": response.create_time.isoformat()
        }
        with open('audit_log.json', 'a') as f:
            f.write(json.dumps(log_entry) + '\n')

if __name__ == "__main__":
    workload = sys.argv[1] if len(sys.argv) > 1 else "default"
    run_governed_agent(workload, "Explain why an active-passive DR topology is safer than an active-active one.")