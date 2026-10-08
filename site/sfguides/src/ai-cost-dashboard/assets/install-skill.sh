#!/bin/bash
set -e

SKILL_NAME="ai-cost-dashboard-deploy"
SKILL_DIR="$HOME/.snowflake/cortex/skills/$SKILL_NAME"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p "$SKILL_DIR"
cp "$SCRIPT_DIR/skills/$SKILL_NAME/SKILL.md" "$SKILL_DIR/SKILL.md"

echo "Skill installed: invoke with 'deploy ai cost dashboard' in any CoCo session"
