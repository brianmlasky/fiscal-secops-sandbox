import redis
import os
from src.auditor import Auditor
from src.controller.governance_controller import FiscalGovernanceController

# 1. Setup
client = redis.Redis(host='localhost', port=6379, decode_responses=True)
audit_file = "audit_log.json"
if os.path.exists(audit_file): os.remove(audit_file) # Clear old logs

auditor = Auditor(log_path=audit_file)
controller = FiscalGovernanceController(client, auditor)

# 2. Setup dummy budget
client.set("budget:dr-architect", 1000)

# 3. Perform a deduction
controller.deduct("dr-architect", 150)

# 4. Verify Audit Log
with open(audit_file, "r") as f:
    log_data = f.read()
    print(f"--- Audit Log Entry ---\n{log_data}")
    print("--- Integration Test Complete ---")
