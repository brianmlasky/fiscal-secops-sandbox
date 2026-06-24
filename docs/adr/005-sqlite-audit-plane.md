# ADR 005: Migration to SQLite for Audit Plane Integrity

## Status
Accepted

## Context
A Phase 2 Adversarial Audit identified a CRITICAL vulnerability in our custom flat-file audit logging. If a process crash occurred between the `fsync` of the audit log and the update of the hash index file, the cryptographic chain became silently and irreparably corrupted. Additionally, file-level locking (`fcntl`) created risks of thread starvation and deadlocks.

## Decision
We will deprecate flat JSON files and adopt **SQLite** as the storage backend for the `Auditor`. 

* We will enable `PRAGMA journal_mode=WAL` to ensure high-concurrency write safety without blocking reads.
* We will leverage SQLite's native ACID transaction guarantees (`BEGIN`, `COMMIT`, `ROLLBACK`) to ensure that a log entry and its corresponding hash chain update are written atomically. If the system crashes mid-transaction, SQLite will automatically rollback, preventing partial states.

## Consequences
* **Positive:** Complete elimination of torn writes, race conditions, and corrupted hash chains. Simplifies the Python codebase by removing manual lock management.
* **Negative:** Audit logs are no longer human-readable text files; they require a SQLite client or a Python script to query and verify.
