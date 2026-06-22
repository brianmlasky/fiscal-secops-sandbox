# ADR 002: Redis-based Atomic State Management
**Status:** Accepted
**Date:** 2026-06-22

## Context
Current architecture relies on `policy.json` reads. This is insufficient for high-concurrency environments as it risks race conditions during token consumption and lacks real-time updates.

## Decision
We will adopt Redis as the primary state store for atomic budget enforcement using Lua scripts. This provides sub-millisecond governance and guarantees atomicity of state transitions.

## Consequences
- **Pros:** Eliminates race conditions; enables real-time fiscal control; supports distributed agent scaling.
- **Cons:** Introduces a dependency on a Redis infrastructure; requires HA configuration for production.