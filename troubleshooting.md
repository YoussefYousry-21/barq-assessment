# Troubleshooting journal


## 2026-09-23 — Public routing

- Symptom: Host `/health` initially reset the connection.
- Evidence: Compose mapped `127.0.0.1:8080` to NGINX port 81, while NGINX listened on 80.
- Failed attempt: Changing only the published port did not solve access. Testing inside NGINX returned 502; its error log showed a refused connection to app-01 port 8081.
- Further cause: App-01 listened on 8080, and Flask bound to `127.0.0.1` inside its container, so NGINX could not reach it over the Docker network.
- Fix: Mapped host 8080 to NGINX 80, changed the upstream to app-01:8080, and bound Flask to `0.0.0.0`.
- Retest: `/health` returned HTTP 200 at 21:54:09 UTC after startup. The immediate 502 after recreation was a startup race.
- Commits: `5984042` investigation; `f87e8b7` fix.

## 2026-09-23 — Health and identity

- Symptom: Both app containers ran but Docker marked them unhealthy; both `/instance` responses said app-01.
- Evidence: Compose checked `/healthz`, but Flask defines `/health`. Compose assigned `INSTANCE_ID: app-01` to app-02.
- Fix: Changed the health path to `/health` and the second ID to `app-02`.
- Retest: Both containers became healthy; repeated `/instance` requests returned both identities. Immediate requests during recreation sometimes reset before services started.
- Commits: `c2b3530` investigation; `6765e66` health fix; `bde238e` identity fix.

## 2026-09-23 — Data-service connections

- Symptom: `/ready`, `/records`, and `/counter` returned 503 despite PostgreSQL and Redis containers being healthy.
- Evidence: App URLs used `postgres:5433` and `redis:6380`, while services listened on 5432 and 6379. After correcting ports, Redis worked but PostgreSQL still failed because the database password did not match.
- Fix: Used matching values from ignored `.env`, removed the credential file copied into the image, and passed the password into PostgreSQL through Compose.
- Retest: `/ready` reported both dependencies ready; `/records` returned rows and `/counter` incremented.
- Commit: `7c303ff`.

## 2026-09-23 — Persistence

- Symptom: PostgreSQL data originally lived on `tmpfs` while the named volume mounted a backup directory; Redis persistence was disabled.
- Fix: Mounted the PostgreSQL named volume at `/var/lib/postgresql/data`, enabled Redis AOF on a named volume, removed database/cache host port publication, and isolated the backend network.
- Retest: Record `id=4`, title `volume-proof-20260923`, remained after PostgreSQL and app recreation. A custom-format dump restored the same row into `barq_restore_test`.
- Commit: `5b0b40a` for volume/network changes; backup/restore scripts were committed later.
