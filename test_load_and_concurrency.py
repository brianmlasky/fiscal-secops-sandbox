import concurrent.futures
import time
import redis
import uuid
from src.auditor import Auditor
from src.controller.governance_controller import FiscalGovernanceController

def worker(controller, agent_id, amount, request_id, family_id):
    try:
        new_balance = controller.deduct(agent_id, amount, request_id, family_id)
        return {"status": "success", "balance": new_balance}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def run_stress_test():
    print("Initializing Stress Test...")
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    r.flushdb() # Clean slate
    
    auditor = Auditor("postgresql://postgres:postgres@localhost:5433/audit")
    controller = FiscalGovernanceController(r, auditor)
    
    agent_id = "stress-agent-999"
    r.set(f"budget:{agent_id}", 10000) # Give agent $10,000
    
    # 1. Test Concurrent Idempotency (Same Family ID, Multiple Threads)
    print("\n--- Test 1: Thundering Herd Idempotency ---")
    family_id = "identical-job-123"
    futures = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        for _ in range(50):
            req_id = str(uuid.uuid4())
            futures.append(executor.submit(worker, controller, agent_id, 100, req_id, family_id))
            
    results = [f.result() for f in concurrent.futures.as_completed(futures)]
    successes = len([r for r in results if r["status"] == "success"])
    final_balance = float(r.get(f"budget:{agent_id}"))
    
    print(f"Threads Completed: {len(results)}")
    print(f"Successful Returns: {successes}")
    print(f"Final Balance: ${final_balance} (Expected: $9900)")
    assert final_balance == 9900, "Idempotency Failed: Double Spend Detected!"
    
    # 2. Test Connection Pool Saturation
    print("\n--- Test 2: Connection Pool Saturation ---")
    futures = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        for i in range(50):
            # Unique family IDs = 50 actual deductions
            req_id = str(uuid.uuid4())
            fam_id = f"unique-job-{i}"
            futures.append(executor.submit(worker, controller, agent_id, 10, req_id, fam_id))
            
    results = [f.result() for f in concurrent.futures.as_completed(futures)]
    successes = len([r for r in results if r["status"] == "success"])
    final_balance = float(r.get(f"budget:{agent_id}"))
    
    print(f"Threads Completed: {len(results)}")
    print(f"Successful Returns: {successes}")
    print(f"Final Balance: ${final_balance} (Expected: $9400)")
    assert final_balance == 9400, "Saturation Failed: Connection Pool Dropped Transactions!"
    
    print("\n✅ All Load & Concurrency Tests Passed! Production Evidence Generated.")

if __name__ == "__main__":
    run_stress_test()
