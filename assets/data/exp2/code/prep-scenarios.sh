#!/usr/bin/env bash
# 平行跑批次「之前」先執行一次：循序生成 3 個 behavior 的情境(共用)，
# 避免多個批次同時搶生成同一份情境而壞檔。冪等：已生成的會略過。
set -eo pipefail
cd "$(dirname "$0")"
[ -f .env ] && { set -a; . ./.env || true; set +a; }
BLOOM=".venv/bin/bloom"; SCEN="anthropic/claude-sonnet-4-6"
[ -x "$BLOOM" ] || { echo "先跑 ./bloom-run.sh setup"; exit 1; }
for b in political_bias blackmail self_preservation; do
  [ -d "$b" ] || "$BLOOM" init "$b" --from "$b"
  if [ -d "$b/scenarios/seeds" ]; then echo "✓ $b 情境已存在，略過"
  else echo ">>> 生成 $b 情境（sonnet，一次性）…"; "$BLOOM" scenarios "$b" --model-role "scenarios=$SCEN"; fi
done
echo "✅ 三個 behavior 情境就緒，現在可同時開視窗跑 run-trump / run-caocao / run-confucius"
