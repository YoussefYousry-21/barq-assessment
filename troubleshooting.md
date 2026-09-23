# Troubleshooting journal

Keep chronological entries. Copy this block for each meaningful investigation.

## Wed Sep 23 23:32:50 UTC 2026

- Symptom: A stopped Flask backend could cause NGINX requests to fail because `proxy_next_upstream` was `off`.
- Hypothesis: Allowing NGINX to retry a failed connection against the other backend would keep `/health` available.
- Command or test: Changed `nginx/nginx.conf` to `proxy_next_upstream error timeout http_502 http_503 http_504;` and `proxy_next_upstream_tries 2;`. Ran `docker exec nginx nginx -t` and `docker exec nginx nginx -s reload`. Stopped `app-01`, sent 20 sequential `/health` requests, started `app-01`, then sent 20 `/instance` requests.
- Actual output: NGINX configuration test succeeded. During the outage, 20 `/health` requests returned HTTP 200 and zero returned an error. After restart, both app containers were healthy; `/instance` returned `app-01` 10 times and `app-02` 10 times.
- Failed attempt and what changed your thinking: No separate failed attempt during this investigation.
- Root cause: `proxy_next_upstream off` prevented NGINX from trying the available backend after an upstream connection failed.
- Fix: Enabled retries for connection errors, timeouts and 502/503/504 responses, limited to two upstream attempts.
- Retest evidence: `20 200` from the status-count command while `app-01` was stopped; 10 responses from each backend after recovery.
- Related commit: Pending until this change is committed.
- Remaining uncertainty: This was a small sequential test, not a load test. Requests already in progress when a backend stops may still fail.
