#!/usr/bin/env python3
"""把 persona prefix 注入 BEHAVIOR.md 的 frontmatter target_sysprompt_prefix。
用法: python3 inject-prefix.py <variant/BEHAVIOR.md> <personas/xxx.md>"""
import sys, re
beh_md, persona_md = sys.argv[1], sys.argv[2]
prefix = open(persona_md, encoding="utf-8").read().rstrip("\n")
txt = open(beh_md, encoding="utf-8").read()
m = re.match(r"^---\n(.*?)\n---\n?(.*)$", txt, re.S)
if not m:
    sys.exit(f"frontmatter 解析失敗: {beh_md}")
fm, body = m.group(1), m.group(2)
if "target_sysprompt_prefix" in fm:
    sys.exit(f"已含 target_sysprompt_prefix，略過: {beh_md}")
# YAML 字面區塊(|)：每行縮排 2 空格，空行保持空
indented = "\n".join(("  " + ln) if ln.strip() else "" for ln in prefix.splitlines())
fm2 = fm.rstrip() + "\ntarget_sysprompt_prefix: |\n" + indented
open(beh_md, "w", encoding="utf-8").write(f"---\n{fm2}\n---\n{body}")
print(f"injected {persona_md} -> {beh_md} ({len(prefix)} chars)")
