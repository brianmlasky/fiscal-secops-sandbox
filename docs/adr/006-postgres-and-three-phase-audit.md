# ADR 006: Migration to PostgreSQL and Three-Phase Audit Logging

## Status
Accepted

## Context
The Final Adversarial Audit identified critical distributed systems limitations in our architecture under high concurrency. 
1. **Database Starvation:** SQLite, even in WAL mode, suffers from lock starvation and connection pool exhaustion when subjected to concurrent writes. The `check_same_thread=False` flag bypassed Python's thread checks but did not actually provide connection thread-safety, risking silent data corruption.
2. **Audit Ledger Drift:** The previous logging mechanism lacked a crash-proof state reconciliation pattern. A process failure occurring immediately after a successful Redis execution—but before the SQLite commit—would leave the fiscal state and the audit ledger permanently out of sync.

## Decision
1. **PostgreSQL Migration:** We will deprecate local SQLite in favor of PostgreSQL, utilizing `psycopg2.pool.SimpleConnectionPool` to handle highly concurrent, thread-safe write streams. (The eventual infrastructure target will be a managed Cloud SQL for PostgreSQL instance on Google Cloud Platform).
2. **Three-Phase Logging (Audit-First):** We will adopt an intent-based transaction pattern:
   - **Phase 1 (Intent):** Pre-log the operation intent with the starting hash state.
   - **Phase 2 (Execution):** Execute the atomic Redis Lua deduction.
   - **Phase 3 (Resolution):** Update the initial intent record with the final `SUCCESS` or `INSUFFICIENT_FUNDS` outcome.
3. **Atomic Lua Locks:** Idempotency enforcement has been refactored to use atomic `SET ... NX` primitives, eliminating Time-Of-Check to Time-Of-Use (TOCTOU) double-spend vulnerabilities.

## Consequences
* **Positive:** True enterprise-grade concurrency; elimination of double-spend race conditions; mathematically infallible audit trails that can survive catastrophic mid-process kernel panics.
* **Negative:** Introduces an external database dependency (`psycopg2-binary`) and mandates the provisioning of a managed PostgreSQL instance prior to any production deployment.
