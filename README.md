# Fiscal SecOps Governance Engine

A production-hardened governance plane for autonomous AI agents, featuring atomic budget control, tamper-evident audit trails, and resilient failure modes.

## Hardening Sprint Summary
- **Atomic Integrity:** Lua-based state transitions with request-id idempotency.
- **Resilience:** Circuit breaking, automatic script recovery, and fail-closed architecture.
- **Audit Plane:** Cryptographically chained, atomic audit logs with log rotation.
- **Security:** Token-bucket rate limiting to prevent 'Denial of Wallet' attacks.

## Emergency Operations
Use `python3 emergency_override.py <agent_id> <amount>` to perform manual budget injections during service outages.
