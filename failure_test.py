#!/usr/bin/env python3
"""Stop one backend, measure availability, restore it, and prove recovery."""
import collections
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
import os
port = "8080"
with open(".env", encoding="utf-8") as env_file:
    for line in env_file:
        if line.startswith("PUBLIC_PORT="):
            port = line.strip().split("=", 1)[1]

url = f"http://127.0.0.1:{port}/instance"
compose = ["docker", "compose", "-p", "barq-assessment"]
failed = False


def fetch():
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            return response.status, json.load(response).get("instance_id")
    except urllib.error.HTTPError as exc:
        return exc.code, None
    except (OSError, ValueError):
        return 0, None


try:
    print("Stopping app-01")
    subprocess.run(compose + ["stop", "app-01"], check=True, timeout=30)

    counts = collections.Counter()
    identities = collections.Counter()
    for _ in range(30):
        status, identity = fetch()
        counts[status] += 1
        if identity:
            identities[identity] += 1

    print(f"Traffic while app-01 stopped: status={dict(counts)} "
          f"instances={dict(identities)}")
    if counts == {200: 30} and identities == {"app-02": 30}:
        print("PASS continued availability: 30 requests, 0 errors")
    else:
        print("FAIL continued availability")
        failed = True

except (subprocess.SubprocessError, OSError) as exc:
    print(f"FAIL outage test: {type(exc).__name__}: {exc}")
    failed = True

finally:
    print("Restoring app-01")
    try:
        subprocess.run(compose + ["start", "app-01"], check=True, timeout=30)
    except (subprocess.SubprocessError, OSError) as exc:
        print(f"FAIL restore: {type(exc).__name__}: {exc}")
        failed = True

seen = set()
deadline = time.monotonic() + 60
while time.monotonic() < deadline:
    status, identity = fetch()
    if status == 200 and identity:
        seen.add(identity)
    if seen == {"app-01", "app-02"}:
        break
    time.sleep(1)

if seen == {"app-01", "app-02"}:
    print("PASS recovery: both backends served requests")
else:
    print(f"FAIL recovery: seen={sorted(seen)}")
    failed = True

print(f"RESULT: {'FAIL' if failed else 'PASS'}")
sys.exit(1 if failed else 0)
