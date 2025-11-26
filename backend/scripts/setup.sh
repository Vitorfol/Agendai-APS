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

if [ "$DO_ALEMBIC" = true ]; then
  echo "[setup_db] Applying migrations: alembic upgrade head"
  docker compose exec backend python -m alembic -c alembic.ini upgrade head
fi

if [ "$DO_POPULATE" = true ]; then
  echo "[setup_db] Populating database: python src/database/popule.py"
  docker compose exec backend python src/database/popule.py
fi

echo "[setup_db] Done."
