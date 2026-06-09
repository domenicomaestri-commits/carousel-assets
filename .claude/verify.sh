#!/usr/bin/env bash
# Golden-master gate for the carousel skill.
# Renders the baseline spec and compares it (tolerantly) to the frozen
# reference. Exit 0 = green, non-zero = red. The global/project Stop hook
# blocks completion while this is red.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILL="$REPO/.claude/skills/carousel"

# nothing to verify if the skill isn't present
[ -f "$SKILL/render.py" ] || { echo "carousel skill not present — skip"; exit 0; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

python3 "$SKILL/render.py" "$SKILL/specs/pre-chorus-vs-chorus.json" --out "$TMP" >/dev/null
python3 "$SKILL/tests/compare.py" "$TMP" "$SKILL/tests/reference"
