# Fiscal SecOps Governance Engine

A production-hardened governance plane for autonomous AI agents, featuring atomic budget control, tamper-evident audit trails, and resilient failure modes.

## System Vision
Autonomous agents in production consume highly variable, non-deterministic token budgets. Relying on application-layer logic to throttle API spend exposes the enterprise to "Denial of Wallet" attacks and runaway compute loops. 

This repository serves as a **Serverless Agentic Governance Controller (SAGC)**. It demonstrates how to decouple fiscal policy from execution logic, utilizing a fail-closed architecture to mathematically bound AI infrastructure costs.

## Core Architecture
* **Identity:** Enforces Zero Trust via Application Default Credentials (ADC) rather than static API keys.
* **Atomic State:** Leverages Redis and Lua scripting to guarantee sub-millisecond, race-condition-free budget deductions.
* **Immutable Ledger:** Utilizes a Three-Phase Audit pattern backed by PostgreSQL to ensure cryptographic ledger integrity, even during catastrophic kernel panics.

## Documentation & Engineering Specs

This system was designed using strict incident command principles. Full architectural decisions, trade-off analyses, and emergency runbooks are documented below:

### Architecture Decision Records (ADRs)
* [ADR 001: Governance-First Architecture](docs/adr/001-governance-first-architecture.md)
* [ADR 002: Redis-based Atomic State Management](docs/adr/002-redis-state-management.md)
* [ADR 003: Lua-Based Atomic Decrement for Budgets](docs/adr/003-lua-atomic-decrement.md)
* [ADR 004: Immutable Audit Logging](docs/adr/004-immutable-audit-logging.md)
* [ADR 005: Migration to SQLite for Audit Plane Integrity](docs/adr/005-sqlite-audit-plane.md)
* [ADR 006: PostgreSQL and Three-Phase Audit Logging](docs/adr/006-postgres-and-three-phase-audit.md)

### Operations & Runbooks
* [Runbook: Emergency Governance Bypass](docs/runbooks/emergency-bypass.md)
* [Runbook: Token Spike Mitigation (Denial-of-Wallet Defense)](docs/runbooks/token-spike-mitigation.md)
* [Scalability Roadmap](docs/roadmap.md)

## Environment Setup
This repository includes a `devcontainer.json` for reproducible environments. The container automatically provisions Python 3.11, the Google Cloud CLI, local Redis, and PostgreSQL.

**Authenticate your CLI before execution:**
```bash
gcloud auth login