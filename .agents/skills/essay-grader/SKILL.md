---
name: essay-grader
description: 讀取學生英文短文 (workspace/input/student_essay.txt)，先以 Python 精確計算字數、句子數並以 Regex 提取所有 APA 引用，再依評分標準 (Rubric) 產出蘇格拉底式引導評語 workspace/output/essay_feedback.md 與成績表 workspace/output/grading_sheet.csv。適用於人文、社科與商管學科。
---

# 學生短文實證批改與蘇格拉底回饋技能 (Evidence-Based Essay Grader)

## 適用對象與教學場景
- **適用學科**：人文學科、社會科學、商管學院、語言中心及大專通識英文寫作課。
- **教學目標**：結合「Python 客觀數據實證檢核（字數、句數、APA 引用格式）」與「生成式 AI 質性評量」，杜絕大型語言模型常見的算錯字數問題，並提供符合蘇格拉底教學法（Socratic Scaffolding）的啟發式寫作回饋。

---

## 執行步驟 (Step-by-Step Workflow)

### 步驟 1：讀取學生短文
1. 呼叫 `read_workspace_file` 讀取 `workspace/input/student_essay.txt` 的完整內容。

### 步驟 2：使用 Python 進行客觀文本數據與 APA 引用檢核（強制步驟）
**嚴禁憑感覺心算字數或人工目視數引用！** 必須呼叫 `run_python_script` 執行一段 Python 腳本，對 `workspace/input/student_essay.txt` 進行以下精確分析並印出 JSON 或結構化結果：
1. **總字數 (Total Word Count)**：以空白分詞統計精確字數（並檢查是否符合約 150 字的作業要求，例如 130–170 字區間）。
2. **句子總數 (Sentence Count)** 與 **平均句長 (Average Words per Sentence)**。
3. **APA 第 7 版文內引用提取 (In-text Citations via Regex)**：
   - 使用正規表達式（例如 `r'\([A-Za-z\s&.,]+,\s*\d{4}[a-z]?\)'`）提取文中所有 `(Author, YYYY)` 或 `(Author & Author, YYYY)` 格式的引用（例如 `(Smith, 2023)`、`(Chan & Lee, 2024)`），並統計引用次數。

### 步驟 3：依評分標準 (Rubric) 進行分析與給分
根據步驟 1 的文本內容與步驟 2 的 Python 實證數據，按照以下三大維度進行評分（滿分 100 分，並可在 Python 內一併驗算加權總分）：
1. **論點結構與批判性思考 (Argument Structure & Critical Thinking) — 佔 40%（滿分 40 分）**
   - 評估主題句（Topic Sentence）、正反論證平衡、因果推論邏輯及結論建議的可行性。
2. **實證支持與 APA 引用規範 (Empirical Evidence & APA 7th Citation) — 佔 30%（滿分 30 分）**
   - 根據 Python 提取出的引用清單，評估文內引用格式是否正確、引用是否有效支撐論點、以及是否缺乏具體數據或文獻書目（Reference List）呼應。
3. **學術表達與語法準確度 (Academic Expression & Cohesion) — 佔 30%（滿分 30 分）**
   - 評估學術詞彙運用（Academic Register）、段落轉折詞（Transitions）、句型多樣性及字數控制。

### 步驟 4：輸出詳細評語與成績表
請透過 `write_workspace_file`（或由 `run_python_script` 輔助）生成以下兩個檔案：

1. **詳細學生回饋報告 `workspace/output/essay_feedback.md`**：
   - 使用**繁體中文**撰寫，關鍵學術與寫作術語保留**中英對照**。
   - 包含：
     - **📊 客觀文本檢核摘要表**（列出 Python 實測之總字數、句子數、平均句長、提取出的 APA 引用清單）。
     - **🏆 各維度評分明細表**（列出三大維度得分、權重、加權總分與等第，如 `A-` / `B+`）。
     - **🌟 寫作亮點肯定 (Strengths)**：具體指出文中寫得好的論點或詞彙。
     - **🧭 蘇格拉底式改進引導 (Socratic Scaffolding & Actionable Hints)**：針對論點深度、實證細節與結尾建議，提出 2–3 個啟發式問題與具體修改提示（**嚴禁直接代寫整篇範文**，僅可提供 1–2 句句型升級示範）。

2. **結構化成績表 `workspace/output/grading_sheet.csv`**：
   - 包含欄位：`Essay_File,Word_Count,Sentence_Count,APA_Citations_Found,Argument_Score_40,Evidence_APA_Score_30,Expression_Score_30,Total_Score_100,Letter_Grade,Key_Recommendation`
   - 寫入該篇短文的精確統計與評分紀錄，方便教授直接匯入 Moodle / Canvas / Excel。
