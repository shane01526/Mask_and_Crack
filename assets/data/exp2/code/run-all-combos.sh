#!/usr/bin/env bash
# 依序跑 combos/ 下全部 18 支。LIMIT 沿用各腳本(預設1)；可整批覆寫: LIMIT=0 ./run-all-combos.sh
set -eo pipefail
cd "$(dirname "$0")"
for s in combos/*.sh; do
  echo; echo "================ $s ================"
  bash "$s" || echo "!! $s 失敗，繼續下一支"
done
echo; echo "全部完成。各組合結果在 logs/<behavior>__<persona>__<target>/"
