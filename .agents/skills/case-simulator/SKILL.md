---
name: case-simulator
description: 先以 Python 驗算評分表 (Rubric) 各維度配分總和必等於 100 分，再自動生成香港本地化跨專業情境案例「學生派發版」workspace/output/student_case_brief.md 與「導師保密評核及引導提問版」workspace/output/instructor_debrief_guide.md。適用於社工、護理與管理學科。
---

# 香港情境個案模擬與雙軌教材生成器 (Localized Case Simulator & Dual-Track Brief Builder)

## 適用對象與教學場景
- **適用學科**：社會工作（Social Work）、護理及醫療科學（Nursing & Allied Health）、公共行政與企業管理（Public & Business Management）。
- **教學目標**：解決實務學科教授撰寫「問題導向學習（Problem-Based Learning, PBL）」及「情境模擬演練（Role-Play / Case Simulation）」教材耗時費力的痛點。一次自動生成兩份嚴格分離的教材：**給學生的公開個案簡報**（不含答案與評分細節）與**給導師的保密帶領指南**（含經 Python 驗算 100% 準確的評分表與蘇格拉底式追問劇本）。

---

## 執行步驟 (Step-by-Step Workflow)

### 步驟 1：讀取課程背景並用 Python 驗算評分表配分（強制步驟）
1. 可先呼叫 `read_workspace_file` 參考 `workspace/input/lecture_notes.md` 中的決策心理學或行為概念（如：現狀偏差 Status Quo Bias、損失規避 Loss Aversion、危機溝通與倫理兩難），將其融入跨專業實務個案中。
2. **強制 Python 配分驗算**：在撰寫導師評分表（Assessment Rubric）前，必須先呼叫 `run_python_script` 定義各評核維度及其配分權重，並用 `assert sum(weights.values()) == 100` 嚴格驗算**所有評分維度配分總和必等於 100 分**（同時驗證各等第如 Excellent / Proficient / Developing / Unsatisfactory 的分數區間無重疊或遺漏）。

### 步驟 2：設計香港在地化高擬真兩難個案 (Hong Kong Localized Dilemma Case)
設計一個背景設於**香港九龍東（如觀塘或深水埗）公共屋邨社區綜合服務中心 / 社區健康中心**的跨專業實務個案：
- **個案主角與情境**：例如 76 歲獨居長者陳伯（患有初期認知障礙徵兆與慢性高血壓，近期因現狀偏差拒絕接受社區日間護理轉介，同時懷疑墮入電話消費陷阱並抗拒動用儲蓄就醫，家屬遠在海外且意見分歧）。
- **核心挑戰**：融合專業倫理兩難（案主自決 Client Self-Determination vs. 安全保護 Duty of Care）、行為心理阻力（Status Quo Bias & Loss Aversion）及跨專業資源協調（社工、社區護士、中心督導）。

### 步驟 3：輸出「學生派發版」個案簡報 (`workspace/output/student_case_brief.md`)
呼叫 `write_workspace_file` 建立 `workspace/output/student_case_brief.md`（使用**繁體中文**，關鍵專業術語保留**中英對照**）：
- **注意保密界線**：此檔案供課堂直接派發給學生小組，**絕對不可包含標準答案、隱藏線索揭秘或詳細扣分細則**。
- **必備內容**：
  1. **個案編號與演練背景 (Case Overview & Setting)**：香港社區真實情境設定。
  2. **人物角色設定 (Stakeholder Profiles)**：陳伯、海外女兒、前線社工/社區護士、服務中心主任。
  3. **事件時間軸與現況困境 (Timeline & Presenting Dilemma)**。
  4. **小組演練任務 (Group Simulation Tasks — 20 分鐘課堂討論)**：要求學生在有限資訊下制定初步介入方案（Initial Intervention Plan）與溝通策略。
  5. **思考提示 (Scaffolding Hints)**：提供 3 個不劇透答案的思考方向。

### 步驟 4：輸出「導師保密評核及引導提問版」(`workspace/output/instructor_debrief_guide.md`)
呼叫 `write_workspace_file` 建立 `workspace/output/instructor_debrief_guide.md`（標註「🔒 導師專用保密文件 Instructor Eyes Only」）：
- **必備內容**：
  1. **教學目標與理論連結 (Learning Objectives & Theoretical Mapping)**：如何結合專業倫理與行為經濟學（現狀偏差、損失規避、助推架構）解讀案主抗拒行為。
  2. **隱藏個案資訊與轉折點 (Hidden Case Triggers / Injects)**：當學生討論陷入僵局或過於表面時，導師可在第 10 分鐘拋出的突發情境變數。
  3. **蘇格拉底式小組帶領與追問劇本 (Socratic Debriefing Questions)**：提供三階段提問（事實釐清 → 倫理與心理機制剖析 → 方案可行性壓力測試），並列出「常見學生盲點 vs. 導師引導話術」。
  4. **經 Python 驗算之 100 分制結構化評分表 (Verified 100-Point Assessment Rubric)**：以 Markdown 表格清楚列出 4–5 個評核維度（總和嚴格等於 100 分，與步驟 1 Python 驗算結果完全一致）及各表現等第的具體評分準則。
