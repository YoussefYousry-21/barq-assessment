# Troubleshooting journal

Keep chronological entries. Copy this block for each meaningful investigation.

## Entry / date / time 24/
- Symptom: curl: (56) Recv failure: Connection reset by peer
- Hypothesis:the published container port differs from NGINX’s listening port
- Command or test:  `grep -nE 'ports:|listen ' docker-compose.yml nginx/nginx.conf`; `docker compose -p barq-assessment ps -a`; `curl -i --max-time 5 http://127.0.0.1:8080/health`.

- Actual output:Compose shows `127.0.0.1:8080->81/tcp`; `nginx.conf` shows `listen 80;`; curl reports connection reset.

- Failed attempt and what changed your thinking:
- Root cause:Pending a one-line port correction and retest.
- Fix:pending for now
- Retest evidence:
- Related commit:
- Remaining uncertainty:

Do not fabricate a failed attempt just to fill the template. Record actual attempts.
