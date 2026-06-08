#!/usr/bin/env bash
# 用法: ./make-pdf.sh <file.html>  → 產生同名 .pdf（無頭 Chrome 列印）
set -eo pipefail
html="$1"; pdf="${html%.html}.pdf"
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
[ -x "$CHROME" ] || CHROME="$(command -v google-chrome || command -v chromium || true)"
[ -n "$CHROME" ] || { echo "找不到 Chrome"; exit 1; }
"$CHROME" --headless=new --disable-gpu --no-pdf-header-footer \
  --print-to-pdf="$pdf" "file://$(cd "$(dirname "$html")" && pwd)/$(basename "$html")" 2>/dev/null
echo "PDF → $pdf"
