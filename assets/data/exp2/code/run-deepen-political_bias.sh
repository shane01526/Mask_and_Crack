#!/usr/bin/env bash
# 加深：political_bias 的 6 個關鍵格子，各跑滿 10 個情境 (n=10)。
# 關鍵格 = {baseline, trump, caocao} × {minimax, sonnet}
# 固定：auditor/judge=opus-4-7、max_turns=8。會先把舊 n=1 log 封存到 logs/_archive_n1/。
#   跑完順便產報告/刷新矩陣： REPORT=1 ./run-deepen-political_bias.sh
set -eo pipefail
cd "$(dirname "$0")"
CELLS="political_bias__baseline__minimax political_bias__baseline__sonnet \
       political_bias__trump__minimax    political_bias__trump__sonnet \
       political_bias__caocao__minimax   political_bias__caocao__sonnet"
mkdir -p logs/_archive_n1
echo "================ 加深 political_bias 6 關鍵格 → n=10 ================"
i=0
for c in $CELLS; do
  i=$((i+1)); echo; echo ">>> [$i/6] $c  (LIMIT=0 → 跑滿 10 情境)"
  # 把舊 n=1 結果移到封存，確保該格重跑後只留 n=10
  if ls "logs/$c"/*.eval >/dev/null 2>&1; then
    mv "logs/$c"/*.eval logs/_archive_n1/ 2>/dev/null && echo "  (舊 n=1 log 已封存 → logs/_archive_n1/)"
  fi
  LIMIT=0 bash "combos/$c.sh"
done
echo; echo "================ 6 格加深完成（n=10）================"
if [ "${REPORT:-0}" = "1" ]; then
  echo "產生報告中（不花錢）…"
  for c in $CELLS; do
    [ -d "logs/$c" ] || continue
    .venv/bin/python build-report.py "logs/$c/" >/dev/null && ./make-pdf.sh "報告-$c.html" >/dev/null && echo "  → 報告-$c.pdf"
  done
  .venv/bin/python build-matrix-report.py >/dev/null && ./make-pdf.sh 矩陣彙總報告.html >/dev/null && echo "  → 矩陣彙總報告.pdf 已刷新（這 6 格為 n=10 平均）"
else
  echo "（要產報告：REPORT=1 ./run-deepen-political_bias.sh）"
fi
