# 🎓 香港大專院校跨學科 Gemini Agent Harness 實戰工作坊 (`gemini-faculty-workshop`)

歡迎參加 **1 小時 Gemini Agent Harness 跨學科教學實戰工作坊**！本專案專為**香港大專院校跨學科講師與教授（人文、社科、商管、教育、心理、醫護、社工）**設計，無需任何軟件工程背景，即可透過 **GitHub Codespaces** 雲端環境，體驗如何用「全域教學規範 (`AGENTS.md`) + 學科專屬技能 (`SKILL.md`) + Python 實證工具」打造零幻覺的 AI 教學助教。

---

## 🌟 為什麼教授需要 Agent Harness（而非單純聊天室對話）？

在一般網頁版聊天室中，大型語言模型常出現「心算錯字數、捏造統計平均值、直接幫學生代寫整篇作業」等問題。本工作坊展示的 **Agent Harness 架構** 具備三大優勢：

1. **全域教學護欄 (`.agents/AGENTS.md`)**：統一規定繁體中文（中英學術術語對照）與**蘇格拉底式引導（Socratic Scaffolding，給提示不代寫）**。
2. **工具實證守則 (`run_python_script`)**：凡涉及字數統計、APA 第 7 版引用檢核、Rubric 配分加總或問卷統計（Mean / SD），AI 必須先自動執行 Python 驗算，**100% 杜絕算術幻覺**。
3. **雙通道一秒切換 (`OpenRouter` ⇄ `Poe`)**：課堂使用工作坊通道，課後回校或在家可一秒切換至**香港免 VPN 直連的 Poe API (`Gemini-3.1-Pro`)**。

---

## 🚀 一、課堂一鍵執行指令 (Quick Start Commands)

開啟終端機（Terminal）後，您可先執行 `--dry-run` 進行**零 Token 消耗的環境與設定自檢**，再正式執行四大跨學科教學情境（Use Cases）：

### 1. 環境與雙通道自檢（不消耗 Token）
```bash
# 檢查四大跨學科情境（預設 OpenRouter 通道）
python3 switch_provider.py --case 1 --dry-run
python3 switch_provider.py --case 2 --dry-run
python3 switch_provider.py --case 3 --dry-run
python3 switch_provider.py --case 4 --dry-run

# 測試一秒切換至香港免 VPN 之 Poe 通道 (Gemini-3.1-Pro)
python3 switch_provider.py --case 1 --provider poe --dry-run
```

### 2. 四大跨學科實戰情境一鍵執行

| 指令 | 跨學科定位 | 技能模組 (`SKILL.md`) | 讀取教材 (`workspace/input/`) | 自動生成產出 (`workspace/output/`) |
| :--- | :--- | :--- | :--- | :--- |
| `python3 switch_provider.py --case 1` | **全學科通用** | `quiz-builder` | `lecture_notes.md` | `pre_class_quiz.html`（含即時批改與思考提示之互動網頁） |
| `python3 switch_provider.py --case 2` | **人文 / 社科 / 商管** | `essay-grader` | `student_essay.txt` | `essay_feedback.md` + `grading_sheet.csv`（Python 實測字數與 APA 引用） |
| `python3 switch_provider.py --case 3` | **教育 / 心理 / 醫護 / 社工** | `survey-analyst` | `course_eval.csv` | `eval_chart.png` + `department_summary.md`（Python 算 Mean/SD 並畫圖） |
| `python3 switch_provider.py --case 4` | **社工 / 護理 / 管理** | `case-simulator` | `lecture_notes.md` | `student_case_brief.md` + `instructor_debrief_guide.md`（Python 驗算 100 分配分） |

---

## 🛠️ 二、如何自訂您的教學規範與學科技能（零程式碼修改）

在本專案中，您**完全不需要修改任何 `.py` 程式碼**，只需用編輯器打開以下 Markdown 純文字檔，像寫課程大綱一樣用中文修改即可：

### 1. 修改全域教學風格：`.agents/AGENTS.md`
打開 `.agents/AGENTS.md`，您可以隨時調整：
- **語言偏好**：例如改為「全英文撰寫回饋，但附上繁體中文重點摘要」。
- **教學法護欄 (Pedagogical Guardrails)**：例如規定「針對大一新生，每段評語必須先列出 2 個具體優點，再提出 1 個蘇格拉底式引導問題」。

### 2. 修改各科批改與出題邏輯：`.agents/skills/<skill-name>/SKILL.md`
每個技能檔頂部都有標準 YAML 標題（`name` 與 `description`），下方則是明確的教學步驟：
- **想改課前測驗題數或情境？** 打開 `.agents/skills/quiz-builder/SKILL.md`，將「3 題四選一」改為「5 題情境題」，或將香港例子改為您學科的案例（如香港建築法規、醫管局臨床指引、香港金融監管案例）。
- **想調整作文評分標準 (Rubric)？** 打開 `.agents/skills/essay-grader/SKILL.md`，修改步驟 3 的配分比重（例如將「論點結構 40%、實證與 APA 引用 30%、學術表達 30%」改為您課程的專屬 Rubric）。
- **想替換成您真實的講義或學生作業？** 直接將您的檔案放進 `workspace/input/` 覆蓋對應檔案，重新執行指令即可在 `workspace/output/` 取得最新產出！

---

## 🔑 三、課後在香港免 VPN 切換個人 API Key 指南

工作坊結束後，您可隨時在個人電腦或 GitHub Codespaces 中切換使用自己的 API Key。我們提供**雙通道一秒切換**設計：

### 方案 A：使用 Poe API（香港大專院校免 VPN 首選推薦 🇭🇰）
如果您身處香港且已訂閱 Poe（或希望免 VPN 穩定直連 `Gemini-3.1-Pro`）：
1. 前往 Poe 官方金鑰頁面：**[https://poe.com/api/keys](https://poe.com/api/keys)**
2. 點擊 **Create Key** 複製您的個人 API Key。
3. 打開專案根目錄的 `.env` 檔案，修改以下兩行：
   ```env
   ACTIVE_PROVIDER=poe
   POE_API_KEY=貼上您的_Poe_API_Key
   ```
   *(您也可以在執行指令時直接加上 `--provider poe` 參數一秒切換！)*

### 方案 B：使用 OpenRouter API（跨模型彈性實驗）
如果您希望按量付費（Pay-as-you-go）並自由測試 `google/gemini-2.5-flash` 或其他開源/商業模型：
1. 前往 OpenRouter 金鑰頁面：**[https://openrouter.ai/keys](https://openrouter.ai/keys)**
2. 點擊 **Create Key** 複製以 `sk-or-v1-` 開頭的金鑰。
3. 打開專案根目錄的 `.env` 檔案，修改以下兩行：
   ```env
   ACTIVE_PROVIDER=openrouter
   OPENROUTER_API_KEY=sk-or-v1-貼上您的_OpenRouter_Key
   ```

---

## 📁 四、專案目錄結構一覽

```text
gemini-faculty-workshop/
├── .devcontainer/
│   └── devcontainer.json          # GitHub Codespaces Python 3.12 自動化環境配置
├── .agents/
│   ├── AGENTS.md                  # 教授專屬全域教學規範（中英對照、Python 實證、蘇格拉底引導）
│   └── skills/                    # 四大跨學科教學技能模組
│       ├── quiz-builder/SKILL.md  # [Case 1] 課前互動選擇題網頁生成器
│       ├── essay-grader/SKILL.md  # [Case 2] 英文短文實證批改與 APA 引用檢核
│       ├── survey-analyst/SKILL.md# [Case 3] 期末問卷量化分析與圖表生成
│       └── case-simulator/SKILL.md# [Case 4] 香港情境案例模擬與雙軌評核指南
├── workspace/
│   ├── input/                     # 模擬教學輸入素材（講義、學生短文、教學評估 CSV）
│   │   ├── lecture_notes.md
│   │   ├── student_essay.txt
│   │   └── course_eval.csv
│   └── output/                    # AI 助教自動生成之互動網頁、評語、圖表與成績單
│       └── .gitkeep
├── .env.example                   # 雙通道環境變數範本（OpenRouter / Poe）
├── .env                           # 本地雙通道設定檔（已加入 .gitignore 保護金鑰安全）
├── .gitignore                     # Git 忽略規則
├── switch_provider.py             # 零外部依賴雙通道 Agent 執行器（內建 3 工具與 6 回合迴圈）
└── README.md                      # 教授課堂與課後操作指南
```
