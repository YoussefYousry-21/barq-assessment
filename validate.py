#!/usr/bin/env python3
"""Validate the running BARQ environment. Exit nonzero if any check fails."""
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

PROJECT = "barq-assessment"
EXPECTED = set(os.getenv("EXPECTED_INSTANCES", "app-01,app-02,app-03").split(","))
PORT = os.getenv("PUBLIC_PORT", "8080")

# Compose reads .env automatically; this standalone script reads only PUBLIC_PORT.
with open(".env", encoding="utf-8") as env_file:
    for line in env_file:
        if line.startswith("PUBLIC_PORT="):
            PORT = line.strip().split("=", 1)[1]

BASE = f"http://127.0.0.1:{PORT}"
failures = 0


def report(name, condition, detail=""):
    global failures
    print(f"{'PASS' if condition else 'FAIL'} {name} {detail}".rstrip())
    if not condition:
        failures += 1


def request(path, data=None):
    headers = {"Content-Type": "application/json"} if data is not None else {}
    payload = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(BASE + path, data=payload, headers=headers)
    with urllib.request.urlopen(req, timeout=5) as response:
        return response.status, json.load(response)


# Wait at most 60 seconds after Compose starts.
ready = False
for attempt in range(30):
    try:
        status, body = request("/ready")
        if status == 200 and body.get("dependencies") == {
            "postgres": "ready", "redis": "ready"
        }:
            ready = True
            break
    except (OSError, ValueError, urllib.error.HTTPError):
        pass
    time.sleep(2)
report("bounded readiness", ready)
if not ready:
    sys.exit(1)

for path in ("/", "/health", "/ready", "/instance"):
    try:
        status, body = request(path)
        report(path, status == 200 and isinstance(body, dict))
    except (OSError, ValueError) as exc:
        report(path, False, type(exc).__name__)

seen = set()
try:
    for _ in range(30):
        _, body = request("/instance")
        seen.add(body["instance_id"])
    report("all backends", seen == EXPECTED,
           f"seen={sorted(seen)} expected={sorted(EXPECTED)}")
except (OSError, ValueError, KeyError) as exc:
    report("all backends", False, type(exc).__name__)

try:
    _, first = request("/counter")
    _, second = request("/counter")
    report("Redis counter", second["counter"] == first["counter"] + 1)
except (OSError, ValueError, KeyError) as exc:
    report("Redis counter", False, type(exc).__name__)

try:
    title = f"validation-{time.time_ns()}"
    status, created = request("/records", {"title": title})
    _, listed = request("/records")
    found = any(row.get("title") == title for row in listed["records"])
    report("PostgreSQL write/read", status in (200, 201) and
           created["record"]["title"] == title and found)
except (OSError, ValueError, KeyError) as exc:
    report("PostgreSQL write/read", False, type(exc).__name__)

names = ["nginx", "app-01", "app-02", "postgres", "redis"]
if "app-03" in EXPECTED:
    names.append("app-03")
try:
    raw = subprocess.run(
        ["docker", "inspect", *names], check=True, capture_output=True,
        text=True, timeout=10
    )
    containers = {item["Name"].lstrip("/"): item for item in json.loads(raw.stdout)}
    healthy = False
    for _ in range(30):
        raw = subprocess.run(
            ["docker", "inspect", *names], check=True, capture_output=True,
            text=True, timeout=10
        )
        containers = {
            item["Name"].lstrip("/"): item for item in json.loads(raw.stdout)
        }
        healthy = len(containers) == len(names) and all(
            c["State"]["Running"] and
            c["State"].get("Health", {}).get("Status") == "healthy"
            for name, c in containers.items()
        )
        if healthy:
            break
        time.sleep(2)
    report("service health", healthy)
    report("only NGINX publishes", all(
        not containers[name]["HostConfig"]["PortBindings"]
        for name in names if name != "nginx"
    ))
    bindings = containers["nginx"]["HostConfig"]["PortBindings"]
    report("host port", bindings.get("80/tcp") == [
        {"HostIp": "127.0.0.1", "HostPort": PORT}
    ])

    def networks(name):
        return set(containers[name]["NetworkSettings"]["Networks"])

    front = f"{PROJECT}_frontend"
    back = f"{PROJECT}_backend"
    report("NGINX network isolation", networks("nginx") == {front})
    report("backend isolation",
           all(networks(name) == {back} for name in ("postgres", "redis")) and
           all(networks(name) == {front, back} for name in EXPECTED))
except (subprocess.SubprocessError, OSError, ValueError, KeyError) as exc:
    report("Docker inspection", False, type(exc).__name__)

print(f"RESULT: {failures} failed")
sys.exit(1 if failures else 0)
