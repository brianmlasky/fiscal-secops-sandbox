import json
import logging
from datetime import datetime
import uuid

class Auditor:
    def __init__(self, log_path: str = "audit_log.json"):
        self.log_path = log_path
        self.logger = logging.getLogger("Auditor")

    def log_event(self, agent_id: str, event_type: str, prev_balance: float, cost: float, new_balance: float, metadata: dict = None):
        """Constructs and persists an immutable audit entry."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": str(uuid.uuid4()),
            "agent_id": agent_id,
            "event_type": event_type,
            "prev_balance": prev_balance,
            "cost": cost,
            "new_balance": new_balance,
            "metadata": metadata or {}
        }
        
        # Persistence: For now, we append to a JSON file
        with open(self.log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")
            
        self.logger.info(f"Audit Logged: {event_type} for {agent_id}")