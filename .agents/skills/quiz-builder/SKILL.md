---
name: quiz-builder
description: 讀取課程講義 (workspace/input/lecture_notes.md)，自動設計 3 題貼近香港生活情境的四選一互動選擇題（含蘇格拉底思考提示 Hint 與詳解），並輸出單一檔案互動網頁 workspace/output/pre_class_quiz.html。適用於全學科課前預習與翻轉課堂。
---

# 課前互動測驗生成器 (Interactive Pre-Class Quiz Builder)

## 適用對象與教學場景
- **適用學科**：全學科通用（通識教育、商管、社科、理工及醫護導論課）。
- **教學目標**：將靜態的課程講義轉化為學生可在手機或電腦直接作答的「單一檔案互動預習網頁」，透過蘇格拉底式提示（Hint）降低挫折感，並於點擊選項時提供即時回饋（Immediate Formative Feedback）。

---

## 執行步驟 (Step-by-Step Workflow)

### 步驟 1：讀取課程講義
1. 呼叫 `read_workspace_file` 讀取 `workspace/input/lecture_notes.md`。
2. 擷取講義中的核心理論概念（例如：錨定效應 Anchoring Effect、損失規避 Loss Aversion、現狀偏差與預設效應 Status Quo Bias & Default Effect）及香港在地實例。

### 步驟 2：設計 3 題高層次香港情境四選一選擇題 (MCQs)
請根據布魯姆認知分類（Bloom's Taxonomy）的「應用（Application）」與「分析（Analysis）」層次，設計 **3 題四選一（A/B/C/D）選擇題**：
- **題目要求**：
  - 每題必須設定一個**貼近香港大學生或市民日常生活的真實決策情境**（例如：強積金 MPF 預設投資策略、超市原價/特價標示、外賣平台湊免運費、膠袋徵費、健身室免費試用自動續約等）。
  - 題幹與選項使用**繁體中文**，關鍵學術專有名詞保留**中英對照**。
  - 每題包含 4 個選項（A、B、C、D），其中僅有 1 個最佳答案，其餘 3 個誘答項（Distractors）需具備合理的迷思概念診斷價值。
- **支架與回饋要求**：
  - **思考提示 (Socratic Hint)**：每題提供一個可點擊展開的「💡 思考提示 (Hint)」，在不直接透露答案的前提下，引導學生回憶關鍵判斷準則。
  - **即時詳解 (Detailed Explanation)**：學生點擊任一選項後，立即顯示該題的完整解析（說明為何正確選項成立，以及常見錯誤選項的盲點）。

### 步驟 3：生成單一檔案互動網頁 (`workspace/output/pre_class_quiz.html`)
呼叫 `write_workspace_file` 將完整的 HTML5 程式碼寫入 `workspace/output/pre_class_quiz.html`。網頁必須為**零外部依賴的單一檔案（Self-contained Single-File HTML）**，內嵌完整 CSS 與 JavaScript，並符合以下規格：
1. **視覺設計 (Modern Academic UI)**：
   - 採用清晰、專業的大學教學介面設計（深藍/靛藍主色調、柔和灰白背景、卡片式題目區塊、圓角與陰影、支援手機與桌面響應式排版 Responsive Design）。
   - 頂部顯示課程標題、測驗說明與即時得分進度列（Score Tracker，例如：`目前已答對：X / 3 題`）。
2. **互動功能 (Interactive JavaScript)**：
   - 每道題目設有「💡 顯示思考提示 (Show Hint)」按鈕，點擊可切換顯示/隱藏提示框。
   - 學生點擊任一選項按鈕（A/B/C/D）後：
     - 若答對：選項標示為綠色（`#dcfce7` 背景、`#166534` 邊框与文字），顯示「✅ 答對了！」，並展開完整詳解。
     - 若答錯：所選項目標示為紅色（`#fee2e2`），同時標示出正確選項並顯示「❌ 再想一想！請參考下方解析：」與完整詳解。
   - 設有「🔄 重新作答 (Reset Quiz)」按鈕，方便課堂演示與學生反覆練習。

### 步驟 4：向教授匯報完成結果
完成檔案寫入後，以繁體中文向教授簡要摘要所設計的 3 道題目主題、對應的認知偏差概念，以及如何在瀏覽器開啟 `workspace/output/pre_class_quiz.html` 進行預覽。
