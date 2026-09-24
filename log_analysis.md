# Log analysis

Use all three supplied logs. Answer every question with commands/scripts and actual output.

1. What UTC interval is covered? How many valid, malformed and duplicate lines are in each file?
2. How many distinct client requests occurred? How did you deduplicate and avoid counting retries twice?
3. What are the final client status counts and error rate? State your denominator.
4. Which paths, time windows and backends account for the failures?
5. What are the median and p95 client latencies? State the percentile method and units.
6. Which requests retried upstream? How many succeeded after retrying?
7. Build an incident timeline using evidence from access, error AND application logs.
8. Show one correlated failed request and one successful request. Include IDs and timestamps.
9. Which errors appear to be proxy/connectivity issues versus dependency/application issues? What proves it?
10. What do the logs not prove? What would you check next in a running environment?

## Commands / scripts

- Count physical lines: `wc -l logs/access.log logs/error.log logs/application.log`
- Verify unchanged inputs: `sha256sum logs/access.log logs/error.log logs/application.log`
- Recalculate all counts: `python3 scripts/analyze_logs.py`
- Join example IDs: `grep -nE 'lab-000122|lab-000124|lab-000607' logs/access.log logs/error.log logs/application.log`
The script reads the original logs, removes duplicate records, and counts final client responses from access records. Matching request IDs connect the access, error, and application evidence.

## Results
### 1. Time interval and file quality

The access log covers 2026-08-20 11:00:00.015–11:29:57.578 UTC. The script `python3 scripts/analyze_logs.py` found 726 access lines: 720 unique valid requests, 5 duplicate lines (122, 243, 365, 486, 607), and 1 malformed line (311). The application log has 730 lines: 727 unique valid events, 2 duplicates (162, 415), and 1 malformed line (401). The error log has 68 lines: 67 request diagnostics and 1 other notice.

### 2. Client requests and retries

The access log contains 720 distinct request IDs. I count each ID once; an application entry or NGINX error entry for the same ID is evidence about that request, not another client request. For `lab-000124`, NGINX first failed to connect to `.12`, retried `.11`, and the client finally received 200. The `502, 200` upstream field represents two attempts within one request.
## Timeline and correlated examples
## Conclusions and limits


### 3. Final client statuses and error rate

The 720 final responses were: 200 = 615, 404 = 10, 502 = 40, 503 = 47, and 504 = 8. Final server errors were 95/720 = 13.19%. If 404 is included, all 4xx/5xx responses were 105/720 = 14.58%. The denominator is distinct client requests in the access log, not backend attempts.

### 4. Failure paths, times, and backends

There were 40 final 502 responses: 10 each for `/`, `/health`, `/records`, and `/counter`. Their failed upstream was `172.23.0.12:8080`. There were 47 final 503 responses: `/ready` 23, `/counter` 16, and `/records` 8. Another 8 `/records` requests ended 504.

Final 5xx responses by UTC minute were: 11:05–11:09, 8 each minute; 11:12, 8; 11:13, 7; 11:14–11:15, 8 each minute; 11:20–11:21, 8 each minute; and 11:25–11:26, 4 each minute. Successful retries are excluded because their final client response was 200.


### 5. Client latency

The median final request time was 54 ms and p95 was 2001 ms. The script converts access-log `request_time` from seconds to milliseconds and sorts all 720 values. The median averages the middle two values. P95 uses nearest rank: position `ceil(0.95 × 720) = 684` in the sorted list, counting from 1.

### 6. Upstream retries

Nineteen access records show more than one upstream attempt, and all 19 ended with a final 200. `lab-000124` is one example: its attempts were `502, 200`, but the client received 200.
	

### 7. Incident timeline (UTC)

- 11:00–11:04: Normal requests appear in access and application logs. `/missing` requests return 404.
- 11:05–11:09: NGINX records 59 connection-refused attempts to `.12`. Access records show 40 final 502 responses and 19 requests that succeed after retrying `.11`.
- 11:12–11:15: Application logs record 31 Redis `TimeoutError` events. Access records show 503 responses on `/ready` and `/counter`.
- 11:20–11:21: Application logs record 16 PostgreSQL `InvalidPassword` events. Access records show 503 responses on `/ready` and `/records`.
- 11:25–11:26: NGINX records 8 upstream read timeouts; access records show 8 final 504 responses on `/records`.

### 8. Requests joined by ID

Failed request `lab-000122`: access line 123 records `GET /health`, final 502 at 11:05:02.503Z. Error line 1 records a refused connection to `.12` at 11:05:02. There is no matching application request event, consistent with the app never receiving that attempt.

Successful request `lab-000124`: access line 125 records `GET /ready`, final 200 at 11:05:07.620Z after upstream results `502, 200`. Error line 2 records the failed connection to `.12`. Application line 123 records app-01 returning 200 for the same request ID after NGINX retried `.11`.

A late response also appears for `lab-000607`: NGINX returned 504 to the client after 2.001 seconds, while app-01 later logged 200 after 2700 ms. The app's later status did not change the response already sent to the client.


### 9. Failure types

NGINX connection-refused errors point to an upstream connectivity problem; `lab-000122` has no matching app event. Redis `TimeoutError` and PostgreSQL `InvalidPassword` appear in application events alongside 503 responses. The `/records` 504s are NGINX read timeouts; for `lab-000607`, the app completed after the client had already received 504.

### 10. Limits

The logs do not prove why the app refused connections, why Redis timed out, who changed a database credential, or whether a timed-out operation changed data. I would next inspect container events, dependency server logs, credential changes, and request traces in a running environment. The historical incident and starter configuration are separate evidence sets.

