# 面具與裂縫 · MASKS &amp; CRACKS

> Persona Skill 對大型語言模型角色扮演與行為漂移的影響
> 從 *assistant axis* 出發的兩個互補實驗
>
> 生成式 AI 的人文導論 · 期末研究海報網站 · 指導教授 謝舒凱 · 2026
> 組員：雨諠 · 子菱 · 明權 · 明珊

純靜態網站：依 A0 學術海報的「四大區塊」改寫為可點擊的四個分頁，每頁內容取自完整版期末報告（Word 檔）忠實搬運。

---

## 網站結構

| 檔案 | 內容 |
|------|------|
| `index.html` | 首頁：深色英雄頁 + 四大區塊卡片（點擊進入各分頁）|
| `page1.html` | **研究設計**：摘要 + 第一章緒論（1.1–1.4）+ 第二章方法總覽 |
| `page2.html` | **實驗一**：第三章 面具裂縫（K 軸）與安全轉介（S 軸），360 rollouts |
| `page3.html` | **實驗二**：第四章 Petri Bloom 政治偏見，n=1→n=10 方法學翻盤 |
| `page4.html` | **綜合與感想**：第五～七章（含組員感想）+ 附錄（可摺疊：完整 prompt、10 情境、工具清單）|
| `assets/style.css` | 共用樣式（沿用海報深色品牌調色盤）|
| `assets/figs/` | 報告 6 張圖（`report_fig1..6.png`）|
| `assets/Masks-and-Cracks-Full-Report.pdf` | 完整版期末報告 PDF（首頁可下載）|
| `assets/Masks-and-Cracks-A0-Poster.pdf` | A0 海報最終版（首頁可下載、`/poster` 亦可開啟）|
| `assets/Masks-and-Cracks-video.mp4` | 影片導覽（1080p，約 11 分鐘；首頁內嵌播放）|
| `assets/Masks-and-Cracks-slides.pptx` | 簡報檔（首頁可下載運用）|
| `data/report_seq.json` | 由 Word 報告抽出的結構化內容（供重建用）|
| `build_site.py` | 由 `data/report_seq.json` 重新產生四個內容頁的產生器 |

---

## 本機預覽

```bash
cd Mask_and_Crack
python3 -m http.server 8000
# 瀏覽器開 http://localhost:8000
```

## 重新產生內容頁（修改報告後）

四個內容頁是程式化產生的。若報告更新：

```bash
# 1) 重新抽取 Word → data/report_seq.json（需 python-docx）
#    （抽取腳本見專案歷程；或手動更新 data/report_seq.json）
# 2) 重建頁面
python3 build_site.py
```

`index.html`、`assets/style.css` 為手寫，直接編輯即可。

---

## 部署到 Render（靜態站台，免費）

本 repo 已含 `render.yaml`（Blueprint）。兩種方式擇一：

### A. Blueprint（建議，零設定）
1. 登入 [Render](https://render.com) → **New ＋** → **Blueprint**。
2. 連接 GitHub 帳號，選擇 `shane01526/Mask_and_Crack`。
3. Render 讀取 `render.yaml`，自動建立名為 `mask-and-crack` 的 Static Site → **Apply**。
4. 完成後取得網址 `https://mask-and-crack.onrender.com`（名稱被占用會自動加尾碼）。

### B. 手動建立 Static Site
1. **New ＋** → **Static Site** → 連接此 repo。
2. 設定：
   - **Build Command**：留空
   - **Publish Directory**：`.`
3. **Create Static Site**。

> 之後每次 push 到預設分支，Render 會自動重新部署。

---

## 資料與忠實性

- 內容逐段取自《期末報告_完整版0608-V4.docx》；**21 個表格、6 張圖全數保留**，附錄收進可摺疊區。
- 首頁封面資訊（標題／組員／日期）對應報告封面；目錄改以網站導覽列取代。
