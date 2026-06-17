#! /bin/bash

set -euo pipefail

CMD="${1-}"
BRANCH_NAME="${2-}"

if [ -z "$CMD" ]; then
echo "Usage: $0 create <branch-name> | $0 plan|deploy|destroy"
exit 1
fi

# Ensure we're operating from the repo root
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || true)
if [ -z "$REPO_ROOT" ]; then
echo "Error: Not inside a git repository."
exit 1
fi

case "$CMD" in
create)
# Require explicit branch name for create
if [ -z "$BRANCH_NAME" ]; then
echo "Usage: $0 create <branch-name>"
exit 1
fi
SANITIZED_NAME=$(echo ${BRANCH_NAME//-/_} | tr '[:lower:]' '[:upper:]')
# Sync local develop with origin/develop
git fetch origin --prune
git checkout develop
git reset --hard origin/develop

# Create the sandbox branch from develop
git checkout -B "$BRANCH_NAME"
echo "Created and switched to branch '$BRANCH_NAME' from up-to-date develop."

# Create a virtual environment and install dependencies
virtualenv -p python3 venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

snow connection test

snow stage create ${SANITIZED_NAME}_FILES
snow sql -q "CREATE DCM PROJECT IF NOT EXISTS ${SANITIZED_NAME};"
snow sql -q "CREATE OR REPLACE DATABASE ${SANITIZED_NAME};"
snow sql -q "CREATE OR REPLACE SCHEMA ${SANITIZED_NAME}.${SANITIZED_NAME} CLONE GOLD.GOLD;"

;;
plan)
# Activate venv if present
if [ -f "venv/bin/activate" ]; then
source venv/bin/activate
fi

BRANCH_NAME=$(git -C "$REPO_ROOT" rev-parse --abbrev-ref HEAD)
SANITIZED_NAME=$(echo ${BRANCH_NAME//-/_} | tr '[:lower:]' '[:upper:]')

pushd $REPO_ROOT
# added remove , when a .sql file is removed from data_project, stage copy does not remove it
snow sql -q "CREATE OR REPLACE STAGE ${SANITIZED_NAME}_FILES"
snow stage copy --recursive ./data_project @${SANITIZED_NAME}_FILES/
snow sql -q "EXECUTE DCM PROJECT ${SANITIZED_NAME} PLAN USING CONFIGURATION prod (target_db => '${SANITIZED_NAME}', target_schema => '${SANITIZED_NAME}') FROM @${SANITIZED_NAME}_FILES/;"
popd

;;
deploy)
# Activate venv if present
if [ -f "venv/bin/activate" ]; then
source venv/bin/activate
fi

BRANCH_NAME=$(git -C "$REPO_ROOT" rev-parse --abbrev-ref HEAD)
SANITIZED_NAME=$(echo ${BRANCH_NAME//-/_} | tr '[:lower:]' '[:upper:]')

pushd $REPO_ROOT
snow sql -q "CREATE OR REPLACE STAGE ${SANITIZED_NAME}_FILES"
snow stage copy --recursive ./data_project @${SANITIZED_NAME}_FILES/

snow sql -q "EXECUTE DCM PROJECT ${SANITIZED_NAME} DEPLOY USING CONFIGURATION prod (target_db => '${SANITIZED_NAME}', target_schema => '${SANITIZED_NAME}') FROM @${SANITIZED_NAME}_FILES/;"
popd

;;
destroy)
# Activate venv if present
if [ -f "venv/bin/activate" ]; then
source venv/bin/activate
fi

BRANCH_NAME=$(git -C "$REPO_ROOT" rev-parse --abbrev-ref HEAD)
SANITIZED_NAME=$(echo ${BRANCH_NAME//-/_} | tr '[:lower:]' '[:upper:]')

snow sql -q "DROP STAGE IF EXISTS ${SANITIZED_NAME}_FILES"
snow sql -q "DROP DCM PROJECT IF EXISTS ${SANITIZED_NAME}"
snow sql -q "DROP DATABASE IF EXISTS ${SANITIZED_NAME}"

;;
*)
echo "Unknown command: $CMD"
echo "Usage: $0 create <branch-name> | $0 plan|deploy|destroy"
exit 1
;;
esac