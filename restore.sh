#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "Usage: ./restore.sh BACKUP.dump barq_restore_NAME" >&2
  exit 2
fi

backup="$1"
target="$2"

if [[ ! -f "$backup" || ! "$target" =~ ^barq_restore_[a-z0-9_]+$ ]]; then
  echo "Backup file missing or invalid test database name" >&2
  exit 2
fi

# Check the archive before creating the destination database.
docker exec -i postgres pg_restore -l < "$backup" > /dev/null
docker exec postgres createdb -U barq_app "$target"
docker exec -i postgres pg_restore -U barq_app -d "$target" \
  --no-owner --no-privileges < "$backup"
printf 'Restored %s into %s\n' "$backup" "$target"
