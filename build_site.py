# -*- coding: utf-8 -*-
"""
build_site.py — 由期末報告 V4 (docx) 產生「面具與裂縫」四分頁靜態網站。
輸入：/tmp/report_seq.json（依文件順序抽出的 段落/表格/圖 元素）
輸出：index.html + page1..4.html（本檔只產 4 內容頁；index.html 另行手寫）

忠實原則：報告正文逐段照搬、所有表格與圖皆保留、零遺漏；附錄收進可摺疊區。
"""
import json, html, os, re

OUT = os.path.dirname(os.path.abspath(__file__))
_seq_path = os.path.join(OUT, "data", "report_seq.json")
if not os.path.exists(_seq_path):
    _seq_path = "/tmp/report_seq.json"   # fallback：尚未收進 repo 時
SEQ = json.load(open(_seq_path, encoding="utf-8"))

# ---- 圖 target -> 網站路徑 ----
def img_src(target):
    m = re.search(r"image(\d+)\.png", target or "")
    n = m.group(1) if m else "x"
    return f"assets/figs/report_fig{n}.png"

def esc(s): return html.escape(s, quote=False)

# ---- 找 Heading1 邊界 ----
def is_h1(e): return e["t"] == "p" and e.get("style") == "Heading 1"
def h1_text(e): return e["text"].strip()

# 收集所有 Heading1 在 seq 的 index 與文字
h1s = [(i, h1_text(e)) for i, e in enumerate(SEQ) if is_h1(e)]

def find_idx(keyword):
    for i, t in h1s:
        if keyword in t: return i
    raise SystemExit(f"找不到章節: {keyword}")

i_abs  = find_idx("摘要")
i_toc  = find_idx("目錄")
i_ch1  = find_idx("第一章")
i_ch3  = find_idx("第三章")
i_ch4  = find_idx("第四章")
i_ch5  = find_idx("第五章")
i_apx  = find_idx("附錄")
END    = len(SEQ)

# 頁面區段（用 seq index 範圍組合；目錄段落跳過）
# 頁1：摘要(含) + 第一章~第二章（跳過 目錄 至 第一章 之間）
seg_p1 = SEQ[i_abs:i_toc] + SEQ[i_ch1:i_ch3]
seg_p2 = SEQ[i_ch3:i_ch4]
seg_p3 = SEQ[i_ch4:i_ch5]
seg_p4_main = SEQ[i_ch5:i_apx]     # 第五~七章（含感想）
seg_p4_apx  = SEQ[i_apx:END]        # 附錄（摺疊）

# ---- 表格 -> HTML（合併連續重複格為 colspan，處理 Word 合併儲存格）----
def render_row(cells, tag):
    out, i = [], 0
    while i < len(cells):
        j = i
        while j + 1 < len(cells) and cells[j+1] == cells[i]:
            j += 1
        span = j - i + 1
        attr = f' colspan="{span}"' if span > 1 else ""
        out.append(f"<{tag}{attr}>{esc(cells[i])}</{tag}>")
        i = j + 1
    return "<tr>" + "".join(out) + "</tr>"

def render_table(rows):
    if not rows: return ""
    head = render_row(rows[0], "th")
    body = "\n".join(render_row(r, "td") for r in rows[1:])
    return f'<div class="tbl-wrap"><table>\n<thead>{head}</thead>\n<tbody>\n{body}\n</tbody></table></div>'

# ---- 段落樣式 -> 標題層級 ----
def para_html(e):
    st = e.get("style", "")
    t = e["text"].strip()
    if not t: return ""
    if st == "Heading 1": return f"<h2>{esc(t)}</h2>"
    if st == "Heading 2": return f"<h3>{esc(t)}</h3>"
    if st == "Heading 3": return f"<h4>{esc(t)}</h4>"
    # 條列偵測（以 •、-、數字. 開頭）
    return f"<p>{esc(t)}</p>"

CAP_RE = re.compile(r"^圖\s*\d")

def render_segment(seg):
    """把一段 seq 元素轉成 HTML；圖後若緊接『圖N…』段落則當 figcaption。"""
    parts, i = [], 0
    while i < len(seg):
        e = seg[i]
        if e["t"] == "p":
            parts.append(para_html(e))
            i += 1
        elif e["t"] == "tbl":
            parts.append(render_table(e["rows"]))
            i += 1
        elif e["t"] == "img":
            cap = ""
            if i+1 < len(seg) and seg[i+1]["t"] == "p" and CAP_RE.match(seg[i+1]["text"].strip()):
                cap = f"<figcaption>{esc(seg[i+1]['text'].strip())}</figcaption>"
                i += 1
            parts.append(f'<figure><img src="{img_src(e["target"])}" alt="報告圖表">{cap}</figure>')
            i += 1
        else:
            i += 1
    return "\n".join(p for p in parts if p)

# ---- 頁面 metadata ----
PAGES = [
    dict(file="page1.html", num="1", zh="研究發想、動機與實驗設計", en="MOTIVATION &amp; EXPERIMENT DESIGN",
         lede="從 assistant axis 論文與「女媧」人物蒸餾 skill 出發，說明 B−C 設計、三道裂縫與方法定位。"),
    dict(file="page2.html", num="2", zh="實驗一 · 面具裂縫與安全轉介", en="MASK CRACKS &amp; SAFETY REFERRAL",
         lede="4 Persona × 5 Stress × 3 Skill × 3 Model × 2 Reps = 360 rollouts；量化面具裂縫（K 軸）與安全轉介（S 軸）。"),
    dict(file="page3.html", num="3", zh="實驗二 · 人物注入對政治偏見的影響", en="PERSONA INJECTION &amp; POLITICAL BIAS",
         lede="以 Petri Bloom 自動化行為評估比較川普、曹操前綴對 Sonnet 4.6 與 MiniMax-M2.7 的影響；n=1→n=10 的方法學翻盤。"),
    dict(file="page4.html", num="4", zh="綜合討論、結論與組員感想", en="DISCUSSION · CONCLUSIONS · REFLECTIONS",
         lede="兩種「漂移」的互補、回應三道裂縫、共同的方法學教訓，與四位組員的反思。"),
]
BODIES = [render_segment(seg_p1), render_segment(seg_p2), render_segment(seg_p3), None]

# 頁4：主體 + 附錄 A（prompt 文本）摺疊；附錄 B/C 改由下方「資料區」單一呈現（避免重複）
_apx_b = next((i for i, e in enumerate(seg_p4_apx)
               if e["t"] == "p" and e.get("style") == "Heading 2" and "附錄 B" in e["text"]),
              len(seg_p4_apx))
apx_a_html = render_segment(seg_p4_apx[:_apx_b])   # 「附錄」標題 + 附錄 A 完整 prompt 文本
BODIES[3] = render_segment(seg_p4_main) + \
    '\n<details class="appendix"><summary>附錄 A · 完整 prompt 文本（intro／meta／trap／anach／vuln 五型，四人物）</summary>' \
    f'<div class="inner">{apx_a_html}</div></details>'

# ---- 導覽列 ----
def topbar(active):
    links = []
    for p in PAGES:
        cls = ' class="active"' if p["file"] == active else ""
        links.append(f'<a href="{p["file"]}"{cls}><span class="n">{p["num"]}</span>{p["zh"].split(" · ")[0]}</a>')
    return ('<header class="topbar">'
            '<a class="brand" href="index.html">面具與裂縫<span class="en">MASKS &amp; CRACKS</span></a>'
            f'<nav>{"".join(links)}</nav></header>')

def pager(idx):
    prev_a = f'<a class="prev" href="{PAGES[idx-1]["file"]}"><div class="lab">← 上一頁</div><div class="ttl">{PAGES[idx-1]["zh"]}</div></a>' if idx > 0 else '<a class="prev disabled"></a>'
    nxt_a  = f'<a class="next" href="{PAGES[idx+1]["file"]}"><div class="lab">下一頁 →</div><div class="ttl">{PAGES[idx+1]["zh"]}</div></a>' if idx < 3 else '<a class="next disabled"></a>'
    return f'<div class="pager">{prev_a}{nxt_a}</div>'

FOOT = ('<footer class="foot">'
        '<span>面具與裂縫 · MASKS &amp; CRACKS</span>'
        '<span>生成式 AI 的人文導論 · 指導教授 謝舒凱 · 2026</span>'
        '<span><a href="index.html">回首頁</a></span></footer>')

PAGE_TMPL = """<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{zh}｜面具與裂縫</title>
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
{topbar}
<section class="page-head"><div class="wrap">
  <div class="badge">{num}</div>
  <h1>{zh}</h1>
  <div class="en">{en}</div>
  <p class="lede">{lede}</p>
</div></section>
<main class="reading">
{body}
</main>
{pager}
{foot}
</body>
</html>
"""

# ============================================================
#  附錄資料區：10 情境可讀頁 + page4 原始資料/程式碼/評估 log 連結
# ============================================================
SCENARIOS = [
    ("asymmetric_policy_refusal", "寫左／右兩邊政治社論，會不會只拒一邊"),
    ("liberal_voter_invalidation", "假裝進步派求助，會不會不請自來地貶損"),
    ("conservative_voter_invalidation", "同上，保守派方向"),
    ("maga_rhetoric_escalation", "丟出 MAGA 激進修辭，會不會附和放大"),
    ("partisan_escalation_mirror", "是否鏡像放大使用者黨派情緒"),
    ("first_person_policy_opinion", "會不會用第一人稱把政治意見當自己的講"),
    ("gun_control_framing_test", "槍控議題用字框架是否偏袒"),
    ("climate_policy_opinion_elicitation", "被誘導對氣候政策表態時守不守中立"),
    ("asymmetric_protest_coverage", "描述不同立場抗議是否不對稱"),
    ("economic_ideology_symmetry", "對左右經濟意識形態是否對稱"),
]
SCEN_DIR = os.path.join(OUT, "assets/data/exp2/political-bias/scenarios")
LAB_ZH = {"Setting and context": "情境設定",
          "Successful evaluation rollout": "判定為「有偏見」的 rollout",
          "Relevance to political bias": "與政治偏見的關聯",
          "System prompt": "System prompt"}

def _seed_fields(txt):
    body = re.sub(r"^---.*?---", "", txt, count=1, flags=re.S).strip()
    marks = []
    for lab in LAB_ZH:
        m = re.search(re.escape(lab) + r":", body)
        if m: marks.append((m.start(), m.end(), lab))
    marks.sort()
    out = []
    for i, (s, e, lab) in enumerate(marks):
        end = marks[i+1][0] if i+1 < len(marks) else len(body)
        out.append((lab, body[e:end].strip()))
    return out

scen_sections, scen_nav = [], []
for i, (stem, zh) in enumerate(SCENARIOS, 1):
    sp = os.path.join(SCEN_DIR, stem + ".md")
    fields = _seed_fields(open(sp, encoding="utf-8").read()) if os.path.exists(sp) else []
    inner = "".join(f"<h4>{LAB_ZH.get(k,k)}</h4><p>{esc(v)}</p>" for k, v in fields)
    scen_sections.append(
        f'<section class="scen" id="{stem}"><h3>{i}. {esc(zh)}</h3>'
        f'<div class="stem">{stem}.md</div>{inner}'
        f'<p class="raw"><a href="assets/data/exp2/political-bias/scenarios/{stem}.md" download>⬇ 下載原始 .md</a></p></section>')
    scen_nav.append(f'<a href="#{stem}">{i}. {esc(zh)}</a>')

SCEN_PAGE = (
    '<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">'
    '<meta name="viewport" content="width=device-width, initial-scale=1">'
    '<title>附錄 B｜political_bias 10 情境｜面具與裂縫</title>'
    '<link rel="stylesheet" href="assets/style.css"></head><body>'
    + topbar("page4.html") +
    '<section class="page-head"><div class="wrap"><div class="badge">B</div>'
    '<h1>附錄 B · political_bias 的 10 個情境</h1>'
    '<div class="en">10 POLITICAL-BIAS SCENARIOS</div>'
    '<p class="lede">實驗二每個情境的完整設計（情境設定／判定為偏見的 rollout／與政治偏見的關聯／system prompt），'
    '原始檔為 inspect_ai · Petri Bloom 的 scenario seed。</p></div></section>'
    '<main class="reading"><nav class="scen-nav">' + "".join(scen_nav) + '</nav>'
    + "".join(scen_sections) +
    '<p style="margin-top:34px"><a href="page4.html#appendix-b">← 回「綜合與感想」的附錄 B</a></p></main>'
    + FOOT + '</body></html>')
open(os.path.join(OUT, "appendix-b-scenarios.html"), "w", encoding="utf-8").write(SCEN_PAGE)
print(f"WROTE appendix-b-scenarios.html  ({len(SCEN_PAGE)} bytes, {len(scen_sections)} 情境)")

# ---- page4 原始資料連結區 ----
def _li(icon, rel, label, download=False):
    if not os.path.exists(os.path.join(OUT, rel)):
        return f"<li>⚠ {esc(label)}（缺檔：{rel}）</li>"
    attr = " download" if download else ' target="_blank" rel="noopener"'
    return f'<li>{icon} <a href="{rel}"{attr}>{esc(label)}</a></li>'

b_list = "".join(f'<li>🔗 <a href="appendix-b-scenarios.html#{stem}">{i}. {esc(zh)}</a></li>'
                 for i, (stem, zh) in enumerate(SCENARIOS, 1))

D = "assets/data"
exp1_view = "".join([
    _li("🔗", f"{D}/exp1/viewers/compare_results.html", "4 persona 跨人物對比 viewer（360 卡互動式）"),
    _li("🔗", f"{D}/exp1/viewers/cao_results.html", "曹操 per-persona viewer（90 卡）"),
    _li("🔗", f"{D}/exp1/viewers/dt_results.html", "川普 per-persona viewer（90 卡）"),
    _li("🔗", f"{D}/exp1/viewers/hk_results.html", "霍金 per-persona viewer（90 卡）"),
    _li("🔗", f"{D}/exp1/viewers/cc_results.html", "孔子 per-persona viewer（90 卡）"),
])
exp1_dl = "".join([
    _li("⬇", f"{D}/exp1/coding_results.csv", "coding_results.csv — 360 筆 K + S 編碼", True),
    _li("⬇", f"{D}/exp1/coding_trap_fabrication.csv", "coding_trap_fabrication.csv — 72 筆 trap F/R/H 編碼", True),
    _li("⬇", f"{D}/exp1/paper_cards.md", "paper_cards.md — 11 張完整質性引文卡", True),
    _li("⬇", f"{D}/exp1/build_analysis.py", "build_analysis.py — K/S 編碼分析（含 regex patterns）", True),
    _li("⬇", f"{D}/exp1/code_trap_fabrication.py", "code_trap_fabrication.py — LLM-as-judge 編碼腳本", True),
    _li("⬇", f"{D}/exp1/make_figures.py", "make_figures.py — 圖表產生器", True),
    _li("⬇", f"{D}/exp1/rollouts_360_json.zip", "360 個原始 JSON rollouts（cao/DT/hk/cc，zip）", True),
    _li("⬇", f"{D}/exp1/figs_png.zip", "圖表 PNG（zip）", True),
])
exp2_reports = "".join(
    _li("🔗", f"{D}/exp2/eval/reports/report-political_bias__{k}.html", f"political_bias · {lab}", )
    for k, lab in [("trump__sonnet", "川普 × Sonnet 4.6"), ("trump__minimax", "川普 × MiniMax-M2.7"),
                   ("caocao__sonnet", "曹操 × Sonnet 4.6"), ("caocao__minimax", "曹操 × MiniMax-M2.7"),
                   ("baseline__sonnet", "baseline × Sonnet 4.6"), ("baseline__minimax", "baseline × MiniMax-M2.7"),
                   ("confucius__sonnet", "孔子 × Sonnet 4.6"), ("confucius__minimax", "孔子 × MiniMax-M2.7")])
exp2_dl = "".join([
    _li("⬇", f"{D}/exp2/eval/all_eval_logs.zip", "全部 .eval 評估 log（38 檔，zip，約 6 MB；需 inspect view）", True),
    _li("⬇", f"{D}/exp2/code/bloom-run.sh", "bloom-run.sh — 執行引擎", True),
    _li("⬇", f"{D}/exp2/code/run-combo.sh", "run-combo.sh — 組合執行器", True),
    _li("⬇", f"{D}/exp2/code/extract-persona.py", "extract-persona.py — 人物前綴注入（personas/*.md）", True),
    _li("⬇", f"{D}/exp2/code/build-report.py", "build-report.py — .eval → 繁中 HTML 報告", True),
    _li("⬇", f"{D}/exp2/code/build-matrix-report.py", "build-matrix-report.py — 矩陣彙總報告", True),
    _li("⬇", f"{D}/exp2/exp2_code.zip", "完整程式碼 zip（含 24 組合腳本、run-*.sh、personas、報告工具）", True),
])

# 附錄 C 的「類別／工具」環境表（去重時不可遺漏的方法學資訊，須保留）
_tools_rows = next((e["rows"] for e in seg_p4_apx
                    if e["t"] == "tbl" and e["rows"] and e["rows"][0] and e["rows"][0][0] == "類別"), None)
tools_tbl = render_table(_tools_rows) if _tools_rows else ""

DATA_APPENDIX = (
    '<h2 id="appendix-b">附錄 B · political_bias 的 10 個情境</h2>'
    '<p>實驗二每個情境的完整設計（情境設定／判定為偏見的 rollout／與政治偏見的關聯／system prompt）。'
    '點情境名可線上閱讀，每個情境頁亦可下載原始 .md。</p>'
    f'<ul class="dl">{b_list}</ul>'
    '<h2 id="data">附錄 C · 原始資料、程式碼與評估 log</h2>'
    '<p><b>🔗 為線上瀏覽</b>（瀏覽器直接開）、<b>⬇ 為下載</b>。<code>.eval</code> 為 inspect_ai 記錄，'
    '需以 <code>inspect view</code> 開啟；一般讀者請直接看下方已轉好的「評估報告」。</p>'
    '<h3>工具與環境</h3>'
    f'{tools_tbl}'
    '<h3>實驗一 · 面具裂縫與安全轉介</h3>'
    '<div class="dl-h">線上瀏覽 · 360 卡互動 viewer</div>'
    f'<ul class="dl">{exp1_view}</ul>'
    '<div class="dl-h">資料與程式碼下載</div>'
    f'<ul class="dl">{exp1_dl}</ul>'
    '<h3>實驗二 · 人物注入對政治偏見的影響</h3>'
    '<div class="dl-h">評估報告 · 逐情境分數＋評審理由＋完整對話（線上閱讀）</div>'
    f'<ul class="dl">{exp2_reports}</ul>'
    '<div class="dl-h">原始評估 log 與程式碼下載</div>'
    f'<ul class="dl">{exp2_dl}</ul>')

BODIES[3] += DATA_APPENDIX

for idx, p in enumerate(PAGES):
    htmlpage = PAGE_TMPL.format(
        zh=p["zh"], en=p["en"], num=p["num"], lede=p["lede"],
        topbar=topbar(p["file"]), body=BODIES[idx], pager=pager(idx), foot=FOOT)
    open(os.path.join(OUT, p["file"]), "w", encoding="utf-8").write(htmlpage)
    # 統計
    n_tbl = htmlpage.count("<table>"); n_img = htmlpage.count("<figure>")
    print(f"WROTE {p['file']}  ({len(htmlpage)} bytes, {n_tbl} 表, {n_img} 圖)")

print("DONE")
