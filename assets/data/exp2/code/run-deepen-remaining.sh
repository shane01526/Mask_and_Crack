#!/usr/bin/env bash
# 補跑：political_bias 4 個 persona 關鍵格(上次撞 API 額度而 error)。各跑滿 10 情境。
# 先決條件：Anthropic API 額度已恢復(6/01)或已在 Console 調高上限。
#   產報告/刷新矩陣： REPORT=1 ./run-deepen-remaining.sh
set -eo pipefail
cd "$(dirname "$0")"
CELLS="political_bias__trump__minimax  political_bias__trump__sonnet \
       political_bias__caocao__minimax political_bias__caocao__sonnet"
mkdir -p logs/_archive_errors
echo "================ 補跑 4 個 persona 關鍵格 → n=10 ================"
i=0
for c in $CELLS; do
  i=$((i+1)); echo; echo ">>> [$i/4] $c"
  # 清掉上次 error 的 log（移到封存），確保重跑乾淨
  if ls "logs/$c"/*.eval >/dev/null 2>&1; then
    mv "logs/$c"/*.eval logs/_archive_errors/ 2>/dev/null && echo "  (舊 error log 已封存)"
  fi
  LIMIT=0 bash "combos/$c.sh"
done
echo; echo "================ 補跑完成 ================"
if [ "${REPORT:-0}" = "1" ]; then
  for c in $CELLS; do
    [ -d "logs/$c" ] && .venv/bin/python build-report.py "logs/$c/" >/dev/null && ./make-pdf.sh "報告-$c.html" >/dev/null && echo "  → 報告-$c.pdf"
  done
  .venv/bin/python build-matrix-report.py >/dev/null && ./make-pdf.sh 矩陣彙總報告.html >/dev/null && echo "  → 矩陣已刷新"
fi
