import json
import redis

def reconcile(log_path, redis_client):
    ledger = {}
    with open(log_path, "r") as f:
        for line in f:
            try:
                entry = json.loads(line)
                agent = entry.get("agent_id")
                event = entry.get("event")
                if event == "INTENT":
                    ledger[agent] = entry.get("prev_balance", 0.0)
                elif event == "SUCCESS":
                    ledger[agent] -= entry.get("amount", 0.0)
            except json.JSONDecodeError: continue
    
    for agent, expected in ledger.items():
        actual = float(redis_client.get(f"budget:{agent}") or 0)
        print(f"Agent {agent}: Expected {expected}, Actual {actual}")
        assert abs(expected - actual) < 0.001, "Mismatch detected!"

client = redis.Redis(host='localhost', port=6379, decode_responses=True)
reconcile("audit_log.json", client)
