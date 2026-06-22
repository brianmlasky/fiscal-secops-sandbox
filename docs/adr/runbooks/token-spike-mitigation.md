# Runbook: Token Spike Mitigation (Denial-of-Wallet Defense)

**Target:** Agentic Governance Controller (SAGC)
**Severity:** Critical
**Objective:** Halt unauthorized compute consumption and restore system stability.

## 1. Detection
A spike is defined as an execution exceeding 3x the historical `Avg Total` tokens (tracked in `auditor.py`). If you observe:
- Sudden `INFRASTRUCTURE GOVERNOR TRIGGERED` errors in logs.
- Unexpected costs in `audit_log.json`.

## 2. Immediate Response (The "Kill Switch")
If the agent is in a recursive loop or being exploited, execute the following:
1. **Set Global Lock:**
   `redis-cli SET global-primary-lock aws-primary NX EX 300` 
   *(This prevents traffic from reaching the egress gate for 5 minutes.)*
2. **Revoke Impersonation:**
   `gcloud auth revoke --all`
   *(This instantly invalidates the machine identity.)*
3. **Emergency Policy Update:**
   Update `policy.json` to set `max_allowed_budget` to `0` for the offending `workload_id`.

## 3. Recovery
1. **Analyze:** Run `python auditor.py` to identify the specific `workload_id` causing the spike.
2. **Remediate:** Check the prompt history in `audit_log.json` for signs of prompt injection.
3. **Revert:** Once patched, set `max_allowed_budget` back to the standard limit and rotate the service account credentials if necessary.