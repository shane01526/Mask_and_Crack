# =============================================================================
# Petri Bloom Runner — 設定檔（可編輯）
# 改這裡即可，不必動 bloom-run.sh。也可用環境變數臨時覆寫，例如:
#   BEHAVIOR=flattery ./bloom-run.sh all
# =============================================================================

# 要評估的「行為」(內建 21 種之一，或你自訂的目錄名)
# 內建例: delusion_sycophancy flattery emotional_bond defer_to_users
#         increasing_pep contextual_optimism blackmail ...
# 註: 想走「混合/訂閱 target」必須是 conversation 模式行為; 但本版是全 API，無此限制。
BEHAVIOR="${BEHAVIOR:-political_bias}"

# init 要從哪裡複製行為定義: 內建名稱 / 本地路徑 / git URL。
# 預設 = 跟 BEHAVIOR 同名的內建定義(帶出真實描述+範例)。
# 要自己從零寫一個全新行為,把它設成空字串: INIT_FROM=""
INIT_FROM="${INIT_FROM:-$BEHAVIOR}"

# -----------------------------------------------------------------------------
# 模型角色 — 全部用 Anthropic ⇒ 只需要一把 ANTHROPIC_API_KEY
#   scenarios: 生成情境(一次性)   auditor: 稽核者(成本大宗)
#   target:    受測模型           judge:   評審(靠 answer() tool，必須走 API)
# 模型字串沿用 Petri 官方文件的已知可用值 (claude-sonnet-4-6)。
# -----------------------------------------------------------------------------
MODEL_SCENARIOS="${MODEL_SCENARIOS:-anthropic/claude-sonnet-4-6}"
MODEL_AUDITOR="${MODEL_AUDITOR:-anthropic/claude-opus-4-7}"
MODEL_TARGET="${MODEL_TARGET:-openai-api/minimax/MiniMax-M2.7}"   # MiniMax-M2.7(MiniMax 無 4.7 版,實測 400); 要改回 Anthropic 換成 anthropic/claude-sonnet-4-6
MODEL_JUDGE="${MODEL_JUDGE:-anthropic/claude-opus-4-7}"
# 想要更強的評審(成本較高)可改成最新 Opus:
#   MODEL_JUDGE=anthropic/claude-opus-4-8
# 想讓 target 便宜些可改:
#   MODEL_TARGET=anthropic/claude-haiku-4-5
#
# 想評估「非 Anthropic」模型 — 例如 MiniMax-M2.7（OpenAI 相容第三方）:
#   1) 取消註解下一行（會蓋掉上面的 target 預設）
#   2) 到 .env 取消註解 MINIMAX_API_KEY / MINIMAX_BASE_URL 並填值
#   格式 = openai-api/<供應商名>/<模型ID>；minimax 對應 .env 的 MINIMAX_* 變數
# MODEL_TARGET="${MODEL_TARGET:-openai-api/minimax/MiniMax-M2.7}"
#   注意: agent 模式行為需 target 回 tool call，MiniMax 支援但請先 --limit 1 實測;
#         auditor / judge 維持 anthropic 不要改（需穩定 tool calling）。

# -----------------------------------------------------------------------------
# 稽核者每個 scenario 的最大回合數 (bloom_audit 原廠預設 15)
#   越大 = 誘導更徹底但更貴; 越小 = 便宜快速但可能誘不出行為
#   建議: 首次驗證用 10; 正式評估用 15(預設); 難誘的複雜行為才上 20
# -----------------------------------------------------------------------------
MAX_TURNS="${MAX_TURNS:-8}"

# uv 建立的 Python 3.12 虛擬環境位置
VENV_DIR="${VENV_DIR:-$SCRIPT_DIR/.venv}"
