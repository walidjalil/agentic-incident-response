# API Latency and HTTP 5xx Investigation

## Purpose
This runbook describes how to investigate an API that becomes slow, times out, or returns elevated HTTP 5xx responses.

High API latency is often caused by a dependency rather than by the API process itself.

## Common symptoms
- increased request latency
- HTTP 500, 502, 503, or 504 responses
- growing request queues
- timeout errors
- reduced throughput
- downstream dependency errors
- normal compute utilization despite poor user-facing latency

Low CPU or GPU utilization does not prove that the service is healthy. A service may be waiting on a database, network dependency, lock, or queue.

## Investigation order

### 1. Confirm timing
Compare the start of the incident with:
- deployments
- configuration changes
- traffic changes
- dependency incidents
- scaling events

Timing can suggest a regression, but does not prove root cause.

### 2. Inspect API logs
Look for:
- timeout errors
- failed downstream calls
- database connection errors
- queue warnings
- retry loops
- HTTP 5xx responses
- changes in request processing time

### 3. Inspect downstream dependencies
If the logs point to another service, investigate that dependency before declaring a root cause.

Typical dependencies include:
- databases
- caches
- message queues
- internal services
- external APIs

For database timeouts, inspect connection counts, query latency, and connection-pool health.

### 4. Check queueing
A growing queue means requests are arriving faster than they are being completed.

Possible reasons include:
- downstream latency
- reduced throughput
- concurrency limits
- lock contention
- resource saturation
- retry amplification

Queue growth is evidence of a bottleneck, but is not necessarily the root cause.

### 5. Check resource metrics
Inspect:
- CPU utilization
- GPU utilization
- memory usage
- request rate
- queue length
- worker utilization

Avoid assuming that the largest metric is automatically the cause.

## Recent deployment checks
When an incident begins after a deployment, inspect changes affecting:
- batching
- concurrency
- request fan-out
- retries
- connection reuse
- timeouts
- worker count
- dependency configuration

Configuration changes can increase downstream load even when user traffic remains stable.

## Mitigation
Possible actions include:
- roll back a regression
- reduce concurrency
- apply backpressure
- disable aggressive retries
- scale the constrained component
- restore a previously stable configuration
- fix the failing downstream dependency

## Verification
Verify recovery using:
- API latency
- HTTP error rate
- queue depth
- dependency health
- request throughput
