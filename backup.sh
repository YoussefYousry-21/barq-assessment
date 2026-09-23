#!/usr/bin/env bash
set -euo pipefail
umask 077

output="${1:-backups/barq-$(date -u +%Y%m%dT%H%M%SZ).dump}"
mkdir -p "$(dirname "$output")"
temporary="$(mktemp "${output}.tmp.XXXXXX")"
trap 'rm -f "$temporary"' EXIT

docker exec postgres pg_dump -U barq_app -d barq_tasks -Fc > "$temporary"
test -s "$temporary"
mv "$temporary" "$output"
printf '%s\n' "$output"
