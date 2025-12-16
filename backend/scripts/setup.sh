#!/usr/bin/env bash
set -euo pipefail

# setup_db.sh - convenience script to (optionally) drop volumes, bring services up,
# run alembic migrations and populate the DB.
# Usage:
#  ./scripts/setup_db.sh         # default: down -v, up -d, alembic upgrade head, populate
#  ./scripts/setup_db.sh --no-down    # skip docker compose down -v
#  ./scripts/setup_db.sh --no-populate # skip running popule.py
#  ./scripts/setup_db.sh --help

# By default do NOT drop volumes/containers. Use --down to force destructive reset.
DO_DOWN=false
DO_UP=true
DO_ALEMBIC=true
DO_INIT=false
# Note: automatic git pull removed to avoid unexpected repository changes during setup

usage() {
  cat <<EOF
Usage: $0 [options]

Options:
  --down           run 'docker compose down -v' (destructive reset)
  --no-down        (deprecated) kept for backwards compatibility; previously skipped the down step
  --no-up          don't run 'docker compose up -d' (skip starting services)
  --no-alembic     don't run alembic upgrade head
  --init           initialize database with UECE and courses for presentation
  --no-git-pull    (removed) previously used to auto-pull changes before running setup
  -h, --help       show this help

Examples:
  # full reset (drop volumes, start services, apply migrations)
  $0 --down

  # initialize database with UECE and courses for presentation
  $0 --init

  # keep existing volumes, just apply migrations
  $0
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
  --down) DO_DOWN=true; shift ;;
  --no-down) echo "--no-down is deprecated; use --down to request a destructive reset"; DO_DOWN=false; shift ;;
    --no-up) DO_UP=false; shift ;;
    --no-alembic) DO_ALEMBIC=false; shift ;;
    --init) DO_INIT=true; shift ;;
  --no-git-pull) echo "--no-git-pull is deprecated; this setup script no longer auto-pulls."; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1"; usage; exit 1 ;;
  esac
done

# Ensure we run from repository backend dir when called from project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
REPO_ROOT="${SCRIPT_DIR%/scripts}"
cd "$REPO_ROOT"

# Load .env into the script environment if present so we can use DATABASE_* vars
if [ -f ".env" ]; then
  # shellcheck disable=SC1091
  set -o allexport
  # shellcheck disable=SC1091
  source ".env"
  set +o allexport
fi

# Optionally update repository before starting containers/migrations.

# NOTE: We intentionally do not run 'git pull' here. Updating the repository is a
# manual action to avoid unexpected changes during setup. Callers should run
# 'git pull' themselves if they want to update before running this script.

if [ "$DO_DOWN" = true ]; then
  echo "[setup_db] Running: docker compose down -v"
  docker compose down -v
fi

if [ "$DO_UP" = true ]; then
  echo "[setup_db] Starting services: docker compose up -d"
  docker compose up -d
fi

wait_for_db() {
  # Wait until the 'db' host accepts TCP connections on the configured port.
  # Prefer an active TCP check from the backend container to avoid false positives
  # where the container logs contain a readiness message but the network port
  # is not yet accepting connections.
  echo "[setup_db] Waiting for DB to accept connections..."
  # try for up to 120 seconds
  for i in $(seq 1 120); do
    # Prefer using mysqladmin inside the DB container to verify server readiness.
    if docker compose exec -T db mysqladmin ping -uroot -p"${DATABASE_PASSWORD:-}" --silent 2>/dev/null; then
      echo "[setup_db] DB ping succeeded, waiting extra 3s for full initialization..."
      sleep 3
      echo "[setup_db] DB is available (mysqladmin ping succeeded)"
      return 0
    fi

    # Fallback: try an active TCP connect from the backend container (less preferred).
    if docker compose exec -T backend sh -c "python - <<'PY'\nimport socket,sys\ntry:\n s=socket.create_connection(('db',3306),timeout=1); s.close(); print('ok'); sys.exit(0)\nexcept Exception:\n sys.exit(1)\nPY" 2>/dev/null; then
      echo "[setup_db] TCP check succeeded, waiting extra 3s for full initialization..."
      sleep 3
      echo "[setup_db] DB is available (tcp check from backend succeeded)"
      return 0
    fi

    # If neither succeeded, inspect recent DB logs as a hint but continue retrying.
    if docker compose logs db --tail 50 2>/dev/null | grep -qi "ready for connections"; then
      echo "[setup_db] DB log shows 'ready for connections' but checks still failing; retrying... ($i)"
    fi

    sleep 1
  done
  echo "[setup_db] timeout waiting for DB (120s)" >&2
  return 1
}

if [ "$DO_ALEMBIC" = true ]; then
  echo "[setup_db] Applying migrations: alembic upgrade head"
  # ensure DB is accepting connections before attempting migrations
  if ! wait_for_db; then
    echo "[setup_db] Aborting alembic step because DB did not become available." >&2
    exit 1
  fi

  docker compose exec backend python -m alembic -c alembic.ini upgrade head || {
    echo "[setup_db] alembic reported an error. If it is an auth error, check DATABASE_* vars in .env." >&2
    exit 1
  }
fi

if [ "$DO_INIT" = true ]; then
  echo "[setup_db] Initializing database with UECE and courses..."
  echo "[setup_db] Creating UECE university..."
  docker compose exec backend python scripts/insert_uece.py
  echo "[setup_db] Creating UECE courses..."
  docker compose exec backend python scripts/insert_uece_courses.py
  echo "[setup_db] Creating test users and event base..."
  docker compose exec backend python scripts/insert_users_event_base.py
fi

echo "[setup_db] Done."
