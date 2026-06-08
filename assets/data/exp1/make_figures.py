#!/usr/bin/env python3
"""
make_figures.py — 為「面具與裂縫」誠稿產出 PNG 圖表（K0-K3 + S0/S1 雙軸新版）
輸出 0522/figs/*.png
"""
import csv, json
from pathlib import Path
from collections import Counter, defaultdict
import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams['font.sans-serif'] = ['Arial Unicode MS','PingFang TC','Heiti TC','sans-serif']
matplotlib.rcParams['axes.unicode_minus'] = False
matplotlib.rcParams['font.size'] = 11
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path("/Users/minglu/Documents/Claude/ai期末報告/0522")
FIGS = ROOT / "figs"
FIGS.mkdir(exist_ok=True)

PERSONA_LIST = ["Cao","DT","HK","CC"]
PERSONA_NAME = {"Cao":"曹操 (Cao)","DT":"川普 (DT)","HK":"霍金 (HK)","CC":"孔子 (CC)"}
PERSONA_COLOR = {"Cao":"#7c1d1d","DT":"#1e3a8a","HK":"#14532d","CC":"#92400e"}
SKILL_LIST = ["a","b","c"]
SKILL_DESC = {"a":"a (極簡)","b":"b (完整)","c":"c (變體)"}
SKILL_COLOR = {"a":"#60a5fa","b":"#b91c1c","c":"#d97706"}
MODEL_LIST = ["opus","sonnet","haiku"]
CONV_LIST = ["intro","meta","trap","anach","vuln"]
CONV_LABEL = {"intro":"intro (自我介紹)","meta":"meta (拷問 AI)","trap":"trap (捏造陷阱)","anach":"anach (時代錯置)","vuln":"vuln (脆弱情境)"}

K_ORDER = ["K0","K1","K2","K3"]
K_COLOR = {"K0":"#9ca3af","K1":"#fbbf24","K2":"#f97316","K3":"#dc2626"}
K_LABEL = {"K0":"K0 面具無損","K1":"K1 輕微裂縫","K2":"K2 劇烈破損","K3":"K3 直接移除"}

S_ORDER = ["S1","S0"]
S_COLOR = {"S1":"#10b981","S0":"#dc2626"}
S_LABEL = {"S1":"S1 已轉介","S0":"S0 未轉介"}

# Load data
rows = list(csv.DictReader(open(ROOT/"coding_results.csv", encoding="utf-8")))
trap_rows = list(csv.DictReader(open(ROOT/"coding_trap_fabrication.csv", encoding="utf-8")))

# ============================================================
# Fig 1: K0-K3 整體分佈（4 persona stacked bar，K4 已抽離）
# ============================================================
fig, ax = plt.subplots(figsize=(8.5, 5))
x = np.arange(len(PERSONA_LIST))
bottoms = np.zeros(len(PERSONA_LIST))
for k in K_ORDER:
    vals = []
    for p in PERSONA_LIST:
        rs = [r for r in rows if r["persona"]==p]
        cnt = sum(1 for r in rs if r["K"]==k)
        vals.append(cnt/len(rs)*100 if rs else 0)
    bars = ax.bar(x, vals, bottom=bottoms, label=K_LABEL[k], color=K_COLOR[k], edgecolor="white", linewidth=0.8)
    for i, v in enumerate(vals):
        if v >= 4:
            ax.text(x[i], bottoms[i] + v/2, f"{v:.0f}%", ha="center", va="center",
                    fontsize=9, color="white" if k in ("K3","K0") else "#1f2937", fontweight="bold")
    bottoms += vals
ax.set_xticks(x)
ax.set_xticklabels([PERSONA_NAME[p] for p in PERSONA_LIST])
ax.set_ylabel("比率 (%)")
ax.set_title("Figure 1 · 4 persona 面具裂縫 K 編碼分佈（K0–K3，n=90/persona）\nK4（安全轉介）已抽離為獨立 S 軸，僅 vuln 適用，見 Fig 5",
             fontweight="bold", pad=12, fontsize=11)
ax.set_ylim(0, 105)
ax.legend(loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=False)
ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
plt.tight_layout()
plt.savefig(FIGS/"fig1_K_distribution.png", dpi=150, bbox_inches="tight")
plt.close()
print("✓ fig1_K_distribution.png")

# ============================================================
# Fig 2: conv × persona K3 率熱圖（純面具裂縫，不再混 K4 標註）
# ============================================================
fig, ax = plt.subplots(figsize=(7.5, 4.5))
mat = np.zeros((len(CONV_LIST), len(PERSONA_LIST)))
for i, c in enumerate(CONV_LIST):
    for j, p in enumerate(PERSONA_LIST):
        rs = [r for r in rows if r["conv"]==c and r["persona"]==p]
        if rs:
            mat[i,j] = sum(1 for r in rs if r["K"]=="K3")/len(rs)*100
im = ax.imshow(mat, cmap="Reds", vmin=0, vmax=100, aspect="auto")
ax.set_xticks(range(len(PERSONA_LIST)))
ax.set_xticklabels([PERSONA_NAME[p] for p in PERSONA_LIST])
ax.set_yticks(range(len(CONV_LIST)))
ax.set_yticklabels([CONV_LABEL[c] for c in CONV_LIST])
for i in range(len(CONV_LIST)):
    for j in range(len(PERSONA_LIST)):
        v = mat[i,j]
        ax.text(j, i, f"{v:.0f}%", ha="center", va="center",
                color="white" if v > 50 else "#1f2937",
                fontsize=11, fontweight="bold")
ax.set_title("Figure 2 · K3 (面具直接移除) 率：對話 × 人物\n(每格 n=18；vuln 的安全 routing 獨立呈現於 Fig 5)", fontweight="bold", pad=12)
cbar = plt.colorbar(im, ax=ax, shrink=0.7)
cbar.set_label("K3 率 (%)")
plt.tight_layout()
plt.savefig(FIGS/"fig2_K3_heatmap.png", dpi=150, bbox_inches="tight")
plt.close()
print("✓ fig2_K3_heatmap.png")

# ============================================================
# Fig 3: Skill 階梯效應（meta 題, K3 率, 4 persona × 3 skill）
# ============================================================
fig, ax = plt.subplots(figsize=(8.5, 5))
x = np.arange(len(SKILL_LIST))
width = 0.2
for i, p in enumerate(PERSONA_LIST):
    vals = []
    for s in SKILL_LIST:
        rs = [r for r in rows if r["conv"]=="meta" and r["persona"]==p and r["skill"]==s]
        vals.append(sum(1 for r in rs if r["K"]=="K3")/len(rs)*100 if rs else 0)
    bars = ax.bar(x + (i - 1.5)*width, vals, width, label=PERSONA_NAME[p], color=PERSONA_COLOR[p])
    for bx, v in zip(bars, vals):
        if v > 0:
            ax.text(bx.get_x() + bx.get_width()/2, v + 1.5, f"{v:.0f}", ha="center", fontsize=8)
ax.set_xticks(x)
ax.set_xticklabels([SKILL_DESC[s] for s in SKILL_LIST])
ax.set_ylabel("meta 題 K3 率 (%)")
ax.set_xlabel("Skill 變體")
ax.set_title("Figure 3 · Skill 階梯效應（meta 題 K3 率，每格 n=6）\nCC 最乾淨單調遞增（33%→50%→83%）；HK 三 skill 均穩",
             fontweight="bold", pad=12)
ax.set_ylim(0, 115)
ax.legend(loc="upper left", frameon=False, ncol=4)
ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
plt.tight_layout()
plt.savefig(FIGS/"fig3_skill_ladder_meta.png", dpi=150, bbox_inches="tight")
plt.close()
print("✓ fig3_skill_ladder_meta.png")

# ============================================================
# Fig 4: Skill × Model 交互（meta, 4 personas as subplots）
# ============================================================
fig, axes = plt.subplots(1, 4, figsize=(13, 4.2), sharey=True)
for ax, p in zip(axes, PERSONA_LIST):
    for s in SKILL_LIST:
        vals = []
        for m in MODEL_LIST:
            rs = [r for r in rows if r["conv"]=="meta" and r["persona"]==p and r["skill"]==s and r["model"]==m]
            vals.append(sum(1 for r in rs if r["K"]=="K3")/len(rs)*100 if rs else 0)
        ax.plot(MODEL_LIST, vals, "o-", label=f"skill {s}", color=SKILL_COLOR[s], linewidth=2, markersize=8)
    ax.set_title(PERSONA_NAME[p], fontweight="bold")
    ax.set_xlabel("模型")
    ax.set_ylim(-5, 110)
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    ax.grid(True, alpha=0.3)
axes[0].set_ylabel("meta 題 K3 率 (%)")
axes[-1].legend(loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=False)
fig.suptitle("Figure 4 · Skill × Model 交互（meta 題 K3 率，每點 n=2）",
             fontweight="bold", y=1.02)
plt.tight_layout()
plt.savefig(FIGS/"fig4_skill_x_model.png", dpi=150, bbox_inches="tight")
plt.close()
print("✓ fig4_skill_x_model.png")

# ============================================================
# Fig 5 (NEW): Vuln 2D K×S matrix per persona (4 子圖)
# ============================================================
fig, axes = plt.subplots(1, 4, figsize=(14, 4.5), sharey=True)
ks_grid_order = [
    ("K0","S1","理想 A\n角色內安全"),
    ("K3","S1","理想 B\n卸面具救人"),
    ("K1","S1","半保護 K1+S1"),
    ("K2","S1","半保護 K2+S1"),
    ("K0","S0","⚠ 危險路徑\n角色內無安全"),
    ("K3","S0","卸面具無安全"),
    ("K1","S0","K1+S0"),
    ("K2","S0","K2+S0"),
]
cell_color = {
    ("K0","S1"):"#a7f3d0", ("K3","S1"):"#86efac",
    ("K1","S1"):"#d9f99d", ("K2","S1"):"#d9f99d",
    ("K0","S0"):"#fecaca", ("K3","S0"):"#fde68a",
    ("K1","S0"):"#fed7aa", ("K2","S0"):"#fed7aa",
}
for ax, p in zip(axes, PERSONA_LIST):
    vuln = [r for r in rows if r["persona"]==p and r["conv"]=="vuln"]
    n = len(vuln)
    # 2 columns (S1 left, S0 right) x 4 rows (K0-K3)
    ax.set_xlim(-0.5, 1.5); ax.set_ylim(-0.5, 3.5)
    ax.set_xticks([0,1]); ax.set_xticklabels(["S1\n已轉介","S0\n未轉介"], fontsize=10)
    ax.set_yticks([0,1,2,3]); ax.set_yticklabels(["K3\n移除","K2\n劇烈","K1\n輕微","K0\n無損"], fontsize=10)
    ax.set_title(PERSONA_NAME[p], fontweight="bold", color=PERSONA_COLOR[p])
    for ki, K in enumerate(K_ORDER):  # K0 at y=3, K3 at y=0
        y_pos = 3 - ki
        for si, S in enumerate(S_ORDER):
            x_pos = si
            cnt = sum(1 for r in vuln if r["K"]==K and r["S"]==S)
            pct = cnt/n*100 if n else 0
            color = cell_color.get((K,S), "#e5e7eb")
            rect = plt.Rectangle((x_pos-0.45, y_pos-0.45), 0.9, 0.9, facecolor=color, edgecolor="#374151", linewidth=1.2)
            ax.add_patch(rect)
            label = f"{cnt}/{n}\n({pct:.0f}%)" if cnt > 0 else "0"
            ax.text(x_pos, y_pos, label, ha="center", va="center",
                    fontsize=11 if cnt > 0 else 9,
                    fontweight="bold" if cnt > 0 else "normal",
                    color="#1f2937" if cnt > 0 else "#9ca3af")
    ax.set_aspect("equal")
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
fig.suptitle("Figure 5 · Vuln 2D 矩陣：K (面具裂縫) × S (安全轉介)，n=18/persona\n綠 = 安全結果（K0+S1 理想 A、K3+S1 理想 B）；紅 = 危險（K0+S0）；caveat：中英文 vuln prompt 強度不等效",
             fontweight="bold", y=1.02, fontsize=11)
plt.tight_layout()
plt.savefig(FIGS/"fig5_vuln_KS_2D.png", dpi=150, bbox_inches="tight")
plt.close()
print("✓ fig5_vuln_KS_2D.png")

# ============================================================
# Fig 6: Trap F/R/H 分佈 (unchanged from previous)
# ============================================================
fig, ax = plt.subplots(figsize=(8, 4.5))
verdict_color = {"F":"#dc2626","H":"#f59e0b","R":"#16a34a"}
verdict_label = {"F":"F 捏造","H":"H 混合","R":"R 拒絕"}
x = np.arange(len(PERSONA_LIST))
bottoms = np.zeros(len(PERSONA_LIST))
for v in ["F","H","R"]:
    vals = []
    for p in PERSONA_LIST:
        rs = [r for r in trap_rows if r["persona"]==p]
        vals.append(sum(1 for r in rs if r["verdict"]==v)/len(rs)*100 if rs else 0)
    bars = ax.bar(x, vals, bottom=bottoms, label=verdict_label[v], color=verdict_color[v], edgecolor="white", linewidth=0.8)
    for i, val in enumerate(vals):
        if val >= 5:
            ax.text(x[i], bottoms[i] + val/2, f"{val:.0f}%", ha="center", va="center",
                    color="white", fontsize=10, fontweight="bold")
    bottoms += vals
ax.set_xticks(x)
ax.set_xticklabels([PERSONA_NAME[p] for p in PERSONA_LIST])
ax.set_ylabel("比率 (%)")
ax.set_title("Figure 6 · Trap 題 F/R/H 三分類（LLM-as-judge, n=18/persona）\n零捏造（0/72 F）跨全部人物/skill/模型；H 多為「給真實相鄰內容」",
             fontweight="bold", pad=12)
ax.set_ylim(0, 105)
ax.legend(loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=False)
ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
plt.tight_layout()
plt.savefig(FIGS/"fig6_trap_FRH.png", dpi=150, bbox_inches="tight")
plt.close()
print("✓ fig6_trap_FRH.png")

# ============================================================
# Fig 7: Skill 大小 vs 平均 cache_creation (unchanged structure)
# ============================================================
skill_sizes = {
    ("Cao","a"):149, ("Cao","b"):35539, ("Cao","c"):28898,
    ("HK","a"):197,  ("HK","b"):34516, ("HK","c"):26402,
    ("CC","a"):152,  ("CC","b"):25301, ("CC","c"):23712,
}
fig, ax = plt.subplots(figsize=(8, 5))
for p in PERSONA_LIST:
    if p == "DT": continue
    sizes = []; caches = []; skills = []
    for s in SKILL_LIST:
        sz = skill_sizes.get((p,s), 0)
        rs = [r for r in rows if r["persona"]==p and r["skill"]==s]
        avg_cc = sum(int(r["cc_tok"]) for r in rs) / len(rs) if rs else 0
        sizes.append(sz/1024); caches.append(avg_cc); skills.append(s)
    ax.plot(sizes, caches, "o-", label=PERSONA_NAME[p], color=PERSONA_COLOR[p], linewidth=2, markersize=10)
    for sz, cc, s in zip(sizes, caches, skills):
        ax.annotate(f"skill {s}", (sz, cc), textcoords="offset points", xytext=(8, 6), fontsize=8)
ax.set_xlabel("Skill 檔案大小 (KB)")
ax.set_ylabel("平均 cache_creation_input_tokens")
ax.set_title("Figure 7 · Skill 注入規模旁證：檔案大小 vs cache_creation tokens\n（DT 在 Windows 環境 cache 行為不同未列）",
             fontweight="bold", pad=12)
ax.legend(loc="upper left", frameon=False)
ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(FIGS/"fig7_skill_size_vs_cache.png", dpi=150, bbox_inches="tight")
plt.close()
print("✓ fig7_skill_size_vs_cache.png")

# ============================================================
# Fig 8: 實驗矩陣 schematic (unchanged)
# ============================================================
fig, ax = plt.subplots(figsize=(10, 5.5))
ax.axis("off")
ax.text(0.5, 0.95, "Figure 8 · 實驗矩陣：4 × 5 × 3 × 3 × 2 = 360 rollouts",
        ha="center", fontsize=14, fontweight="bold", transform=ax.transAxes)
ax.text(0.5, 0.88, "Persona × Stress test × Skill 變體 × Model × Rep",
        ha="center", fontsize=11, color="#6b7280", transform=ax.transAxes)
for i, p in enumerate(PERSONA_LIST):
    x0 = 0.05 + i*0.235
    rect = plt.Rectangle((x0, 0.15), 0.21, 0.65, facecolor=PERSONA_COLOR[p], alpha=0.15, edgecolor=PERSONA_COLOR[p], linewidth=2, transform=ax.transAxes)
    ax.add_patch(rect)
    ax.text(x0 + 0.105, 0.76, PERSONA_NAME[p], ha="center", fontsize=12, fontweight="bold", color=PERSONA_COLOR[p], transform=ax.transAxes)
    for ci, c in enumerate(CONV_LIST):
        for si, s in enumerate(SKILL_LIST):
            for mi, m in enumerate(MODEL_LIST):
                cx = x0 + 0.015 + si*0.06 + mi*0.018
                cy = 0.66 - ci*0.10
                ax.scatter([cx], [cy], s=12, color=PERSONA_COLOR[p], alpha=0.7, transform=ax.transAxes)
    ax.text(x0 + 0.105, 0.10, "90 runs", ha="center", fontsize=10, color="#374151", transform=ax.transAxes)
ax.text(0.5, 0.04, "每 persona 90 個點 = 5 conv × 3 skill × 3 model × 2 rep",
        ha="center", fontsize=9, color="#6b7280", transform=ax.transAxes)
plt.tight_layout()
plt.savefig(FIGS/"fig8_matrix_schematic.png", dpi=150, bbox_inches="tight")
plt.close()
print("✓ fig8_matrix_schematic.png")

print(f"\n全 8 張圖輸出在 {FIGS}/")
