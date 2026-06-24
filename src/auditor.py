import json
import logging
import hashlib
from datetime import datetime
import psycopg2
from psycopg2.pool import SimpleConnectionPool

class Auditor:
    def __init__(self, dsn: str = "postgresql://postgres:postgres@localhost:5433/audit"):
        self.logger = logging.getLogger("Auditor")
        self.pool = SimpleConnectionPool(1, 20, dsn)
        self._init_db()

    def _init_db(self):
        conn = self.pool.getconn()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS audit_log (
                        line_number SERIAL PRIMARY KEY,
                        ts TIMESTAMP NOT NULL,
                        event VARCHAR(50) NOT NULL,
                        agent_id VARCHAR(255),
                        request_id VARCHAR(255),
                        prev_hash VARCHAR(64) NOT NULL,
                        hash VARCHAR(64) NOT NULL,
                        data JSONB NOT NULL
                    )
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS hash_state (
                        id INTEGER PRIMARY KEY CHECK (id = 1),
                        last_hash VARCHAR(64) NOT NULL,
                        line_count INTEGER NOT NULL
                    )
                """)
                cursor.execute("SELECT id FROM hash_state WHERE id=1")
                if not cursor.fetchone():
                    cursor.execute(
                        "INSERT INTO hash_state (id, last_hash, line_count) VALUES (1, %s, 0)",
                        ("0" * 64,)
                    )
            conn.commit()
        except Exception as e:
            conn.rollback()
            self.logger.critical(f"Failed to initialize database: {e}")
            raise
        finally:
            self.pool.putconn(conn)

    def _compute_hash(self, entry: dict, prev_hash: str) -> str:
        entry_copy = {k: v for k, v in entry.items() if k != "hash"}
        content = json.dumps(entry_copy, sort_keys=True) + prev_hash
        return hashlib.sha256(content.encode()).hexdigest()

    def _log_phase(self, event_type: str, data: dict):
        conn = None
        for attempt in range(3):
            try:
                conn = self.pool.getconn()
                break
            except psycopg2.pool.PoolError:
                if attempt < 2:
                    import time
                    time.sleep((2 ** attempt) * 0.1)
                else:
                    raise Exception("Database pool exhausted after 3 retries")

        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT last_hash, line_count FROM hash_state WHERE id=1 FOR UPDATE")
                row = cursor.fetchone()
                prev_hash, line_count = row

                entry = {
                    "ts": datetime.utcnow().isoformat(),
                    "event": event_type,
                    **data
                }
                
                entry["prev_hash"] = prev_hash
                entry["hash"] = self._compute_hash(entry, prev_hash)
                entry["line_number"] = line_count + 1

                cursor.execute(
                    """INSERT INTO audit_log 
                       (line_number, ts, event, agent_id, request_id, prev_hash, hash, data)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                    (entry["line_number"], entry["ts"], event_type,
                     data.get("agent_id"), data.get("request_id"),
                     entry["prev_hash"], entry["hash"], json.dumps(data))
                )

                cursor.execute(
                    "UPDATE hash_state SET last_hash=%s, line_count=%s WHERE id=1",
                    (entry["hash"], line_count + 1)
                )
            conn.commit()
        except Exception as e:
            conn.rollback()
            self.logger.critical(f"Audit log transaction failed: {e}")
            raise
        finally:
            if conn:
                self.pool.putconn(conn)

    def pre_log_intent(self, agent_id, request_id, family_id, amount, prev_balance):
        self._log_phase("INTENT", {"agent_id": agent_id, "request_id": request_id, "family_id": family_id, "amount": amount, "prev_balance": prev_balance})

    def update_intent_success(self, request_id, prev_balance, amount, new_balance):
        self._log_phase("SUCCESS", {"request_id": request_id, "prev_balance": prev_balance, "amount": amount, "new_balance": new_balance})

    def update_intent_insufficient(self, request_id, prev_balance, amount, new_balance):
        self._log_phase("INSUFFICIENT_FUNDS", {"request_id": request_id, "prev_balance": prev_balance, "amount": amount, "new_balance": new_balance})

    def update_intent_failed(self, request_id, error):
        self._log_phase("FAILURE", {"request_id": request_id, "error": error})
