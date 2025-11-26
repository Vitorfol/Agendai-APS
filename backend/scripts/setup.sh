#!/usr/bin/env bash
set -euo pipefail

# setup_db.sh - convenience script to (optionally) drop volumes, bring services up,
# run alembic migrations and populate the DB.
# Usage:
#  ./scripts/setup_db.sh         # default: down -v, up -d, alembic upgrade head, populate
#  ./scripts/setup_db.sh --no-down    # skip docker compose down -v
#  ./scripts/setup_db.sh --no-populate # skip running popule.py
#  ./scripts/setup_db.sh --help

DO_DOWN=true
DO_UP=true
DO_ALEMBIC=true
DO_POPULATE=true
DO_GIT_PULL=true

usage() {
  cat <<EOF
Usage: $0 [options]

Options:
  --no-down        don't run 'docker compose down -v' (skip dropping volumes)
  --no-up          don't run 'docker compose up -d' (skip starting services)
  --no-alembic     don't run alembic upgrade head
  --no-populate    don't run the seed/popule script
  --git-pull       run 'git pull --ff-only' in the backend repo before any actions (default: enabled)
  --no-git-pull    disable automatic git pull (opt-out)
  -h, --help       show this help

Examples:
  # full reset (drop volumes, start services, apply migrations, populate DB)
  $0

  # keep existing volumes, just apply migrations and populate
  $0 --no-down
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-down) DO_DOWN=false; shift ;;
    --no-up) DO_UP=false; shift ;;
    --no-alembic) DO_ALEMBIC=false; shift ;;
    --no-populate) DO_POPULATE=false; shift ;;
  --git-pull) DO_GIT_PULL=true; shift ;;
  --no-git-pull) DO_GIT_PULL=false; shift ;;
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
if [ "$DO_GIT_PULL" = true ]; then
  echo "[setup_db] Git pull requested. Checking for uncommitted changes..."
  if [ -n "$(git -C "$REPO_ROOT" status --porcelain)" ]; then
    echo "[setup_db] Uncommitted changes detected in $REPO_ROOT. Please commit or stash before running --git-pull." >&2
    exit 1
  fi
  echo "[setup_db] Running: git -C \"$REPO_ROOT\" pull --ff-only"
  git -C "$REPO_ROOT" pull --ff-only
fi

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
      echo "[setup_db] DB is available (mysqladmin ping succeeded)"
      return 0
    fi

    # Fallback: try an active TCP connect from the backend container (less preferred).
    if docker compose exec -T backend sh -c "python - <<'PY'\nimport socket,sys\ntry:\n s=socket.create_connection(('db',3306),timeout=1); s.close(); print('ok'); sys.exit(0)\nexcept Exception:\n sys.exit(1)\nPY" 2>/dev/null; then
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

if [ "$DO_POPULATE" = true ]; then
  echo "[setup_db] Populating database: python src/database/popule.py"
  docker compose exec backend python src/database/popule.py
fi

echo "[setup_db] Done."
