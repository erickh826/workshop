---
name: survey-analyst
description: 使用 Python 標準庫 (csv, statistics) 讀取期末教學評估問卷 (course_eval.csv)，精確計算各指標平均值與標準差，生成內嵌 Chart.js 互動視覺化圖表報告 eval_report.html 與學系教學檢討報告 department_summary.md。適用於教育、心理、醫護與社工學科。
---

# 期末教學評估量化分析與互動視覺化技能 (Course Evaluation Survey Analyst)

## 適用對象與教學場景
- **適用學科**：教育學院、心理學系、護理及醫療科學、社會工作及跨學科課程委員會。
- **教學目標**：協助教師在學期結束時，自動對學生教學評估問卷（Student Evaluation of Teaching, SET）進行嚴謹的描述性統計分析（平均值 Mean、標準差 SD、相關性 Correlation），並直接產出可於瀏覽器即時互動預覽的 Chart.js 視覺化圖表網頁與學系檢討報告。

---

## 執行步驟 (Step-by-Step Workflow)

### 步驟 1：執行 Python 標準庫腳本計算統計數據（強制步驟）
**嚴禁心算任何統計數字！** 必須先呼叫 `run_python_script` 執行純 Python 標準庫程式碼（僅使用 `csv`、`statistics`、`math`、`json`，**切勿 import pandas 或 matplotlib**，以確保雲端 Serverless 環境極速執行），完成以下計算並 `print()` 輸出：
1. 讀取輸入目錄下的 `course_eval.csv`（包含 10 位學生樣本，欄位為：`Student_ID`, `Clarity_Score`, `Engagement_Score`, `Feedback_Helpfulness`, `Overall_Satisfaction`, `Study_Hours_Per_Week`）。
2. 針對全部 5 個數值指標，使用 `statistics.mean()` 與 `statistics.stdev()` 精確計算：
   - 樣本數 ($N=10$)
   - 平均值 ($\text{Mean}$，四捨五入至小數點後 2 位)
   - 樣本標準差 ($\text{SD}$，四捨五入至小數點後 2 位)
   - 最小值 ($\text{Min}$) 與最大值 ($\text{Max}$)
3. 計算 `Study_Hours_Per_Week`（每週學習時數）與 `Overall_Satisfaction`（整體滿意度）之間的皮爾森相關係數（Pearson Correlation $r$）。

### 步驟 2：生成互動式視覺化圖表報告 (`eval_report.html`)
根據步驟 1 Python 輸出的真實數據，呼叫 `write_workspace_file` 寫入 `output/eval_report.html`。
- 必須為**單一檔案 HTML5 互動視覺化儀表板**（引入 Chart.js CDN `https://cdn.jsdelivr.net/npm/chart.js` 或使用精美內嵌 SVG 圖表）：
  1. **頂部關鍵指標卡片 (KPI Cards)**：顯示樣本數 $N=10$、整體滿意度平均分、最高分維度（講解清晰度 Clarity Score）與待改進維度（回饋實用性 Feedback Helpfulness）及相關係數 $r$。
  2. **左圖（互動柱狀圖 Bar Chart）**：呈現四項 5 分制教學評鑑指標的平均值（Mean）與 4.0 分學系基準線對比。
  3. **右圖（散佈圖 Scatter Plot）**：呈現每週學習時數（X 軸）與整體滿意度（Y 軸）的正相關分佈。
  4. **下方描述性統計表格與行動方案摘要**。

### 步驟 3：撰寫學系教學檢討報告 (`department_summary.md`)
呼叫 `write_workspace_file` 將結構嚴謹的《學系期末教學評估與質素保證檢討報告》寫入 `output/department_summary.md`（使用**繁體中文**，保留關鍵統計與教學術語**中英對照**）：
1. **📋 執行摘要 (Executive Summary)**。
2. **📊 描述性統計匯總表 (Descriptive Statistics Table)**：完整呈現 5 個指標的 Mean、SD、Min、Max（與步驟 1 Python 計算結果 100% 一致）。
3. **🔍 關鍵數據洞察 (Key Quantitative Insights)**：分析優勢項目、待補強痛點（`Feedback_Helpfulness` 平均分最低）及學習時數與滿意度之強正相關。
4. **🚀 下學期具體教學行動方案 (Action Plan for Next Semester)**：提出 3 項具體可落地的跨學科教學改進建議（如期中形成性回饋 Formative Feedback Checkpoints、AI 蘇格拉底評語支架等）。
