#!/usr/bin/env bash
# 組合(baseline,無persona): behavior=self_preservation  target=sonnet  (auditor/judge=opus-4-7, max_turns=8)
export BEHAVIOR_BASE="self_preservation"
export PERSONA=""
export TARGET_MODEL="anthropic/claude-sonnet-4-6"
export TARGET_TAG="sonnet"
export MAX_TURNS=8
exec "$(dirname "$0")/../run-combo.sh"
