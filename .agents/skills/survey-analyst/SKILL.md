---
name: survey-analyst
description: 使用 Python 讀取期末教學評估問卷 (workspace/input/course_eval.csv)，精確計算各指標平均值與標準差，繪製視覺化圖表 workspace/output/eval_chart.png，並撰寫學系教學檢討報告 workspace/output/department_summary.md。適用於教育、心理、醫護與社工學科。
---

# 期末教學評估量化分析與視覺化技能 (Course Evaluation Survey Analyst)

## 適用對象與教學場景
- **適用學科**：教育學院、心理學系、護理及醫療科學、社會工作及跨學科課程委員會。
- **教學目標**：協助教師在學期結束時，自動對學生教學評估問卷（Student Evaluation of Teaching, SET）進行嚴謹的描述性統計分析（平均值 Mean、標準差 SD、相關性 Correlation），自動輸出出版級圖表與學系檢討報告，免除手動拉 Excel 圖表的繁瑣工序。

---

## 執行步驟 (Step-by-Step Workflow)

### 步驟 1：執行 Python 腳本計算統計數據並繪製圖表（強制步驟）
**嚴禁心算任何統計數字！** 必須先呼叫 `run_python_script` 執行 Python 程式碼（使用 `pandas`、`matplotlib` 或標準庫 `csv`/`statistics`），完成以下兩項任務：

1. **精確計算統計指標**：
   - 讀取 `workspace/input/course_eval.csv`（包含 10 位學生樣本，欄位為：`Student_ID`, `Clarity_Score`, `Engagement_Score`, `Feedback_Helpfulness`, `Overall_Satisfaction`, `Study_Hours_Per_Week`）。
   - 針對全部 5 個數值指標，計算並印出：
     - 樣本數 ($N$)
     - 平均值 ($\text{Mean}$，四捨五入至小數點後 2 位)
     - 樣本標準差 ($\text{SD}$，四捨五入至小數點後 2 位)
     - 最小值 ($\text{Min}$) 與最大值 ($\text{Max}$)
   - 額外計算 `Study_Hours_Per_Week`（每週學習時數）與 `Overall_Satisfaction`（整體滿意度）之間的皮爾森相關係數（Pearson Correlation $r$），以及識別得分最高與最低的教學評鑑維度。

2. **生成高解析度視覺化圖表 (`workspace/output/eval_chart.png`)**：
   - 在同一支或第二支 Python 腳本中，使用 `matplotlib` 繪製一張包含兩個子圖（Subplots）的專業統計圖表（使用英文圖表標籤以避免容器環境中文字型缺字問題，設定 `dpi=150` 及 `bbox_inches='tight'`）：
     - **左圖（Bar Chart with Error Bars）**：展示四項 5 分制教學評鑑指標（`Clarity_Score`, `Engagement_Score`, `Feedback_Helpfulness`, `Overall_Satisfaction`）的平均值（Mean）與標準差誤差線（$\pm 1\text{ SD}$），並在柱狀圖上方標註具體數值及加上 4.0 分基準虛線（Department Benchmark）。
     - **右圖（Scatter Plot with Trendline）**：展示 `Study_Hours_Per_Week` 與 `Overall_Satisfaction` 的散佈圖與線性趨勢線，呈現投入時間與滿意度之關係。
   - 將圖表儲存至 `workspace/output/eval_chart.png`。

### 步驟 2：撰寫學系教學檢討報告 (`workspace/output/department_summary.md`)
根據步驟 1 Python 腳本輸出的真實數據，呼叫 `write_workspace_file` 撰寫一份結構嚴謹的《學系期末教學評估與質素保證檢討報告》(Departmental Course Evaluation & Quality Assurance Summary)，寫入 `workspace/output/department_summary.md`。報告必須使用**繁體中文**（保留關鍵統計與教學術語**中英對照**），並包含：
1. **📋 執行摘要 (Executive Summary)**：概述樣本規模（$N=10$）、整體滿意度表現及核心發現。
2. **📊 描述性統計匯總表 (Descriptive Statistics Table)**：以 Markdown 表格完整呈現 5 個指標的 Mean、SD、Min、Max（數值必須與 Python 計算結果 100% 一致），並嵌入視覺化圖表連結 `![Course Evaluation Chart](eval_chart.png)`。
3. **🔍 關鍵數據洞察 (Key Quantitative Insights)**：
   - **優勢項目**：例如講解清晰度（Clarity Score）與整體滿意度（Overall Satisfaction）表現突出。
   - **待補強痛點**：指出「回饋實用性（Feedback Helpfulness）」平均分相對最低（且部分低投入時數學生給分偏低），為下學期首要改進目標。
   - **學習投入關聯分析**：解讀每週學習時數與滿意度的相關性。
4. **🚀 下學期具體教學行動方案 (Action Plan for Next Semester)**：提出 3 項具體、可落地的跨學科教學改進建議（例如：引入期中形成性回饋機制 Formative Feedback Checkpoints、結合 AI 助教提供即時評語支架、為低投入學生設計課前微任務等）。
