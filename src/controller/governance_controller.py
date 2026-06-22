import redis
import logging
import uuid
from src.auditor import Auditor

class FiscalGovernanceController:
    def __init__(self, redis_client: redis.Redis, auditor: Auditor, fail_closed: bool = True):
        self.redis = redis_client
        self.auditor = auditor
        self.fail_closed = fail_closed
        self.logger = logging.getLogger("FiscalGovernance")
        self._script_sha = self._load_lua_script()

    def _load_lua_script(self):
        with open("src/lua/deduct.lua", "r") as f:
            script = f.read()
        return self.redis.script_load(script)

    def deduct(self, agent_id: str, amount: float, request_id: str = None) -> float:
        if not request_id:
            request_id = str(uuid.uuid4())

        # 1. Health check
        try:
            self.redis.ping()
        except redis.ConnectionError:
            if self.fail_closed:
                raise Exception("Governance Plane Down: Fail-Closed active")
            return -1.0

        # 2. Pre-log INTENT (Atomic Record of Attempt)
        prev_balance = float(self.redis.get(f"budget:{agent_id}") or 0)
        self.auditor.log_intent(agent_id, request_id, amount, prev_balance)
        
        # 3. Execute atomic Lua logic (returns dict)
        try:
            result = self._execute_lua_deduction(agent_id, amount, request_id)
        except Exception as e:
            self.auditor.log_failure(agent_id, request_id, str(e))
            raise e
            
        # 4. Final outcome logging
        if result["was_success"]:
            self.auditor.log_success(agent_id, request_id, result)
        else:
            self.auditor.log_insufficient(agent_id, request_id, result)
            
        return result["new_balance"]

    def _execute_lua_deduction(self, agent_id: str, amount: float, request_id: str) -> dict:
        key = f"budget:{agent_id}"
        # Lua returns: [new_balance, prev_balance, was_success]
        raw = self.redis.evalsha(self._script_sha, 1, key, str(amount), request_id)
        return {
            "new_balance": float(raw[0]),
            "prev_balance": float(raw[1]),
            "was_success": bool(raw[2])
        }