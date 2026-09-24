#!/usr/bin/env python3
"""Summarize the three supplied historical logs without changing them."""
import collections
import json
import math
import re
import statistics
from pathlib import Path


def read_json_log(name):
    rows, malformed, duplicates, seen = [], [], [], set()
    for line_number, line in enumerate(
        Path("logs", name).read_text().splitlines(), 1
    ):
        try:
            row = json.loads(line)
            assert isinstance(row, dict) and row["request_id"] and row["timestamp"]
        except (ValueError, KeyError, AssertionError, TypeError):
            malformed.append(line_number)
            continue

        # Application logs can have different events for the same request.
        key = (row["request_id"], row.get("event", "http_request"))
        if key in seen:
            duplicates.append(line_number)
            continue
        seen.add(key)
        rows.append(row)
    return rows, malformed, duplicates


access, access_bad, access_dup = read_json_log("access.log")
app, app_bad, app_dup = read_json_log("application.log")
errors = Path("logs/error.log").read_text().splitlines()
diagnostics = [line for line in errors if "request_id=" in line]

statuses = collections.Counter(row["status"] for row in access)
latencies_ms = sorted(row["request_time"] * 1000 for row in access)
retries = [row for row in access if "," in row["upstream_status"]]
dependency_events = [
    row for row in app if row.get("event") == "dependency_error"
]

result = {
    "access": {
        "physical": len(access) + len(access_bad) + len(access_dup),
        "unique_valid": len(access),
        "malformed_lines": access_bad,
        "duplicate_lines": access_dup,
    },
    "application": {
        "physical": len(app) + len(app_bad) + len(app_dup),
        "unique_valid_events": len(app),
        "malformed_lines": app_bad,
        "duplicate_lines": app_dup,
    },
    "error": {
        "physical": len(errors),
        "request_diagnostics": len(diagnostics),
        "other_notices": len(errors) - len(diagnostics),
        "duplicate_request_ids": len(diagnostics) - len(set(
            re.findall(r"request_id=([^, ]+)", "\n".join(diagnostics))
        )),
    },
    "utc_access_interval": [
        min(row["timestamp"] for row in access),
        max(row["timestamp"] for row in access),
    ],
    "distinct_client_requests": len({row["request_id"] for row in access}),
    "final_client_statuses": dict(sorted(statuses.items())),
    "server_error_rate": sum(
        count for status, count in statuses.items() if status >= 500
    ) / len(access),
    "all_error_rate": sum(
        count for status, count in statuses.items() if status >= 400
    ) / len(access),
    "latency_ms": {
        "median": statistics.median(latencies_ms),
        "p95_nearest_rank": latencies_ms[
            math.ceil(0.95 * len(latencies_ms)) - 1
        ],
    },
    "retry_count": len(retries),
    "retry_succeeded": sum(row["status"] == 200 for row in retries),
    "failed_path_status": {
        str(key): count for key, count in sorted(collections.Counter(
            (row["path"], row["status"])
            for row in access if row["status"] >= 500
        ).items())
    },
    "failures_by_utc_minute": dict(sorted(collections.Counter(
        row["timestamp"][:16] for row in access if row["status"] >= 500
    ).items())),
    "dependency_errors": {
        str(key): count for key, count in collections.Counter(
            (row.get("dependency"), row.get("error_type"))
            for row in dependency_events
        ).items()
    },
    "proxy_errors": {
        "connection_refused": sum(
            "Connection refused" in line for line in diagnostics
        ),
        "upstream_timeout": sum("timed out" in line for line in diagnostics),
    },
}
print(json.dumps(result, indent=2))
