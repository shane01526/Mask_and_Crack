#!/usr/bin/env bash
# 批次：曹操（persona=caocao）的 6 個組合 = 3 behavior × 2 target，依序跑。
# 固定：auditor/judge=opus-4-7、max_turns=8。LIMIT 預設 1（每組只評 1 情境）。
#   跑滿 10 情境：   LIMIT=0 ./run-caocao.sh
#   順便產報告/刷新矩陣： REPORT=1 ./run-caocao.sh
set -eo pipefail
cd "$(dirname "$0")"
P=caocao
echo "================ 批次開始：曹操（persona=$P，6 組）================"
i=0
for s in combos/*__${P}__*.sh; do
  i=$((i+1)); echo; echo ">>> [$i/6] $s"
  bash "$s" || echo "!! $s 失敗，繼續下一組"
done
echo; echo "================ 曹操 批次完成 ================"
if [ "${REPORT:-0}" = "1" ]; then
  echo "產生報告中（不花錢）…"
  for d in logs/*__${P}__*/; do
    [ -d "$d" ] || continue; n=$(basename "$d")
    .venv/bin/python build-report.py "$d" >/dev/null && ./make-pdf.sh "報告-${n}.html" >/dev/null && echo "  → 報告-${n}.pdf"
  done
  .venv/bin/python build-matrix-report.py >/dev/null && ./make-pdf.sh 矩陣彙總報告.html >/dev/null && echo "  → 矩陣彙總報告.pdf 已刷新"
else
  echo "（要產報告：REPORT=1 ./run-caocao.sh，或事後手動 build-report.py）"
fi
