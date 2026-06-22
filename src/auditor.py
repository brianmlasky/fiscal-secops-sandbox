import json
import logging
from datetime import datetime

class Auditor:
    def __init__(self, log_path: str = "audit_log.json"):
        self.log_path = log_path
        self.logger = logging.getLogger("Auditor")

    def _write_log(self, entry: dict):
        with open(self.log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def log_intent(self, agent_id, request_id, amount, prev_balance):
        self._write_log({"event": "INTENT", "agent_id": agent_id, "request_id": request_id, "amount": amount, "prev_balance": prev_balance, "ts": datetime.utcnow().isoformat()})

    def log_success(self, agent_id, request_id, result):
        self._write_log({"event": "SUCCESS", "agent_id": agent_id, "request_id": request_id, "new_balance": result["new_balance"], "ts": datetime.utcnow().isoformat()})

    def log_failure(self, agent_id, request_id, error):
        self._write_log({"event": "FAILURE", "agent_id": agent_id, "request_id": request_id, "error": error, "ts": datetime.utcnow().isoformat()})

    def log_insufficient(self, agent_id, request_id, result):
        self._write_log({"event": "INSUFFICIENT_FUNDS", "agent_id": agent_id, "request_id": request_id, "ts": datetime.utcnow().isoformat()})