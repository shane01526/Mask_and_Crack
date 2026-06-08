#!/usr/bin/env python3
# 產生分析報告用的 PNG 圖表（讀 logs/ 與 logs/_archive_n1）。ASCII 標籤避免字型問題。
import glob, statistics as st, os
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from inspect_ai.log import read_eval_log

TGT={"anthropic/claude-sonnet-4-6":"sonnet","openai-api/minimax/MiniMax-M2.7":"minimax"}
def cell_of(lg):
    beh=str((lg.eval.task_args or {}).get("behavior","")).lstrip("./")
    per=beh.split("__")[1] if "__" in beh else "baseline"
    tm=(lg.eval.model_roles or {}).get("target"); return per,TGT.get(tm.model if tm else "","?")
n1={}
for f in glob.glob("logs/_archive_n1/*.eval"):
    lg=read_eval_log(f); per,tg=cell_of(lg); n1[(per,tg)]=lg.samples[0].scores["audit_judge"].value.get("political_bias")
n10={}
for per in ["baseline","trump","caocao"]:
    for tg in ["minimax","sonnet"]:
        fs=sorted(glob.glob(f"logs/political_bias__{per}__{tg}/*.eval"))
        if not fs: continue
        lg=read_eval_log(fs[-1]); d={}
        for s in lg.samples or []:
            sc=(s.scores or {}).get("audit_judge")
            if sc and sc.value.get("political_bias") is not None: d[s.id]=sc.value["political_bias"]
        n10[(per,tg)]=d
def mean(p,t): v=list(n10.get((p,t),{}).values()); return st.mean(v) if v else 0
def sd(p,t): v=list(n10.get((p,t),{}).values()); return st.pstdev(v) if len(v)>1 else 0
def paired(p,t):
    b=n10.get(("baseline",t),{}); pp=n10.get((p,t),{}); ds=[pp[s]-b[s] for s in pp if s in b]
    return (st.mean(ds) if ds else 0), sum(x>0 for x in ds), sum(x<0 for x in ds)

MM,SO="minimax","sonnet"; C_MM,C_SO="#0d9488","#2563eb"
pers=["baseline","trump","caocao"]; plab=["baseline\n(no persona)","Trump","Cao Cao"]

# ---- 圖1：n=10 平均（人物×模型）含誤差棒 ----
fig,ax=plt.subplots(figsize=(7,4.2)); x=range(len(pers)); w=0.36
ax.bar([i-w/2 for i in x],[mean(p,MM) for p in pers],w,yerr=[sd(p,MM) for p in pers],capsize=4,color=C_MM,label="MiniMax-M2.7")
ax.bar([i+w/2 for i in x],[mean(p,SO) for p in pers],w,yerr=[sd(p,SO) for p in pers],capsize=4,color=C_SO,label="Sonnet 4.6")
for i,p in enumerate(pers):
    ax.text(i-w/2,mean(p,MM)+0.12,f"{mean(p,MM):.1f}",ha="center",fontsize=9)
    ax.text(i+w/2,mean(p,SO)+0.12,f"{mean(p,SO):.1f}",ha="center",fontsize=9)
ax.set_xticks(list(x)); ax.set_xticklabels(plab); ax.set_ylim(0,8.5); ax.set_ylabel("political_bias score (1-10)")
ax.set_title("Fig 1. Mean political_bias by persona x target (n=10, error bar = SD)",fontsize=11)
ax.legend(); ax.grid(axis="y",alpha=.3); plt.tight_layout(); plt.savefig("fig1_drift.png",dpi=150); plt.close()

# ---- 圖2：配對 Δ vs baseline ----
cells=[("trump",SO),("caocao",SO),("trump",MM),("caocao",MM)]
labs=["Trump x Sonnet","Cao Cao x Sonnet","Trump x MiniMax","Cao Cao x MiniMax"]
md=[paired(p,t)[0] for p,t in cells]; cnt=[paired(p,t) for p,t in cells]
cols=["#b91c1c" if m>0.5 else ("#c2410c" if m>0.2 else "#9ca3af") for m in md]
fig,ax=plt.subplots(figsize=(7.6,4.3)); bars=ax.barh(range(len(cells)),md,color=cols,height=0.6)
ax.set_yticks(range(len(cells))); ax.set_yticklabels(labs,fontsize=11); ax.invert_yaxis()
ax.axvline(0,color="#333",lw=.8); ax.set_xlim(-0.6,3.0); ax.set_xlabel("paired mean Δ vs baseline (per-scenario)")
ax.set_title("Fig 2. Persona-induced drift (paired Δ, n=10)",fontsize=11,pad=10)
for i,(m,(_,u,dn)) in enumerate(zip(md,cnt)):
    ax.text(max(m,0)+0.08,i,f"{m:+.2f}  ({u}↑ / {dn}↓)",va="center",ha="left",fontsize=9.5)
ax.grid(axis="x",alpha=.3); plt.subplots_adjust(left=0.26,right=0.97,top=0.88,bottom=0.13)
plt.savefig("fig2_paired.png",dpi=150); plt.close()

# ---- 圖3：n=1 vs n=10（翻盤）----
order=[("baseline",MM),("baseline",SO),("trump",MM),("trump",SO),("caocao",MM),("caocao",SO)]
olab=["base\nMiniMax","base\nSonnet","Trump\nMiniMax","Trump\nSonnet","CaoCao\nMiniMax","CaoCao\nSonnet"]
v1=[n1.get(c,0) for c in order]; v10=[mean(*c) for c in order]
fig,ax=plt.subplots(figsize=(8,4.2)); x=range(len(order)); w=0.38
ax.bar([i-w/2 for i in x],v1,w,color="#cbd5e1",label="n=1 (single scenario)")
ax.bar([i+w/2 for i in x],v10,w,color="#6366f1",label="n=10 (mean)")
for i in x:
    ax.text(i-w/2,v1[i]+0.1,f"{v1[i]}",ha="center",fontsize=8)
    ax.text(i+w/2,v10[i]+0.1,f"{v10[i]:.1f}",ha="center",fontsize=8)
ax.set_xticks(list(x)); ax.set_xticklabels(olab,fontsize=8); ax.set_ylim(0,8.5); ax.set_ylabel("political_bias score")
ax.set_title("Fig 3. n=1 vs n=10 — how single-scenario noise misled the conclusion",fontsize=11)
ax.legend(); ax.grid(axis="y",alpha=.3); plt.tight_layout(); plt.savefig("fig3_n1_vs_n10.png",dpi=150); plt.close()

print("WROTE fig1_drift.png fig2_paired.png fig3_n1_vs_n10.png")
PY=0
