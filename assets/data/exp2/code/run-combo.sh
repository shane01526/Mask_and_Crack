#!/usr/bin/env bash
# 共用引擎 — 被 combos/*.sh 以環境變數呼叫，跑「一個」組合。
#   必需: BEHAVIOR_BASE  TARGET_MODEL  TARGET_TAG
#   選用: PERSONA(空=baseline)  MAX_TURNS(預設8)  LIMIT(預設1; 設 0 跑全部 scenario)
# 固定: auditor=judge=opus-4-7, scenarios 生成用 sonnet-4-6(一次性、共用)
set -eo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
[ -f .env ] && { set -a; . ./.env || true; set +a; }

VENV="$ROOT/.venv"; BLOOM="$VENV/bin/bloom"; INSPECT="$VENV/bin/inspect"
[ -x "$BLOOM" ]   || { echo "找不到 $BLOOM，請先 ./bloom-run.sh setup"; exit 1; }
[ -n "${ANTHROPIC_API_KEY:-}" ] || { echo "ANTHROPIC_API_KEY 未設(.env)"; exit 1; }

AUDITOR="anthropic/claude-opus-4-7"
JUDGE="anthropic/claude-opus-4-7"
SCEN="anthropic/claude-sonnet-4-6"
: "${MAX_TURNS:=8}"
: "${LIMIT:=1}"
: "${BEHAVIOR_BASE:?需設 BEHAVIOR_BASE}"
: "${TARGET_MODEL:?需設 TARGET_MODEL}"
: "${TARGET_TAG:?需設 TARGET_TAG}"
PERSONA="${PERSONA:-}"

log(){ printf '\033[1;36m[combo]\033[0m %s\n' "$*"; }

# 1) baseline 行為 + scenarios（共用、冪等：只第一次生成）
[ -d "$BEHAVIOR_BASE" ] || { log "init $BEHAVIOR_BASE"; "$BLOOM" init "$BEHAVIOR_BASE" --from "$BEHAVIOR_BASE"; }
if [ ! -d "$BEHAVIOR_BASE/scenarios/seeds" ]; then
  log "生成 $BEHAVIOR_BASE 情境(一次性，用 $SCEN)…"
  "$BLOOM" scenarios "$BEHAVIOR_BASE" --model-role "scenarios=$SCEN"
fi

# 2) persona 變體（複製 baseline 的 scenarios + 注入 prefix；冪等）
if [ -n "$PERSONA" ]; then
  VAR="${BEHAVIOR_BASE}__${PERSONA}"
  if [ ! -d "$VAR" ]; then
    log "建立變體 $VAR（複製 scenarios + 注入 $PERSONA prefix）"
    cp -R "$BEHAVIOR_BASE" "$VAR"
    "$VENV/bin/python" inject-prefix.py "$VAR/BEHAVIOR.md" "personas/$PERSONA.md"
  fi
else
  VAR="$BEHAVIOR_BASE"
fi

# 3) eval（每組合獨立 log 目錄）
LOGDIR="logs/${BEHAVIOR_BASE}__${PERSONA:-baseline}__${TARGET_TAG}"
# 防呆：已有 log 就跳過（避免重複花錢）；要強制重跑用 FORCE=1
if [ "${FORCE:-0}" != "1" ] && ls "$LOGDIR"/*.eval >/dev/null 2>&1; then
  log "已有結果，跳過（要重跑: FORCE=1）→ $LOGDIR"
  exit 0
fi
LIMIT_ARG=""; [ "${LIMIT}" != "0" ] && LIMIT_ARG="--limit ${LIMIT}"
log "EVAL behavior=$VAR target=$TARGET_MODEL auditor/judge=opus-4-7 max_turns=$MAX_TURNS limit=${LIMIT}"
"$INSPECT" eval petri_bloom/bloom_audit \
  -T "behavior=./$VAR" -T "max_turns=$MAX_TURNS" \
  --model-role "auditor=$AUDITOR" --model-role "judge=$JUDGE" --model-role "target=$TARGET_MODEL" \
  --log-dir "$LOGDIR" $LIMIT_ARG
log "完成 → $LOGDIR"
