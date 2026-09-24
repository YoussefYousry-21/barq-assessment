# BARQ DevOps assessment

A Flask API runs behind NGINX with PostgreSQL and Redis. The current pre-video setup has two app instances and publishes only NGINX at `127.0.0.1:8080`. The recorded challenge will change the final setup to three instances on port 8090.

## Requirements

Linux/WSL2, Git, Python 3, Docker Engine and Docker Compose. Run commands from the repository root. Keep `.env` and database dumps out of Git.

## First-time setup

```bash
cp .env.example .env
python3 - <<'PY'
import secrets
from pathlib import Path
path = Path(".env")
path.write_text(path.read_text().replace(
    "replace-with-a-long-random-password", secrets.token_hex(24)
))
PY
chmod 600 .env
docker compose -p barq-assessment config --quiet
