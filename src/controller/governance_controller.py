import redis
import logging
from src.auditor import Auditor

class FiscalGovernanceController:
    def __init__(self, redis_client: redis.Redis, auditor: Auditor, fail_closed: bool = True):
        self.redis = redis_client
        self.auditor = auditor  # Injected Audit Plane
        self.fail_closed = fail_closed
        self.logger = logging.getLogger("FiscalGovernance")
        self._script_sha = self._load_lua_script()

    def _load_lua_script(self):
        """Loads the Lua script into Redis memory."""
        with open("src/lua/deduct.lua", "r") as f:
            script = f.read()
        return self.redis.script_load(script)

    def deduct(self, agent_id: str, amount: float) -> float:
        """Entry point that handles circuit breaking, logic, and audit logging."""
        # 1. Health check (Circuit Breaker)
        try:
            self.redis.ping()
        except redis.ConnectionError:
            self.logger.error("Governance Plane Unreachable.")
            if self.fail_closed:
                raise Exception("Governance Plane Down: Fail-Closed active")
            return -1.0

        # 2. Capture state before for audit trail
        prev_balance = float(self.redis.get(f"budget:{agent_id}") or 0)
        
        # 3. Execute atomic logic
        new_balance = self._execute_lua_deduction(agent_id, amount)
        
        # 4. Emit Audit Event
        event_type = "DEDUCT_SUCCESS" if new_balance >= 0 else "DEDUCT_FAILED"
        self.auditor.log_event(agent_id, event_type, prev_balance, amount, new_balance)
        
        return new_balance

    def _execute_lua_deduction(self, agent_id: str, amount: float) -> float:
        key = f"budget:{agent_id}"
        result = self.redis.evalsha(self._script_sha, 1, key, str(amount))
        return float(result)