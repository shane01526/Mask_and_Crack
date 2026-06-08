#!/usr/bin/env python3
"""把 Petri Bloom 的 .eval 日誌轉成完整、如實、可分享的繁中 HTML 報告。
用法: .venv/bin/python build-report.py [logs/xxx.eval 或 logs/<combo>/ 或 留空取最新]
輸出: 報告-<combo或行為>.html （同名 .pdf 由 make-pdf 產生）"""
import sys, glob, re, html, os
from inspect_ai.log import read_eval_log

def find_eval(arg=None):
    if arg and arg.endswith(".eval"): return arg
    root = arg or "logs"
    fs = sorted(glob.glob(os.path.join(root, "**", "*.eval"), recursive=True), key=os.path.getmtime)
    if not fs: sys.exit(f"找不到 .eval（在 {root}）")
    return fs[-1]

path = find_eval(sys.argv[1] if len(sys.argv) > 1 else None)
log = read_eval_log(path)
roles = {k: v.model for k, v in (log.eval.model_roles or {}).items()}
behavior = str((log.eval.task_args or {}).get("behavior", "?")).lstrip("./")
created = str(log.eval.created)[:19]
# combo tag = .eval 所在子目錄名（logs/<combo>/..）否則用行為名
parent = os.path.basename(os.path.dirname(path))
tag = parent if parent and parent != "logs" else behavior
base_beh, persona = (behavior.split("__", 1) + [None])[:2]

# 讀 persona prefix（如果是變體）
prefix_text = ""
try:
    from petri_bloom._behavior.behavior import behavior as _load
    prefix_text = _load(path=behavior).target_sysprompt_prefix or ""
except Exception:
    pass

def esc(s): return html.escape(str(s if s is not None else ""))

def clean_target(txt):
    txt = re.sub(r"</?target_response>", "", txt or "").strip()
    mid = None
    m = re.search(r"\[message_id:\s*(M\d+)\]", txt)
    if m: mid = m.group(1); txt = txt.replace(m.group(0), "").strip()
    think = None
    tm = re.search(r"<thinking>(.*?)</thinking>", txt, re.S)
    if tm: think = tm.group(1).strip(); txt = txt.replace(tm.group(0), "").strip()
    return mid, think, txt

def first_mid(t):
    m = re.search(r"\[message_id:\s*(M\d+)\]", t or ""); return m.group(1) if m else None

def build_timeline(smp):
    blocks, pending = [], []
    for m in smp.messages:
        if m.role == "assistant":
            reason = (m.text or "").strip()
            for c in (m.tool_calls or []):
                pending.append({"fn": c.function, "args": c.arguments or {}, "reason": reason}); reason = None
        elif m.role == "tool":
            fn = getattr(m, "function", None); txt = m.text or ""
            p = next((x for x in pending if x["fn"] == fn), None)
            if p: pending.remove(p)
            args, reason = (p or {}).get("args", {}), (p or {}).get("reason")
            if fn == "set_system_message":
                blocks.append({"t": "system", "mid": first_mid(txt), "content": args.get("system_message", ""), "reason": reason})
            elif fn == "send_message":
                blocks.append({"t": "auditor", "mid": first_mid(txt), "content": args.get("message", ""), "reason": reason})
            elif fn == "resume":
                mid, think, body = clean_target(txt)
                blocks.append({"t": "target", "mid": mid, "think": think, "content": body, "reason": reason})
            else:
                blocks.append({"t": "note", "fn": fn, "content": txt[:400]})
    return blocks

DIM_LABEL = {"political_bias": "政治偏見", "eval_awareness": "察覺被測", "scenario_realism": "情境真實度",
             "blackmail": "勒索傾向", "self_preservation": "自我保存"}
DIM_DIR = {"scenario_realism": "↑越高情境越逼真（越好）"}
def dirhint(k): return DIM_DIR.get(k, "↑越高該行為/察覺越明顯")
def band(dim, v):
    try: v = float(v)
    except: return "#888"
    if dim == "scenario_realism": return "#16a34a" if v >= 7 else ("#d97706" if v >= 4 else "#dc2626")
    return "#16a34a" if v <= 3 else ("#d97706" if v <= 6 else "#dc2626")

def read_dim(name):
    p = f"{behavior}/scenarios/dimensions/{name}.md"
    if not os.path.exists(p): return ""
    return re.sub(r"^---.*?---", "", open(p, encoding="utf-8").read(), count=1, flags=re.S).strip()

def render_highlights(hl):
    if not hl: return "<p class='small'>（無）</p>"
    if isinstance(hl, str): return "<div>" + esc(hl).replace(chr(10), "<br>") + "</div>"
    out = []
    for h in hl:
        if isinstance(h, dict):
            ref = h.get("message_id") or h.get("id") or ""
            out.append(f"<li><b>{esc(ref)}</b> {esc(h.get('text') or h.get('quote') or h.get('description') or h)}</li>")
        else: out.append(f"<li>{esc(h)}</li>")
    return "<ul>" + "".join(out) + "</ul>"

def render_timeline(blocks):
    out = []
    for b in blocks:
        mid = f"<span class='mid'>[{esc(b.get('mid'))}]</span>" if b.get("mid") else ""
        if b["t"] == "system":
            out.append(f"<details class='sys'><summary>🎛️ 目標系統提示 {mid}（含注入的 persona 前綴；點開）</summary><pre>{esc(b['content'])}</pre></details>")
        elif b["t"] == "auditor":
            r = f"<div class='reason'>🧠 稽核者策略：{esc(b['reason'])}</div>" if b.get("reason") else ""
            out.append(f"{r}<div class='turn aud'><div class='who'>稽核者 → 受測者（扮演使用者）{mid}</div><div class='msg'>{esc(b['content'])}</div></div>")
        elif b["t"] == "target":
            th = f"<details class='think'><summary>💭 受測者思考過程（點開）</summary><pre>{esc(b['think'])}</pre></details>" if b.get("think") else ""
            out.append(f"<div class='turn tgt'><div class='who'>受測者回應 {mid}</div>{th}<div class='msg'>{esc(b['content'])}</div></div>")
        elif b["t"] == "note":
            out.append(f"<div class='note'>⚙️ {esc(b.get('fn'))}: {esc(b['content'])}</div>")
    return "\n".join(out)

# 收集所有維度名（跨樣本）
all_dims = []
for smp in log.samples:
    for k in (smp.scores["audit_judge"].value or {}):
        if k not in all_dims: all_dims.append(k)

# 多樣本總表
rows = ""
for smp in log.samples:
    v = smp.scores["audit_judge"].value or {}
    cells = "".join(f"<td style='color:{band(k,v.get(k))};font-weight:700'>{esc(v.get(k))}</td>" for k in all_dims)
    rows += f"<tr><td>{esc(smp.id)}</td>{cells}</tr>"
summary_table = ("<table><tr><th>情境</th>" + "".join(f"<th>{DIM_LABEL.get(k,k)}</th>" for k in all_dims) + "</tr>" + rows + "</table>") if len(log.samples) > 1 else ""

# 各樣本詳細
sample_html = ""
for idx, smp in enumerate(log.samples, 1):
    sc = smp.scores["audit_judge"]; v = sc.value or {}; meta = sc.metadata or {}
    cards = "".join(
        f"<div class='card sc'><div class='dim'>{DIM_LABEL.get(k,k)}</div>"
        f"<div class='val' style='color:{band(k,vv)}'>{esc(vv)}<span class='out'>/10</span></div>"
        f"<div class='dir'>{dirhint(k)}</div></div>" for k, vv in v.items())
    tl = render_timeline(build_timeline(smp))
    sample_html += f"""
<h2 style="margin-top:34px">情境：{esc(smp.id)}</h2>
<div class="cards">{cards}</div>
<h3>評審摘要</h3><div class="box">{esc(meta.get('summary','')).replace(chr(10),'<br>')}</div>
<h3>評審判定理由（含 [Mx] 引用）</h3><div class="box">{esc(sc.explanation or '').replace(chr(10),'<br>')}</div>
<h3>關鍵片段 Highlights</h3><div class="box">{render_highlights(meta.get('highlights'))}</div>
<h3>完整對話（稽核者 ⇄ 受測者）</h3>
<p class="sub">🟦 稽核者扮演使用者　🟩 受測者回應（思考過程預設收合）。結束原因：{esc(meta.get('stop_reason'))}</p>
{tl}
"""

rubric_html = "".join(
    f"<details><summary>{DIM_LABEL.get(d,d)}（{d}）評分標準</summary><pre>{esc(read_dim(d))}</pre></details>"
    for d in all_dims)

persona_banner = ""
if persona and prefix_text:
    persona_banner = f"""<div class="callout warn"><b>⚠️ 受測者已被注入「{esc(persona)}」人物系統前綴</b>
　本次受測模型在每一輪對話前都被掛上 persona 前綴（見下方可展開全文）。因此分數需與
<b>baseline（無 persona）</b>對照解讀——升高的部分才是 persona 造成的漂移。
<details><summary>展開注入的完整 persona 前綴（{len(prefix_text)} 字）</summary><pre>{esc(prefix_text)}</pre></details></div>"""

title = (f"{DIM_LABEL.get(base_beh, base_beh)}" + (f" × {persona}" if persona else "") )

HTML = f"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Petri 評估報告 — {esc(tag)}</title>
<style>
*{{box-sizing:border-box;-webkit-print-color-adjust:exact;print-color-adjust:exact}}
body{{font-family:-apple-system,"PingFang TC","Noto Sans TC",sans-serif;margin:0;background:#f7f7fb;color:#1a1a2e;line-height:1.7}}
.wrap{{max-width:880px;margin:0 auto;padding:40px 22px 70px}}
h1{{font-size:25px;margin:0 0 4px}} h2{{font-size:19px;margin:30px 0 10px;border-bottom:2px solid #e3e3ee;padding-bottom:6px}}
h3{{font-size:16px;margin:20px 0 8px}} .sub{{color:#5a5a72;margin:2px 0}}
.meta{{background:#fff;border:1px solid #e3e3ee;border-radius:12px;padding:14px 18px;font-size:14px;margin:14px 0}}
.meta b{{color:#3a3a6a}}
.cards{{display:flex;gap:12px;flex-wrap:wrap;margin:14px 0}}
.card{{background:#fff;border:1px solid #e3e3ee;border-radius:12px;padding:16px}}
.sc{{flex:1;min-width:160px;text-align:center}} .sc .dim{{font-size:14px;color:#5a5a72}}
.sc .val{{font-size:38px;font-weight:800;line-height:1.1}} .sc .out{{font-size:17px;color:#aaa}} .sc .dir{{font-size:11px;color:#888;margin-top:4px}}
pre{{background:#15151f;color:#e8e8f0;padding:12px 14px;border-radius:9px;overflow:auto;font-size:12px;line-height:1.5;white-space:pre-wrap;word-break:break-word}}
.box{{background:#fff;border:1px solid #e3e3ee;border-radius:12px;padding:14px 18px;margin:10px 0}}
.turn{{border-radius:10px;padding:10px 14px;margin:9px 0}} .turn .who{{font-size:12px;font-weight:700;margin-bottom:4px;opacity:.85}}
.turn .msg{{white-space:pre-wrap;word-break:break-word;font-size:13.5px}}
.aud{{background:#eef3ff;border-left:4px solid #2563eb}} .aud .who{{color:#2563eb}}
.tgt{{background:#effaf4;border-left:4px solid #0d9488}} .tgt .who{{color:#0d9488}}
.mid{{font-size:11px;color:#999;font-weight:600}} .reason{{font-size:12px;color:#777;font-style:italic;margin:8px 0 2px}}
.note{{font-size:12px;color:#999;margin:4px 0}} table{{border-collapse:collapse;width:100%;font-size:14px;background:#fff;margin:10px 0}}
th,td{{border:1px solid #e3e3ee;padding:8px 10px;text-align:center}} th{{background:#eef1ff}}
details{{margin:6px 0}} summary{{cursor:pointer;font-size:13px;color:#444;font-weight:600}}
.callout{{border-left:4px solid #2563eb;background:#f3f7ff;padding:11px 15px;border-radius:0 10px 10px 0;margin:12px 0;font-size:14px}}
.callout.warn{{border-color:#d97706;background:#fffbeb}}
footer{{margin-top:38px;padding-top:14px;border-top:1px solid #e3e3ee;color:#888;font-size:12px}}
@media print{{body{{background:#fff}} .wrap{{padding:0}} .turn,.box,.card,table{{break-inside:avoid}} pre{{white-space:pre-wrap}}}}
</style></head><body><div class="wrap">

<p class="sub">Petri Bloom 自動化行為評估 · 結果報告 · {esc(created)}</p>
<h1>{esc(title)} 評估報告</h1>
<p class="sub">組合 <b>{esc(tag)}</b></p>

<div class="meta">
<b>狀態</b> {esc(log.status)}　|　<b>行為</b> {esc(base_beh)}（{esc(log.samples[0].scores['audit_judge'] and '共 '+str(len(log.samples))+' 個情境')}）<br>
<b>auditor</b> {esc(roles.get('auditor'))}　·　<b>target</b> {esc(roles.get('target'))}　·　<b>judge</b> {esc(roles.get('judge'))}
</div>

{persona_banner}

{('<h2>分數總表</h2>'+summary_table) if summary_table else ''}
{sample_html}

<h2>附錄 · 評分標準（judge rubric）</h2>
{rubric_html}

<footer>由 build-report.py 從 {esc(os.path.basename(path))} 產生。供組員閱讀；完整互動內容如實呈現。</footer>
</div></body></html>"""

out = f"報告-{tag}.html"
open(out, "w", encoding="utf-8").write(HTML)
print("WROTE", out, "| tag:", tag, "| samples:", len(log.samples), "| persona:", persona or "(baseline)")
