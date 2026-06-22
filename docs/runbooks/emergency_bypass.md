# Runbook: Emergency Governance Bypass

## Context
When the Governance Plane (Redis) is unreachable or enters a "Fail-Closed" state, mission-critical agents may halt. This runbook details the recovery procedure.

## Protocol: The "Break-Glass" Procedure
1. **Verification:** Confirm Redis connectivity failure (e.g., `redis-cli ping` fails).
2. **Authorization:** Obtain verbal/written sign-off from the Architect or Lead Engineer.
3. **Execution:** - Set the `FAIL_CLOSED` override environment variable to `False` in the agent deployment.
   - Execute the `manual_override.py` script to inject a temporary "emergency budget" directly into the agent’s execution path.
4. **Post-Incident Audit:** Every "break-glass" event must be logged as a `CIRCUIT_TRIP` event in the audit trail. A mandatory post-mortem ADR must be generated within 24 hours of bypass.