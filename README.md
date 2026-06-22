# Fiscal SecOps Sandbox: Agentic Logic Engine

## 1. System Vision
This repository functions as the dedicated **Agentic Logic Engine** and infrastructure-as-code prototyping environment. It serves as the primary development sandbox for the [Serverless Agentic Governance Controller (SAGC)](https://github.com/brianmlasky/serverless-agentic-governance-controller). 

While the SAGC handles enterprise-scale zero-trust admission control via a sidecar proxy architecture, this sandbox focuses on the underlying mathematical logic: enforcing atomic budget states, real-time circuit breakers, and granular telemetry to prevent "denial-of-wallet" risks from autonomous AI workloads.

## 2. Architectural Fabric
- **The Registry (`registry.py`):** Acts as the ingress router, mapping business intent to policy-backed workloads.
- **The Controller (`main.py`):** The primary Python control plane. It interfaces with the Redis-backed Governance Plane to execute atomic `Check-and-Set` token operations.
- **The Auditor (`auditor.py`):** The observability layer that calculates fiscal health and ensures structural validation of token burn rates.

## 3. Governance Tiers
The logic engine enforces strict boundaries across multi-agent environments:

| Tier | Workload ID | Budget (Tokens) | Purpose |
| :--- | :--- | :--- | :--- |
| **Tier 1** | `alert-triage` | 250 | High-frequency, low-reasoning operations. |
| **Tier 2** | `default` | 150 | General purpose tasking. |
| **Tier 3** | `dr-architect` | 4096 | Complex logic & system design. |

## 4. Operational Procedures
- **Adding a Task:** Update `registry.json` and map the task to an existing workload.
- **Adjusting Budget:** Update `policy.json` (or the corresponding Redis initialization script). *Note: An approved Architecture Decision Record (ADR) is strictly required for budget increases.*
- **Emergency Bypass:** See `docs/runbooks/emergency_bypass.md` for "Fail-Open" vs. "Fail-Closed" mitigation strategies.

## 5. Documentation & ADRs
All structural decisions are documented in the `docs/adr/` directory to maintain design consensus and defensibility.