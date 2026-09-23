# Troubleshooting journal

Keep chronological entries. Copy this block for each meaningful investigation.

## Entry / date / time 24/
- Symptom: curl: (56) Recv failure: Connection reset by peer
- Hypothesis:the published container port differs from NGINX’s listening port
- Command or test:  `grep -nE 'ports:|listen ' docker-compose.yml nginx/nginx.conf`; `docker compose -p barq-assessment ps -a`; `curl -i --max-time 5 http://127.0.0.1:8080/health`.

- Actual output:Compose shows `127.0.0.1:8080->81/tcp`; `nginx.conf` shows `listen 80;`; curl reports connection reset.

- Failed attempt and what changed your thinking: I changed the NGINX published port from 81 to 80 and recreated the NGINX container, but host curl still returned `curl: (56) Recv failure: Connection reset by peer`. Testing inside NGINX then returned `HTTP/1.1 502 Bad Gateway`. The NGINX error log showed `connect() failed (111: Connection refused)` for upstream `172.19.0.3:8081`, so I investigated the upstream port next.
- Root cause: The public port mapped host 8080 to NGINX port 81, while NGINX listened on 80. NGINX also pointed to app-01 port 8081 instead of 8080. Flask bound to 127.0.0.1 inside the app containers, so NGINX could not reach it over the Docker network.
- Fix: Changed the NGINX published container port from 81 to 80, its app-01 upstream port from 8081 to 8080, and APP_HOST from 127.0.0.1 to 0.0.0.0.
- Retest evidence: Immediately after recreating the apps, /health returned 502 while they were still starting. A later `curl -i --max-time 5 http://127.0.0.1:8080/health` returned `HTTP/1.1 200 OK` at 2026-09-23 21:54:09 UTC. The NGINX access log recorded upstream `172.19.0.3:8080` with status 200.
- Related commit: Pending until the fix commit is created.
- Remaining uncertainty: The Docker app health checks request /healthz and receive 404. Both app instances currently report the same identity. Other endpoints and dependencies have not yet been validated.

Do not fabricate a failed attempt just to fill the template. Record actual attempts.
