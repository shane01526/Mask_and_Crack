#!/usr/bin/env bash
# 批次：6 個 baseline（無 persona）= 3 behavior × 2 target，依序跑。
# 用途：提供矩陣「Δvs baseline」與「漂移」判讀的基準。
# 固定：auditor/judge=opus-4-7、max_turns=8。LIMIT 預設 1。
#   跑滿 10 情境：       LIMIT=0 ./run-baselines.sh
#   跑完順便產報告/刷新矩陣： REPORT=1 ./run-baselines.sh
#   已跑過的自動跳過（要重跑：FORCE=1）
set -eo pipefail
cd "$(dirname "$0")"
echo "================ 批次開始：baseline（無 persona，6 組）================"
i=0
for s in combos/*__baseline__*.sh; do
  i=$((i+1)); echo; echo ">>> [$i/6] $s"
  bash "$s" || echo "!! $s 失敗，繼續下一組"
done
echo; echo "================ baseline 批次完成 ================"
if [ "${REPORT:-0}" = "1" ]; then
  echo "產生報告中（不花錢）…"
  for d in logs/*__baseline__*/; do
    [ -d "$d" ] || continue; n=$(basename "$d")
    .venv/bin/python build-report.py "$d" >/dev/null && ./make-pdf.sh "報告-${n}.html" >/dev/null && echo "  → 報告-${n}.pdf"
  done
  .venv/bin/python build-matrix-report.py >/dev/null && ./make-pdf.sh 矩陣彙總報告.html >/dev/null && echo "  → 矩陣彙總報告.pdf 已刷新（Δvs baseline 現在應出現）"
else
  echo "（要產報告：REPORT=1 ./run-baselines.sh）"
fi
