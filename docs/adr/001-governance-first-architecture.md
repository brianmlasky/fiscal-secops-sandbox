# ADR 001: Governance-First Architecture

**Status:** Accepted
**Date:** 2026-06-19

## Context
Autonomous agents in production consume variable token budgets. Hardcoding limits in application logic leads to drift and inability to perform centralized cost control.

## Decision
We have decoupled the execution logic from the fiscal policy. All agents must query the `policy.json` contract at runtime. If a policy is missing, the system defaults to a fail-closed 150-token limit.

## Consequences
- **Pros:** Centralized fiscal control; auditability; zero-config deployment changes.
- **Cons:** Added latency of a file read (negligible vs. API latency).