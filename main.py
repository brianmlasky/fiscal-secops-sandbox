import json
from google import genai
from google.genai import types

# Initialize client using the authenticated Application Default Credentials (ADC)
client = genai.Client(
    vertexai=True, 
    project="project-3be8586c-e3f9-4cbc-909", 
    location="global"
)

def load_policy(workload_name="default"):
    """Reads the policy.json file to extract the fiscal guardrails."""
    with open("policy.json", "r") as f:
        policy = json.load(f)
    
    # Fallback to default if workload doesn't exist in policy
    workloads = policy.get("workloads", {})
    return workloads.get(workload_name, workloads.get("default"))

def run_governed_agent(prompt_text, workload_name="default"):
    # 1. Evaluate Policy-as-Code
    profile = load_policy(workload_name)
    budget = profile["budget"]
    target_model = profile["model"]
    
    # 2. Establish the fiscal guardrail dynamically
    config = types.GenerateContentConfig(
        max_output_tokens=budget,  
        temperature=0.2,        
    )
    
    print(f"[+] Assuming Workload Profile: '{workload_name}'")
    print(f"[+] Sending prompt to {target_model} with a strictly enforced {budget}-token budget using ADC identity...")
    
    response = client.models.generate_content(
        model=target_model, 
        contents=prompt_text,
        config=config
    )
    
    # Diagnostic Hook: Detect if the infrastructure governor killed the process
    candidate = response.candidates[0] if response.candidates else None
    if candidate and candidate.finish_reason.name == 'MAX_TOKENS':
        print("\n[!] INFRASTRUCTURE GOVERNOR TRIGGERED: Agent hit budget limit before completing.")
    
    # Attempt to parse the text output
    try:
        print(f"\n--- Agent Response ---\n{response.text}")
    except ValueError:
        print("\n--- Agent Response ---\n[Payload cut off by governor - text parsing failed]")
    
    # FinOps Hook: Extract and audit the telemetry
    if response.usage_metadata:
        usage = response.usage_metadata
        print("\n--- Fiscal Audit ---")
        print(f"Prompt Tokens: {usage.prompt_token_count}")
        print(f"Thought Tokens: {usage.thoughts_token_count}")
        print(f"Response Tokens: {usage.candidates_token_count}")
        print(f"Total Tokens: {usage.total_token_count}")

if __name__ == "__main__":
    # Passing the specific workload profile defined in policy.json
    run_governed_agent("Explain why an active-passive DR topology is safer than an active-active one.", workload_name="dr-architect")
