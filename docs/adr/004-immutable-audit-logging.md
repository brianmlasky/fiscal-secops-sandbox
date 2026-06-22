# ADR 004: Immutable Audit Logging for Fiscal SecOps

**Status:** Proposed
**Date:** 2026-06-22

## Context
Our governance system makes real-time decisions that affect financial outcomes. We currently lack a structured, immutable trail of these decisions, making regulatory-grade incident investigations impossible.

## Decision
All fiscal operations (deductions, balance checks, circuit breaker triggers) must emit a structured audit log entry to the `auditor.py` service. Logs will be formatted in JSON and include a unique `request_id` for idempotency and trace-ability. The audit sink must be decoupled from the governance controller to ensure that audit failures do not block fiscal operations (unless Fail-Closed policies dictate otherwise).

## Consequences
- **Pros:** Full traceability of all fiscal events; compliance with regulatory standards; simplified debugging of agentic behavior.
- **Cons:** Increased logging volume; minor latency overhead for asynchronous log emission.