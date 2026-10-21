# Queue Overload and Backpressure

## Purpose
This runbook describes how to investigate a queue that grows continuously, reaches an operational limit, or begins dropping work.

Queue overload usually means work is entering the system faster than downstream components can process it.

## Common symptoms
- increasing queue length
- delayed request processing
- dropped requests or jobs
- worker lag
- increasing end-to-end latency
- timeout errors
- backpressure warnings
- elevated retry volume

Persistent growth means arrival rate is greater than processing rate.

## Initial checks
Determine:
- when the queue began growing
- whether incoming traffic increased
- whether processing throughput decreased
- whether a deployment happened recently
- whether workers are healthy
- whether a downstream dependency is slow

Queue length must be interpreted together with throughput.

## Producer-side investigation
Possible causes of increased work generation include:
- increased user traffic
- more application instances
- disabled batching
- duplicated events
- retry amplification
- configuration changes that create additional tasks

If batching is reduced, the same logical workload may generate more individual operations.

## Consumer-side investigation
Possible reasons consumers process work more slowly include:
- database latency
- dependency timeouts
- worker saturation
- reduced worker count
- lock contention
- long-running operations
- repeated retries

Increasing worker count can make an overloaded downstream dependency worse.

## Downstream dependencies
A growing queue often reflects a downstream bottleneck.

Example:

incoming requests
→ API
→ queue
→ workers
→ database

If the database refuses connections, workers complete work more slowly and the queue grows even though the queue itself is functioning correctly.

## Backpressure
Useful backpressure mechanisms include:
- concurrency limits
- bounded queues
- rate limiting
- circuit breakers
- load shedding
- adaptive retry policies

Without backpressure, a temporary slowdown can become a cascading failure.

## Retry storms
A failure may create:
original request
→ timeout
→ retry
→ timeout
→ retry

This increases load during the incident.

## Mitigation
Possible actions include:
- reduce producer concurrency
- restore batching
- limit retries
- scale consumers when downstream capacity allows it
- fix the constrained dependency
- reject low-priority work temporarily
- roll back a risky configuration change

Increasing queue capacity alone can hide the bottleneck while increasing latency.

## Verification
After mitigation:
- queue length should stop increasing
- throughput should recover
- dropped work should decrease
- latency should move toward baseline
- downstream dependencies should remain stable
