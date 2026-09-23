# Troubleshooting journal

Keep chronological entries. Copy this block for each meaningful investigation.

## Entry / date / time 24/
- Symptom: Both app containers were running but marked unhealthy.
- Hypothesis: Docker checks a path the Flask app does not provide.
- Command or test:`grep -n 'healthz\|/health' docker-compose.yml app/server.py`; `docker compose -p barq-assessment ps -a`.
- Actual output:Compose checks `/healthz` on line 12; Flask defines `/health` on line 96. Both apps were `Up 13 minutes (unhealthy)`.
- Failed attempt and what changed your thinking: None for this issue yet.
- Root cause: The configured health-check path does not match the Flask route.
- Fix: Pending.
- Retest evidence: Pending.
- Related commit: Pending.
- Remaining uncertainty: Whether changing the path makes both containers healthy.

Do not fabricate a failed attempt just to fill the template. Record actual attempts.
