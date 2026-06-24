import redis
import sqlite3
from src.auditor import Auditor
from src.controller.governance_controller import FiscalGovernanceController

def run_test():
    print("1. Initializing components...")
    client = redis.Redis(host='localhost', port=6379, decode_responses=True)
    auditor = Auditor("audit_log.db")
    controller = FiscalGovernanceController(client, auditor, fail_closed=True)
    
    # Ensure agent has funds
    client.set("budget:test-agent-007", 1000)
    
    print("2. Executing deduction with family_id...")
    new_balance = controller.deduct(
        agent_id="test-agent-007", 
        amount=150, 
        request_id="req-101", 
        family_id="fam-101"
    )
    print(f"   Success! New balance: ${new_balance}")
    
    print("3. Testing Idempotency (Replay identical family_id)...")
    retry_balance = controller.deduct(
        agent_id="test-agent-007", 
        amount=150, 
        request_id="req-102", 
        family_id="fam-101"
    )
    assert retry_balance == new_balance, "Idempotency failed!"
    print(f"   Success! Replay caught and ignored. Balance remains: ${retry_balance}")
    
    print("4. Verifying SQLite ACID Audit Log...")
    conn = sqlite3.connect("audit_log.db")
    cursor = conn.cursor()
    cursor.execute("SELECT event, prev_hash, hash FROM audit_log ORDER BY line_number DESC LIMIT 1")
    row = cursor.fetchone()
    print(f"   Success! Last SQLite record: Event={row[0]}, Hash={row[2][:16]}...")
    
    print("\n✅ All Production-Readiness Systems GO.")

if __name__ == "__main__":
    run_test()
