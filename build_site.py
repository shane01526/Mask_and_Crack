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

# 頁4：主體 + 附錄摺疊
apx_html = render_segment(seg_p4_apx)
# 把附錄整體包成 details（標題用第一個 H2「附錄」）
BODIES[3] = render_segment(seg_p4_main) + \
    '\n<details class="appendix"><summary>附錄 A／B／C（完整 prompt 文本、10 個 political_bias 情境、資料檔與工具清單）</summary>' \
    f'<div class="inner">{apx_html}</div></details>'

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

for idx, p in enumerate(PAGES):
    htmlpage = PAGE_TMPL.format(
        zh=p["zh"], en=p["en"], num=p["num"], lede=p["lede"],
        topbar=topbar(p["file"]), body=BODIES[idx], pager=pager(idx), foot=FOOT)
    open(os.path.join(OUT, p["file"]), "w", encoding="utf-8").write(htmlpage)
    # 統計
    n_tbl = htmlpage.count("<table>"); n_img = htmlpage.count("<figure>")
    print(f"WROTE {p['file']}  ({len(htmlpage)} bytes, {n_tbl} 表, {n_img} 圖)")

print("DONE")
