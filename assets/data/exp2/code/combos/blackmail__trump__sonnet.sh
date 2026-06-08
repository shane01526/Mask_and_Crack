#!/usr/bin/env bash
# 組合: behavior=blackmail  persona=trump  target=sonnet
# 固定: auditor/judge=opus-4-7, max_turns=8, LIMIT 預設 1(設 LIMIT=0 跑全部 10 個)
export BEHAVIOR_BASE="blackmail"
export PERSONA="trump"
export TARGET_MODEL="anthropic/claude-sonnet-4-6"
export TARGET_TAG="sonnet"
export MAX_TURNS=8
exec "$(dirname "$0")/../run-combo.sh"
