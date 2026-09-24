# Security and production readiness review

This is a local assessment stack. “Implemented” describes tested repository changes; “Production follow-up” is proposed work, not a claim of completion.

| Risk and evidence | Implemented | Production follow-up / verification |
|---|---|---|
| Database credentials originally appeared in starter configuration and an app image copy step. | Moved runtime values to ignored `.env`; removed the image copy; `.env.example` contains placeholders. | Use a secret manager, rotate any exposed credentials, and scan full Git history. Verify with image inspection and a secret scan. |
| PostgreSQL and Redis originally published host ports. | Removed their `ports`; only NGINX publishes loopback 8090 in the final configuration. `validate.py` checks bindings. | Add host firewall rules and restrict deployment network access. |
| NGINX originally shared backend network access. | NGINX now joins only `frontend`; apps bridge `frontend` and `backend`; database/cache join only `backend`. | Enforce equivalent segmentation in production orchestration and test it continuously. |
| The app originally ran as root. | Dockerfile uses UID 10001 (`app`). | Run NGINX and data services with least privilege where supported; consider read-only filesystems and dropped capabilities. |
| Base images and Python packages can contain vulnerabilities. | Image tags use digests; an optional Trivy scan runs on push/PR. Run 35943656166 found 3 HIGH `libpcre2-8-0` findings (CVE-2026-86145, CVE-2026-89157, CVE-2026-89161). | Review fixed package/image versions, rebuild, rescan, and set an agreed vulnerability threshold. The report-only scan does not block CI. |
| PostgreSQL data was on temporary storage in the starter. | Named `postgres-data` volume; record `id=4` survived container recreation; backup restored to `barq_restore_test`. | Encrypt backups, retain off-host copies, set retention, and regularly test restore objectives. |
| Redis originally disabled persistence. | Redis AOF is enabled on named `redis-data`. | Define acceptable counter loss, monitor AOF health, and plan backup or replication if required. |
| A single NGINX, PostgreSQL, Redis, and Docker host remain. | Two Flask apps and NGINX retry survived one stopped app: 30/30 requests returned 200. | Use redundant proxy and managed/replicated data services across hosts; test failover under load. |
| Local Docker logs can grow or disappear with containers. | NGINX and app log to stdout; historical log analysis correlates request IDs. | Centralize logs, set retention and rotation, scrub secrets, add metrics and alerts. |
| HTTP on loopback has no TLS or authentication. | Publication is limited to `127.0.0.1` for this lab. | Use HTTPS at the ingress and appropriate authentication and authorization before public deployment. |

A green validation run verifies specified behavior at that commit; it is not a penetration test, load test, or proof that all dependencies are vulnerability-free.
