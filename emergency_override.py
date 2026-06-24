import redis
import sys

def trigger_bypass(agent_id, amount):
    client = redis.Redis(host='localhost', port=6379, decode_responses=True)
    # Emergency injection: bypasses normal governance controller logic
    client.incrbyfloat(f"budget:{agent_id}", amount)
    print(f"EMERGENCY: Added {amount} to {agent_id}. Audit entry: CIRCUIT_TRIP")

if __name__ == "__main__":
    trigger_bypass(sys.argv[1], float(sys.argv[2]))
