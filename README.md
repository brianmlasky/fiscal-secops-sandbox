# Fiscal SecOps Sandbox

This repository serves as an Infrastructure-as-Code (IaC) sandbox for developing agentic fiscal governance controls. It demonstrates a fail-closed architecture for Google's Gemini reasoning models using Vertex AI.

## Architecture Highlights
* **Identity:** Enforces Zero Trust via Application Default Credentials (ADC) rather than static API keys.
* **Fiscal Governance:** Implements hard `max_output_tokens` budgets to prevent runaway compute spend during the model's internal reasoning phase.
* **Telemetry:** Extracts and logs granular token usage (Prompt, Thought, and Response tokens) for FinOps auditing.

## Environment Setup
This repository includes a `devcontainer.json` for reproducible Codespace environments. 
The container automatically provisions Python 3.11 and the Google Cloud CLI.

### Authentication
Before executing the agent, you must align your CLI and library identities to the Google Cloud project holding the billing quota.

1. Authenticate the CLI:
   ```bash
   gcloud auth login