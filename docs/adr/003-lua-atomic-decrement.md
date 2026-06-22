# ADR 003: Lua-Based Atomic Decrement for Token Budgets

**Status:** Accepted
**Date:** 2026-06-22

## Context
Following [ADR 002](002-redis-state-management.md), we established Redis as our primary state store. However, executing a "Check-and-Set" (CAS) operation from the Python application layer (e.g., `GET budget`, verify in Python, `SET budget`) introduces a race condition. High-speed autonomous agents could query the same budget state concurrently, leading to over-commitment of tokens and rendering the fiscal circuit breaker ineffective.

## Decision
We will encapsulate the fiscal decrement logic entirely within Redis using Lua scripting. The Python `FiscalGovernanceController` will pass the agent ID and requested token amount to Redis via the `EVAL` command. Redis's single-threaded nature ensures the Lua script executes atomically, verifying the balance and deducting the amount in one uninterruptible operation.

## Consequences
- **Pros:** Guarantees absolute atomicity under high concurrent load; eliminates network round-trip latency between the read and write operations; provides true "structural validation" of fiscal boundaries.
- **Cons:** Business logic (the budget calculation) is now split between Python and Lua; requires specific documentation for maintaining Lua scripts within the Python repository.