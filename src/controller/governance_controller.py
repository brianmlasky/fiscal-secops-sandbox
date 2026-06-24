import redis
import logging
import uuid
import time
import threading
from prometheus_client import Counter, Histogram
from src.auditor import Auditor
from src.exceptions import GovernancePlaneError, InsufficientFundsError

class ScalableMetrics:
    def __init__(self):
        self.deduct_attempts = Counter('deduct_attempts_total', 'Total deductions', ['agent_id', 'status'])
        self.deduct_latency = Histogram('deduct_duration_seconds', 'Deduction latency', ['status'])
        self.redis_latency = Histogram('redis_operation_duration_seconds', 'Redis latency', ['operation'])

    def record_deduction(self, agent_id: str, status: str, duration: float):
        self.deduct_attempts.labels(agent_id=agent_id, status=status).inc()
        self.deduct_latency.labels(status=status).observe(duration)

    def record_redis_op(self, operation: str, duration: float):
        self.redis_latency.labels(operation=operation).observe(duration)

class RateLimiter:
    def __init__(self, max_per_second=100, cleanup_interval=3600):
        self.max_per_second = max_per_second
        self.cleanup_interval = cleanup_interval
        self.buckets = {}
        self._cleanup_lock = threading.Lock()
        self.logger = logging.getLogger("RateLimiter")
        self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._cleanup_thread.start()
    
    def _cleanup_loop(self):
        while True:
            try:
                time.sleep(self.cleanup_interval)
                self._async_cleanup()
            except Exception as e:
                self.logger.error(f"Cleanup error: {e}")
    
    def _async_cleanup(self):
        with self._cleanup_lock:
            now = time.time()
            stale_threshold = 86400
            to_delete = [aid for aid, b in self.buckets.items() if now - b["last_refill"] > stale_threshold]
            for aid in to_delete:
                del self.buckets[aid]

    def is_limited(self, agent_id: str) -> bool:
        now = time.time()
        if agent_id not in self.buckets:
            with self._cleanup_lock:
                if agent_id not in self.buckets:
                    self.buckets[agent_id] = {"tokens": self.max_per_second, "last_refill": now}
            return False
        
        bucket = self.buckets[agent_id]
        elapsed = now - bucket["last_refill"]
        bucket["tokens"] = min(self.max_per_second, bucket["tokens"] + (elapsed * self.max_per_second))
        bucket["last_refill"] = now
        
        if bucket["tokens"] >= 1.0:
            bucket["tokens"] -= 1.0
            return False
        return True

class FiscalGovernanceController:
    def __init__(self, redis_client: redis.Redis, auditor: Auditor, fail_closed: bool = True):
        self.redis = redis_client
        self.auditor = auditor
        self.fail_closed = fail_closed
        self.logger = logging.getLogger("FiscalGovernance")
        self._rate_limiter = RateLimiter(max_per_second=100)
        self._metrics = ScalableMetrics()
        self._script_sha = None
        self._script_body = None
        self._load_lua_script()

    def _load_lua_script(self):
        with open("src/lua/deduct.lua", "r") as f:
            self._script_body = f.read()
        try:
            self._script_sha = self.redis.script_load(self._script_body)
        except redis.ConnectionError:
            self.logger.warning("Redis unavailable; will retry.")

    def deduct(self, agent_id: str, amount: float, request_id: str = None, family_id: str = None) -> float:
        start_time = time.time()
        status = "success"
        
        try:
            if not isinstance(amount, (int, float)) or amount <= 0:
                raise ValueError(f"Amount must be positive; got {amount}")
                
            if self._rate_limiter.is_limited(agent_id):
                status = "rate_limited"
                raise GovernancePlaneError(f"Rate limit exceeded for {agent_id}")
                
            if not request_id: request_id = str(uuid.uuid4())
            if not family_id: raise ValueError("family_id is required")

            redis_start = time.time()
            prev_balance_str = self.redis.get(f"budget:{agent_id}")
            prev_balance = float(prev_balance_str) if prev_balance_str else 0.0
            self._metrics.record_redis_op("get_balance", time.time() - redis_start)

            audit_logged = False
            audit_error = None
            for retry in range(3):
                try:
                    self.auditor.pre_log_intent(agent_id, request_id, family_id, amount, prev_balance)
                    audit_logged = True
                    break
                except Exception as e:
                    audit_error = e
                    if retry < 2:
                        time.sleep((2 ** retry) * 0.1)
                        
            if not audit_logged:
                status = "failure"
                raise GovernancePlaneError(f"Cannot write to audit log: {audit_error}")

            try:
                result = self._execute_lua_deduction(agent_id, amount, request_id, family_id)
            except Exception as e:
                status = "failure"
                self.auditor.update_intent_failed(request_id, str(e))
                raise GovernancePlaneError(f"Deduction failed: {e}")

            new_balance = result["new_balance"]

            if not result["was_success"]:
                status = "insufficient_funds"
                self.auditor.update_intent_insufficient(request_id, prev_balance, amount, new_balance)
                raise InsufficientFundsError("Insufficient funds")
                
            self.auditor.update_intent_success(request_id, prev_balance, amount, new_balance)
            return new_balance
            
        except Exception as e:
            if isinstance(e, InsufficientFundsError):
                status = "insufficient_funds"
            elif isinstance(e, ValueError):
                status = "validation_error"
            else:
                status = "failure"
            raise
        finally:
            self._metrics.record_deduction(agent_id, status, time.time() - start_time)

    def _execute_lua_deduction(self, agent_id: str, amount: float, request_id: str, family_id: str) -> dict:
        key = f"budget:{agent_id}"
        
        for retry in range(10):
            try:
                if not self._script_sha:
                    self._script_sha = self.redis.script_load(self._script_body)
                redis_start = time.time()
                raw = self.redis.evalsha(self._script_sha, 1, key, str(amount), request_id, family_id)
                self._metrics.record_redis_op("evalsha", time.time() - redis_start)
            except redis.ResponseError as e:
                if "NOSCRIPT" in str(e):
                    self.logger.warning("Script evicted; falling back to EVAL")
                    self._script_sha = None
                    redis_start = time.time()
                    raw = self.redis.eval(self._script_body, 1, key, str(amount), request_id, family_id)
                    self._metrics.record_redis_op("eval", time.time() - redis_start)
                    try:
                        self._script_sha = self.redis.script_load(self._script_body)
                    except Exception as cache_error:
                        self.logger.error(f"Failed to re-cache: {cache_error}")
                else: raise

            status_flag = raw[3]
            
            if status_flag == "CORRUPTED":
                raise GovernancePlaneError(f"CRITICAL: Budget corrupted for {agent_id}")
            
            if status_flag == "TIMEOUT":
                raise GovernancePlaneError(f"Lock holder timeout for family_id={family_id}")
                
            if status_flag == "PROCESSING":
                wait_time = min(1.0, (2 ** retry) * 0.01)
                time.sleep(wait_time)
                continue 
                
            return {
                "new_balance": float(raw[0]),
                "prev_balance": float(raw[1]),
                "was_success": bool(raw[2])
            }
            
        raise GovernancePlaneError("Timeout waiting for concurrent family_id lock to release")
