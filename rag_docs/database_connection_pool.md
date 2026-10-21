# Database Connection Pool Exhaustion

## Purpose
This runbook describes how to investigate incidents where applications cannot obtain database connections or where the database reaches its configured connection limit.

## Common symptoms
- database connection timeouts
- increasing API or worker latency
- HTTP 5xx responses
- rapidly increasing active connection counts
- rejected or blocked database clients
- requests waiting for an available connection

Connection exhaustion is often a symptom rather than the root cause.

## Initial checks
Check the current connection count and compare it with the configured maximum.

Investigate:
- recent deployments or configuration changes
- increased request concurrency
- changes to batching or request aggregation
- changes to connection reuse
- slow queries or long-running transactions
- connection leaks
- retry storms
- scaling changes that increase the number of clients

A rapid increase after a deployment is evidence of correlation, but does not by itself prove the mechanism.

## Application-side investigation
Inspect logs from services that connect to the database.

Look for:
- connection acquisition timeouts
- repeated connection creation
- aggressive retries
- changes in worker count
- disabled batching or aggregation
- errors that prevent connections from being returned correctly

If multiple services fail at about the same time, determine whether they share the same database or connection limit.

## Database-side investigation
Check:
- active connections
- maximum allowed connections
- connection creation rate
- query latency
- lock contention
- long-running transactions
- idle connections
- rejected clients

High connection count with normal query latency may indicate a different failure mode from high connection count caused by slow queries.

## Common causes
1. Increased request concurrency
2. Reduced batching or aggregation
3. Connection leaks
4. Slow queries or transactions
5. Retry amplification
6. Pool configuration mismatch
7. Additional application instances or workers

## Mitigation
Possible actions include:
- roll back a risky configuration change
- reduce concurrency
- restore batching
- limit retries
- reduce worker count temporarily
- terminate clearly stuck connections
- increase connection limits only when database capacity supports it

Increasing the connection limit should not be the default response, because it can hide the underlying source of connection pressure.

## Verification
After mitigation, verify that:
- connection count returns to a stable level
- timeouts stop
- API and worker error rates fall
- latency decreases
- queues begin draining
