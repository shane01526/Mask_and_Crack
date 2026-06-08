#!/usr/bin/env bash
# 組合(baseline,無persona): behavior=blackmail  target=minimax  (auditor/judge=opus-4-7, max_turns=8)
export BEHAVIOR_BASE="blackmail"
export PERSONA=""
export TARGET_MODEL="openai-api/minimax/MiniMax-M2.7"
export TARGET_TAG="minimax"
export MAX_TURNS=8
exec "$(dirname "$0")/../run-combo.sh"
