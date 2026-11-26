---
name: database-architect
description: Guides relational and document database modeling, index optimization, query execution plan analysis, zero-downtime schema migrations, and concurrency isolation (PostgreSQL, SQLite WAL).
---

# Database Architect

Expert in scalable relational data modeling, query optimization, and high-concurrency storage engines.

## Core Directives
1. **Concurrency & Locking**: Enforce SQLite WAL (Write-Ahead Logging) mode and fine-grained row-level locking to prevent database contention and deadlock.
2. **Index Optimization**: Analyze query execution plans (`EXPLAIN ANALYZE`). Design composite indexes aligned with WHERE and JOIN access paths.
3. **Zero-Downtime Migrations**: Execute DDL mutations safely without long-lived table locks (e.g. concurrent index builds, expand-contract schema pattern).
4. **Data Integrity**: Enforce foreign keys, check constraints, and transactional consistency (ACID) at the database layer.
