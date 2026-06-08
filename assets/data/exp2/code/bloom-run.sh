#!/usr/bin/env bash
# =============================================================================
# Petri Bloom Runner — 全 API 版
# 把 Petri Bloom 的 setup → init → scenarios → eval → view 包成一支 shell。
# 詳見 README.md。 用法: ./bloom-run.sh help
# =============================================================================
set -eo pipefail   # 注意: 不用 -u，避免任何 config 變數缺失就整支爆 "unbound variable"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 載入 .env（金鑰）與 config.sh（設定）。沒讀到也不致命，下方有內建後備。
if [ -f "$SCRIPT_DIR/.env" ]; then set -a; . "$SCRIPT_DIR/.env" || true; set +a; fi
if [ -f "$SCRIPT_DIR/config.sh" ]; then . "$SCRIPT_DIR/config.sh" || true; fi

# 內建後備預設：即使 config.sh 沒成功載入，也用「目前指定的設定」確保能跑。
: "${BEHAVIOR:=political_bias}"
: "${INIT_FROM:=$BEHAVIOR}"
: "${MODEL_SCENARIOS:=anthropic/claude-sonnet-4-6}"
: "${MODEL_AUDITOR:=anthropic/claude-opus-4-7}"
: "${MODEL_TARGET:=openai-api/minimax/MiniMax-M2.7}"
: "${MODEL_JUDGE:=anthropic/claude-opus-4-7}"
: "${MAX_TURNS:=8}"
: "${VENV_DIR:=$SCRIPT_DIR/.venv}"

BLOOM="$VENV_DIR/bin/bloom"
INSPECT="$VENV_DIR/bin/inspect"

log() { printf '\033[1;36m[bloom-run]\033[0m %s\n' "$*"; }
err() { printf '\033[1;31m[bloom-run 錯誤]\033[0m %s\n' "$*" >&2; }
die() { err "$*"; exit 1; }

require_bin() {
  [ -x "$BLOOM" ]   || die "找不到 $BLOOM。請先執行: ./bloom-run.sh setup"
  [ -x "$INSPECT" ] || die "找不到 $INSPECT。請先執行: ./bloom-run.sh setup"
}
require_key() {
  [ -n "${ANTHROPIC_API_KEY:-}" ] || \
    die "ANTHROPIC_API_KEY 未設定。請: cp .env.example .env 再填入金鑰。"
}

# ---- 指令 -------------------------------------------------------------------

cmd_setup() {
  command -v uv >/dev/null 2>&1 || die "找不到 uv，請先安裝 uv (https://docs.astral.sh/uv/)。"
  log "用 uv 建立 Python 3.12 虛擬環境: $VENV_DIR"
  uv venv "$VENV_DIR" --python 3.12
  log "安裝 petri-bloom（含 inspect-ai / inspect-petri）…"
  uv pip install --python "$VENV_DIR/bin/python" petri-bloom
  require_bin
  log "完成 ✓  bloom: $("$BLOOM" --version 2>&1 | head -1 || echo '?')"
  log "下一步: cp .env.example .env → 填入 ANTHROPIC_API_KEY → ./bloom-run.sh all --limit 1"
}

cmd_init() {
  require_bin
  if [ -d "$SCRIPT_DIR/$BEHAVIOR" ]; then
    log "行為目錄已存在: $BEHAVIOR（略過 init）"
  elif [ -n "$INIT_FROM" ]; then
    log "bloom init $BEHAVIOR --from $INIT_FROM（複製內建/來源定義）"
    "$BLOOM" init "$BEHAVIOR" --from "$INIT_FROM"
  else
    log "bloom init $BEHAVIOR（空白模板，需自行撰寫 BEHAVIOR.md）"
    "$BLOOM" init "$BEHAVIOR"
  fi
}

cmd_scenarios() {
  require_bin; require_key
  local overwrite="${1:-}"
  [ -d "$SCRIPT_DIR/$BEHAVIOR" ] || cmd_init
  if [ -d "$SCRIPT_DIR/$BEHAVIOR/scenarios/seeds" ] && [ "$overwrite" != "--overwrite" ]; then
    log "情境已生成（scenarios/seeds 存在）。要重生請: ./bloom-run.sh scenarios --overwrite"
    return 0
  fi
  log "bloom scenarios ./$BEHAVIOR  (scenarios 模型=$MODEL_SCENARIOS)"
  "$BLOOM" scenarios "./$BEHAVIOR" \
    --model-role "scenarios=$MODEL_SCENARIOS" \
    ${overwrite:+$overwrite}
}

cmd_eval() {
  require_bin; require_key
  [ -d "$SCRIPT_DIR/$BEHAVIOR/scenarios/seeds" ] || \
    die "尚未生成情境。請先: ./bloom-run.sh scenarios"
  log "inspect eval  auditor=$MODEL_AUDITOR  target=$MODEL_TARGET  judge=$MODEL_JUDGE  max_turns=$MAX_TURNS"
  log "省錢提示: 第一次加 --limit 1 只跑 1 個 scenario，用真實 token 數驗證成本。"
  "$INSPECT" eval petri_bloom/bloom_audit \
    -T "behavior=./$BEHAVIOR" \
    -T "max_turns=$MAX_TURNS" \
    --model-role "auditor=$MODEL_AUDITOR" \
    --model-role "target=$MODEL_TARGET" \
    --model-role "judge=$MODEL_JUDGE" \
    "$@"
  log "完成 ✓  log 在 ./logs。看結果: ./bloom-run.sh view"
}

cmd_view() {
  require_bin
  log "啟動 inspect view（用瀏覽器看分數與 transcript）…"
  "$INSPECT" view
}

cmd_all() {
  cmd_init
  cmd_scenarios
  cmd_eval "$@"
}

cmd_doctor() {
  echo "── Petri Bloom Runner 診斷 ──"
  echo "bash       : $BASH_VERSION"
  echo "SCRIPT_DIR : $SCRIPT_DIR"
  echo "config.sh  : $([ -f "$SCRIPT_DIR/config.sh" ] && echo 存在 || echo 缺少)"
  echo ".env       : $([ -f "$SCRIPT_DIR/.env" ] && echo 存在 || echo 缺少)"
  echo "解析後設定:"
  echo "  BEHAVIOR  = ${BEHAVIOR:-<空>}"
  echo "  INIT_FROM = ${INIT_FROM:-<空>}"
  echo "  scenarios = ${MODEL_SCENARIOS:-<空>}"
  echo "  auditor   = ${MODEL_AUDITOR:-<空>}"
  echo "  target    = ${MODEL_TARGET:-<空>}"
  echo "  judge     = ${MODEL_JUDGE:-<空>}"
  echo "  max_turns = ${MAX_TURNS:-<空>}"
  echo "venv bloom : $([ -x "$BLOOM" ] && echo 在 || echo 缺少 — 先跑 setup)"
  echo "venv inspect: $([ -x "$INSPECT" ] && echo 在 || echo 缺少)"
  echo "金鑰(僅看有無，不顯示內容):"
  echo "  ANTHROPIC_API_KEY = $([ -n "${ANTHROPIC_API_KEY:-}" ] && echo 已設 || echo 未設)"
  echo "  MINIMAX_API_KEY   = $([ -n "${MINIMAX_API_KEY:-}" ] && echo 已設 || echo 未設)"
  echo "  MINIMAX_BASE_URL  = ${MINIMAX_BASE_URL:-<空>}"
}

usage() {
  cat <<EOF
Petri Bloom Runner — 全 API 版

用法: ./bloom-run.sh <指令> [選項]

指令:
  setup                    一次性: uv 建 py3.12 venv 並安裝 petri-bloom
  init                     bloom init <BEHAVIOR>（建立行為目錄）
  scenarios [--overwrite]  生成情境 (understanding + ideation)
  eval [inspect 選項]      跑評估; 例: ./bloom-run.sh eval --limit 1
  view                     開 inspect view 看結果
  all  [inspect 選項]      init → scenarios → eval 一條龍
  doctor                   診斷: 印出環境/設定/金鑰狀態(不顯示金鑰內容)
  help                     顯示本說明

目前設定（改 config.sh，或用環境變數覆寫）:
  BEHAVIOR  = $BEHAVIOR
  auditor   = $MODEL_AUDITOR
  target    = $MODEL_TARGET
  judge     = $MODEL_JUDGE
  max_turns = $MAX_TURNS

建議首次流程:
  1) ./bloom-run.sh setup
  2) cp .env.example .env   # 然後填入 ANTHROPIC_API_KEY
  3) ./bloom-run.sh all --limit 1   # 只跑 1 個 scenario，看真實成本
  4) ./bloom-run.sh eval            # 滿意後跑完整 10 個
  5) ./bloom-run.sh view
EOF
}

main() {
  local cmd="${1:-help}"; shift || true
  case "$cmd" in
    setup)     cmd_setup ;;
    init)      cmd_init ;;
    scenarios) cmd_scenarios "${1:-}" ;;
    eval)      cmd_eval "$@" ;;
    view)      cmd_view ;;
    all)       cmd_all "$@" ;;
    doctor)    cmd_doctor ;;
    help|-h|--help) usage ;;
    *) err "未知指令: $cmd"; echo; usage; exit 1 ;;
  esac
}
main "$@"
