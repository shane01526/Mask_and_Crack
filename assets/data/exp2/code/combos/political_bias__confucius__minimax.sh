#!/usr/bin/env bash
# 組合: behavior=political_bias  persona=confucius  target=minimax
# 固定: auditor/judge=opus-4-7, max_turns=8, LIMIT 預設 1(設 LIMIT=0 跑全部 10 個)
export BEHAVIOR_BASE="political_bias"
export PERSONA="confucius"
export TARGET_MODEL="openai-api/minimax/MiniMax-M2.7"
export TARGET_TAG="minimax"
export MAX_TURNS=8
exec "$(dirname "$0")/../run-combo.sh"
