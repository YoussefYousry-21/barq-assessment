# BARQ DevOps assessment

A Flask API runs behind NGINX with PostgreSQL and Redis. The final Compose configuration defines three app instances (`app-01`, `app-02`, and `app-03`) and publishes only NGINX at `127.0.0.1:8090`. Flask listens on port 8080 inside the containers; NGINX listens on port 80 inside its container.

## Requirements

Linux/WSL2, Git, Python 3, Docker Engine and Docker Compose. Run commands from the repository root. Keep `.env` and database dumps out of Git.

## First-time setup

```bash
cp .env.example .env
python3 - <<'PY'
import secrets
from pathlib import Path
path = Path(".env")
path.write_text(path.read_text().replace(
    "replace-with-a-long-random-password", secrets.token_hex(24)
))
PY
chmod 600 .env
docker compose -p barq-assessment config --quiet

```

## Build, start, validate

```bash
docker compose -p barq-assessment build
docker compose -p barq-assessment up -d
docker compose -p barq-assessment ps -a
python3 validate.py
python3 failure_test.py
```

The final public URL is `http://127.0.0.1:8090`. Only NGINX publishes a host port. `/health` checks the process; `/ready` checks PostgreSQL and Redis. The failure test stops app-01, measures 30 requests, restores it, and checks the expected identities after recovery.

## Endpoints

```bash
curl -fsS http://127.0.0.1:8090/
curl -fsS http://127.0.0.1:8090/health
curl -fsS http://127.0.0.1:8090/ready
curl -fsS http://127.0.0.1:8090/instance
curl -fsS http://127.0.0.1:8090/records
curl -fsS -H 'Content-Type: application/json' -d '{"title":"demo"}' http://127.0.0.1:8090/records
curl -fsS http://127.0.0.1:8090/counter
```

Repeat `/instance` to observe app-01, app-02, and app-03. NGINX reaches apps through `frontend`; apps reach `postgres:5432` and `redis:6379` through internal `backend`. PostgreSQL and Redis have named volumes.

## Backup and restore

```bash
backup_file=$(./backup.sh)
./restore.sh "$backup_file" barq_restore_demo
docker exec postgres psql -U barq_app -d barq_restore_demo -c 'SELECT id, title FROM records;'
```

The restore script creates a separate test database. A record with ID 4 survived PostgreSQL and app recreation and was present in a restored backup. Dump files and `.env` are ignored by Git.

## Logs, CI, security

```bash
python3 scripts/analyze_logs.py
grep -n 'lab-000124' logs/access.log logs/error.log logs/application.log
```

See `log_analysis.md`, `troubleshooting.md`, `decisions.md`, `security_review.md`, `AI_USAGE.md`, and `architecture.png`. CI builds, starts and validates on push/PR. The optional Trivy scan is report-only; its first run found three HIGH findings. Green CI proves only its defined checks.

## Stop and cleanup

```bash
docker compose -p barq-assessment down
```

This retains named volumes. `down -v` permanently deletes this lab's data and must not be used during persistence testing or the recorded challenge. Back up data first.

## Availability limits

The initial two-app failure test measured 30/30 HTTP 200 responses with `app-01` stopped. The final configuration has three app instances; rerun the updated failure test to verify its final behavior. NGINX, PostgreSQL, Redis, and the Docker host remain single points of failure. Production would require redundant ingress and data services, off-host backups, TLS, monitoring, and managed secrets.


## Validation limits

`validate.py` should return a nonzero exit code when an endpoint, dependency operation, expected instance, health check, port binding, or network membership fails. A green CI run proves those checks passed for that commit in the CI environment. It does not prove production availability, security, performance under load, or that every possible failure was covered.

The recorded demonstration includes runtime troubleshooting. The investigation journal records observed errors and repairs; a command that failed during startup is not reported as a successful test.
