#!/usr/bin/env bash
# Installa il gate golden-master come hook GLOBALE sulla macchina locale (Mac).
#
# Cosa fa: fonde uno Stop hook nel tuo ~/.claude/settings.json. L'hook e
# difensivo — in ogni progetto che NON contiene .claude/verify.sh esce subito
# senza fare nulla, quindi e sicuro tenerlo globale. Dove esiste un verify.sh
# (come in questo repo) il semaforo rosso blocca il completamento del task.
#
# Idempotente: rilanciarlo non crea duplicati.
#
# Uso (dal tuo Mac):  bash .claude/install-global-gate.sh
set -euo pipefail

SETTINGS="${1:-$HOME/.claude/settings.json}"
mkdir -p "$(dirname "$SETTINGS")"
[ -f "$SETTINGS" ] || echo '{}' > "$SETTINGS"

python3 - "$SETTINGS" <<'PY'
import json, sys

path = sys.argv[1]
with open(path) as f:
    cfg = json.load(f) or {}

CMD = (
    'dir="${CLAUDE_PROJECT_DIR:-$PWD}"; v="$dir/.claude/verify.sh"; '
    '[ -f "$v" ] || exit 0; bash "$v" >/tmp/claude-verify.log 2>&1 && exit 0; '
    'echo "{\\"decision\\":\\"block\\",\\"reason\\":\\"Golden-master verify '
    'FALLITO (semaforo rosso). Esegui .claude/verify.sh, leggi '
    '/tmp/claude-verify.log e correggi finche non passa, poi fermati.\\"}"'
)
ENTRY = {"hooks": [{"type": "command", "command": CMD,
                    "statusMessage": "Verifica golden-master carosello..."}]}

hooks = cfg.setdefault("hooks", {})
stop = hooks.setdefault("Stop", [])

# evita duplicati: rimuovi ogni Stop hook che invoca lo stesso verify.sh
def is_ours(group):
    return any(".claude/verify.sh" in h.get("command", "")
               for h in group.get("hooks", []))
stop[:] = [g for g in stop if not is_ours(g)]
stop.append(ENTRY)

with open(path, "w") as f:
    json.dump(cfg, f, indent=2, ensure_ascii=False)
    f.write("\n")
print(f"OK: gate golden-master installato in {path}")
PY

echo
echo "Fatto. Riavvia Claude Code perche l'hook venga registrato."
echo "Il gate si attiva solo nei progetti con .claude/verify.sh; altrove e inerte."
