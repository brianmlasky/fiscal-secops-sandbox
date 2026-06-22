import redis
from src.controller.governance_controller import FiscalGovernanceController

# 1. Connect to local Redis
client = redis.Redis(host='localhost', port=6379, decode_responses=True)

# 2. Instantiate Controller
controller = FiscalGovernanceController(client)

# 3. Setup a dummy budget
client.set("budget:dr-architect", 5000)

# 4. Perform a test deduction
new_balance = controller.deduct("dr-architect", 100)
print(f"New Balance: {new_balance}")
