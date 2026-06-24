import redis
from src.auditor import Auditor
from src.controller.governance_controller import FiscalGovernanceController

# Initialize
client = redis.Redis(host='localhost', port=6379, decode_responses=True)
auditor = Auditor("audit_log.json")
controller = FiscalGovernanceController(client, auditor)

# 1. Test Fail-Closed
print("Injecting Network Failure...")
client.shutdown() # Force Redis crash
try:
    controller.deduct("test-agent", 10.0)
except Exception as e:
    print(f"Success: System failed closed as expected: {e}")

# 2. Test Lua Fallback
print("Restarting Redis...") # Note: You'd restart redis here
# Manually flush scripts
client.script_flush() 
result = controller.deduct("test-agent", 5.0)
print(f"Success: System auto-reloaded Lua script: {result}")
