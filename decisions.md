# Technical decisions

Record at least 5 decisions. Include assumptions and limits.

# Technical decisions

## 1. Python base image and process user
- Choice: Pin `python:3.12-slim-bookworm` by digest and run the app as UID 10001.
- Why: A small Debian image supports the installed Python packages; a non-root app limits the impact of a process compromise.
- Alternative: Alpine Python or running as root.
- Trade-off: Debian slim is larger than Alpine; dependencies still need vulnerability scanning.
- Evidence: `Dockerfile`; container build, endpoint validation, and image scan.
- Production improvement: Rebuild regularly from reviewed base-image updates.

## 2. Separate liveness and readiness
- Choice: `/health` checks the Flask process; `/ready` performs real PostgreSQL and Redis operations. Docker app health checks use `/health`; NGINX checks its local `/health` route.
- Why: A live process and available dependencies answer different questions. Compose startup waits for database/cache health.
- Alternative: One endpoint checking everything.
- Trade-off: Dependency outages can return `/ready` 503 while the process remains healthy; monitoring must distinguish them.
- Evidence: `validate.py`, Compose health checks, and CI run 35943106764.
- Production improvement: Monitor both endpoints and dependency latency.

## 3. Two isolated networks
- Choice: NGINX and apps share `frontend`; apps, PostgreSQL and Redis share internal `backend`.
- Why: NGINX needs to reach apps but does not need direct data-service access.
- Alternative: Put all services on one network.
- Trade-off: More network configuration to maintain as services change.
- Evidence: `validate.py` checks membership and published ports.

## 4. Proxy timeout and retry behavior
- Choice: NGINX uses a 2-second connect timeout, 3-second read timeout, and up to two attempts for configured upstream failures.
- Why: Bound how long a request waits and try the second app after a failed connection.
- Alternative: No retry or a much longer timeout.
- Trade-off: In-flight requests can still fail; retries can add load and do not make state-changing requests automatically safe to repeat.
- Evidence: `failure_test.py` measured 30/30 HTTP 200 while app-01 was stopped.
- Production improvement: Measure latency and error budgets under load before tuning timeouts.

## 5. Restart and resource controls
- Choice: `unless-stopped`, health-based startup ordering, 256 MB/0.5 CPU per app, 512 MB/1 CPU PostgreSQL, and 128 MB/0.5 CPU each for Redis and NGINX.
- Why: Recover crashed processes, avoid starting dependents before healthy dependencies, and bound lab resource use.
- Alternative: No restart policy or resource limits.
- Trade-off: Limits may be too small for production and restart does not solve an underlying fault.
- Evidence: Compose recreation, `validate.py`, `failure_test.py`, and CI run 35940983269.
- Production improvement: Size limits from observed usage and alerts.

## 6. Persistent data and restoration
- Choice: Named PostgreSQL and Redis volumes; PostgreSQL custom-format dump restored into a separate test database.
- Why: Container recreation must not erase records, and a backup is useful only if restoration works.
- Alternative: Temporary filesystem or keeping a dump without testing restore.
- Trade-off: Local volumes and backups still share the same host failure risk.
- Evidence: record `id=4` survived recreation; `barq_restore_test` contained `4|volume-proof-20260923`.
- Production improvement: Encrypted off-host backups, retention and scheduled restore drills.

## 7. CI and security scan
- Choice: CI builds the Compose stack and runs bounded validation; a separate Trivy image scan produces a report without blocking CI.
- Why: Every push/PR tests behavior; the scan exposes image findings for review.
- Alternative: Manual testing only, or fail immediately on every scanner finding.
- Trade-off: Green CI covers defined checks only; report-only scan does not enforce remediation.
- Evidence: CI run 35940983269 and scan run 35943656166.
- Production improvement: Review findings, then adopt a documented blocking threshold.



Cover your base image, health checks, networks, timeouts/retries, restart/resource settings,
storage and any other meaningful choices.
