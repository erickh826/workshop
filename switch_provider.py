#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gemini-faculty-workshop: 零外部套件依賴之雙通道 Agent Harness 執行器 (switch_provider.py)
專為香港大專院校跨學科教授及講師工作坊設計。
支援 OpenRouter 與 Poe (香港免 VPN) 雙通道一秒切換，內建 3 個沙盒工具與 6 回合 Tool Calling Loop。
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

# 確保跨平台終端機（特別是 Windows PowerShell / CMD）支援繁體中文與 Emoji 輸出
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).resolve().parent
WORKSPACE_DIR = ROOT_DIR / "workspace"
AGENTS_MD_PATH = ROOT_DIR / ".agents" / "AGENTS.md"
ENV_PATH = ROOT_DIR / ".env"

MAX_TOOL_TURNS = 6

# 四大跨學科教學情境設定
CASES = {
    1: {
        "id": 1,
        "skill": "quiz-builder",
        "title": "Use Case 1：全學科通用 — 課前互動選擇題網頁生成 (Pre-Class Interactive Quiz)",
        "discipline": "全學科通用 (All Disciplines)",
        "input_file": "workspace/input/lecture_notes.md",
        "expected_outputs": ["workspace/output/pre_class_quiz.html"],
        "user_prompt": (
            "請依照 quiz-builder 技能規範，先讀取 `workspace/input/lecture_notes.md`，"
            "針對「錨定效應、損失規避、現狀偏差」設計 3 題貼近香港生活情境的四選一選擇題（含思考提示 Hint 與詳解），"
            "並將包含美觀 CSS 與點擊即時批改 JavaScript 的單一檔案互動網頁寫入 `workspace/output/pre_class_quiz.html`。"
        ),
    },
    2: {
        "id": 2,
        "skill": "essay-grader",
        "title": "Use Case 2：人文/社科/商管 — 英文短文實證批改與蘇格拉底回饋 (Evidence-Based Essay Grader)",
        "discipline": "人文 / 社科 / 商管 (Humanities, Social Sciences & Business)",
        "input_file": "workspace/input/student_essay.txt",
        "expected_outputs": [
            "workspace/output/essay_feedback.md",
            "workspace/output/grading_sheet.csv",
        ],
        "user_prompt": (
            "請依照 essay-grader 技能規範，先讀取 `workspace/input/student_essay.txt`，"
            "接著務必呼叫 `run_python_script` 精確計算總字數、句子數並用 Regex 提取所有 `(Author, YYYY)` APA 引用，"
            "再依 Rubric（論點結構 40%、實證與 APA 引用 30%、學術表達 30%）產出蘇格拉底式引導評語 "
            "`workspace/output/essay_feedback.md` 及成績表 `workspace/output/grading_sheet.csv`。"
        ),
    },
    3: {
        "id": 3,
        "skill": "survey-analyst",
        "title": "Use Case 3：教育/心理/醫護/社工 — 期末教學評估統計分析與視覺化 (Course Evaluation Analyst)",
        "discipline": "教育 / 心理 / 醫護 / 社工 (Education, Psychology, Healthcare & Social Work)",
        "input_file": "workspace/input/course_eval.csv",
        "expected_outputs": [
            "workspace/output/eval_chart.png",
            "workspace/output/department_summary.md",
        ],
        "user_prompt": (
            "請依照 survey-analyst 技能規範，先呼叫 `run_python_script` 讀取 `workspace/input/course_eval.csv`，"
            "精確計算各指標的平均值（Mean）與標準差（SD），並繪製視覺化統計圖表儲存至 `workspace/output/eval_chart.png`，"
            "最後根據真實統計數據撰寫學系教學檢討報告 `workspace/output/department_summary.md`。"
        ),
    },
    4: {
        "id": 4,
        "skill": "case-simulator",
        "title": "Use Case 4：社工/護理/管理 — 香港情境案例模擬與雙軌評核指南 (Localized Case Simulator)",
        "discipline": "社工 / 護理 / 管理 (Social Work, Nursing & Management)",
        "input_file": "workspace/input/lecture_notes.md",
        "expected_outputs": [
            "workspace/output/student_case_brief.md",
            "workspace/output/instructor_debrief_guide.md",
        ],
        "user_prompt": (
            "請依照 case-simulator 技能規範，先呼叫 `run_python_script` 驗算評分表（Rubric）各維度配分總和必等於 100 分，"
            "並參考 `workspace/input/lecture_notes.md` 的行為決策概念，生成香港本地化跨專業情境案例："
            "「學生派發版」`workspace/output/student_case_brief.md` 與「導師保密評核及引導提問版」"
            "`workspace/output/instructor_debrief_guide.md`。"
        ),
    },
}


def load_dotenv(env_file: Path) -> dict:
    """使用純標準庫解析 .env 檔案，不依賴 python-dotenv。"""
    env_vars = {}
    if not env_file.exists():
        return env_vars
    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        key = key.strip()
        val = val.strip().strip("'").strip('"')
        env_vars[key] = val
    return env_vars


def resolve_provider_config(cli_provider: str | None, env_vars: dict) -> dict:
    """決定當前啟用的 API 通道（OpenRouter 或 Poe）與對應參數。"""
    provider = (
        cli_provider
        or os.environ.get("ACTIVE_PROVIDER")
        or env_vars.get("ACTIVE_PROVIDER")
        or "openrouter"
    ).strip().lower()

    if provider == "poe":
        base_url = (
            os.environ.get("POE_BASE_URL")
            or env_vars.get("POE_BASE_URL")
            or "https://api.poe.com/v1"
        )
        model = (
            os.environ.get("POE_MODEL")
            or env_vars.get("POE_MODEL")
            or "Gemini-3.1-Pro"
        )
        api_key = (
            os.environ.get("POE_API_KEY")
            or env_vars.get("POE_API_KEY")
            or ""
        )
    elif provider == "openrouter":
        base_url = (
            os.environ.get("OPENROUTER_BASE_URL")
            or env_vars.get("OPENROUTER_BASE_URL")
            or "https://openrouter.ai/api/v1"
        )
        model = (
            os.environ.get("OPENROUTER_MODEL")
            or env_vars.get("OPENROUTER_MODEL")
            or "google/gemini-2.5-flash"
        )
        api_key = (
            os.environ.get("OPENROUTER_API_KEY")
            or env_vars.get("OPENROUTER_API_KEY")
            or ""
        )
    else:
        raise ValueError(f"不支援的 provider: {provider}（僅支援 'openrouter' 或 'poe'）")

    is_placeholder = (
        not api_key
        or "replace-with-your" in api_key
        or api_key.startswith("your_")
    )
    return {
        "provider": provider,
        "base_url": base_url.rstrip("/"),
        "endpoint": f"{base_url.rstrip('/')}/chat/completions",
        "model": model,
        "api_key": api_key,
        "has_valid_key": not is_placeholder,
    }


def parse_skill_frontmatter(skill_text: str) -> dict:
    """使用純標準庫解析 SKILL.md 的 YAML frontmatter (name, description)。"""
    meta = {}
    lines = skill_text.splitlines()
    if not lines or lines[0].strip() != "---":
        return meta
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip().strip('"').strip("'")
    return meta


# ==============================================================================
# 三大內建沙盒工具 (Built-in Sandbox Tools)
# ==============================================================================

def _resolve_sandbox_path(rel_path: str, require_output_dir: bool = False) -> Path:
    """確保檔案讀寫嚴格限制在專案 workspace/ 目錄內，防止路徑穿越。"""
    clean_rel = rel_path.strip().replace("\\", "/")
    target = (ROOT_DIR / clean_rel).resolve()
    workspace_resolved = WORKSPACE_DIR.resolve()
    output_resolved = (WORKSPACE_DIR / "output").resolve()

    if not str(target).startswith(str(workspace_resolved)):
        raise PermissionError(
            f"沙盒安全攔截：禁止存取 workspace/ 以外的路徑 ({rel_path})。"
        )
    if require_output_dir and not str(target).startswith(str(output_resolved)):
        raise PermissionError(
            f"教學規範攔截：所有生成檔案必須寫入 workspace/output/ 目錄內 ({rel_path})。"
        )
    return target


def read_workspace_file(path: str) -> str:
    """沙盒工具 1：讀取 workspace/ 內的檔案內容。"""
    try:
        target = _resolve_sandbox_path(path, require_output_dir=False)
        if not target.exists():
            return f"Error: 找不到檔案 '{path}'。"
        content = target.read_text(encoding="utf-8")
        return content
    except Exception as exc:
        return f"Error reading file '{path}': {exc}"


def write_workspace_file(path: str, content: str) -> str:
    """沙盒工具 2：將生成的教材、報告或 CSV 寫入 workspace/output/ 目錄。"""
    try:
        target = _resolve_sandbox_path(path, require_output_dir=True)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        size_bytes = target.stat().st_size
        return (
            f"Success: 已成功寫入檔案 '{path}' "
            f"（共 {len(content)} 字元，{size_bytes} bytes）。"
        )
    except Exception as exc:
        return f"Error writing file '{path}': {exc}"


def run_python_script(code: str) -> str:
    """沙盒工具 3：在本地子行程中執行 Python 驗證或繪圖腳本，回傳真實 stdout/stderr。"""
    try:
        (WORKSPACE_DIR / "output").mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".py",
            dir=str(ROOT_DIR),
            encoding="utf-8",
            delete=False,
        ) as tmp_file:
            tmp_path = Path(tmp_file.name)
            tmp_file.write(code)

        try:
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            result = subprocess.run(
                [sys.executable, str(tmp_path)],
                cwd=str(ROOT_DIR),
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=30,
                env=env,
            )
            stdout_str = result.stdout.strip()
            stderr_str = result.stderr.strip()
            output_parts = [f"Exit Code: {result.returncode}"]
            if stdout_str:
                output_parts.append(f"STDOUT:\n{stdout_str}")
            if stderr_str:
                output_parts.append(f"STDERR:\n{stderr_str}")
            return "\n".join(output_parts)
        finally:
            if tmp_path.exists():
                tmp_path.unlink()
    except Exception as exc:
        return f"Error executing Python script: {exc}"


TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "read_workspace_file",
            "description": "讀取 workspace/ 目錄下的教學輸入檔案（如 workspace/input/lecture_notes.md）。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "相對於專案根目錄的檔案路徑，例如 'workspace/input/lecture_notes.md'",
                    }
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_workspace_file",
            "description": "將生成的教材、評語報告或 CSV 寫入 workspace/output/ 目錄下。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "相對於專案根目錄的輸出檔案路徑，必須位於 'workspace/output/' 下",
                    },
                    "content": {
                        "type": "string",
                        "description": "要寫入檔案的完整文字內容（HTML、Markdown 或 CSV）",
                    },
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_python_script",
            "description": (
                "執行 Python 3 程式碼以進行精確字數統計、Regex 引用提取、Rubric 配分驗算、"
                "CSV 問卷統計分析（Mean/SD）或繪製圖表（儲存至 workspace/output/）。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "要執行的完整 Python 程式碼（請使用 print() 輸出計算結果）",
                    }
                },
                "required": ["code"],
            },
        },
    },
]

TOOL_DISPATCH = {
    "read_workspace_file": lambda args: read_workspace_file(args.get("path", "")),
    "write_workspace_file": lambda args: write_workspace_file(
        args.get("path", ""), args.get("content", "")
    ),
    "run_python_script": lambda args: run_python_script(args.get("code", "")),
}


# ==============================================================================
# OpenAI 相容端點呼叫與多回合 Tool Calling Loop
# ==============================================================================

def call_chat_completions(provider_cfg: dict, messages: list, tools: list) -> dict:
    """使用標準庫 urllib.request 呼叫 OpenAI 相容之 /chat/completions 端點。"""
    payload = {
        "model": provider_cfg["model"],
        "messages": messages,
        "tools": tools,
        "tool_choice": "auto",
        "temperature": 0.2,
    }
    data = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {provider_cfg['api_key']}",
        "User-Agent": "gemini-faculty-workshop/1.0",
    }
    if provider_cfg["provider"] == "openrouter":
        headers["HTTP-Referer"] = "https://github.com/gemini-faculty-workshop"
        headers["X-Title"] = "HK Faculty Gemini Agent Workshop"

    for attempt in range(1, 4):
        req = urllib.request.Request(
            provider_cfg["endpoint"], data=data, headers=headers, method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                body = resp.read().decode("utf-8")
                return json.loads(body)
        except urllib.error.HTTPError as http_err:
            err_body = http_err.read().decode("utf-8", errors="replace")
            # 若在香港本地網路 (非 GitHub Codespaces) 直連 OpenRouter 的 Google 模型遭遇 HTTP 403 地區限制，自動切換至香港免 VPN 的 Poe 通道
            if http_err.code == 403 and provider_cfg["provider"] == "openrouter":
                env_vars = load_dotenv(ENV_PATH)
                poe_cfg = resolve_provider_config("poe", env_vars)
                if poe_cfg["has_valid_key"]:
                    print(
                        "   ⚠️ [香港本地網路偵測] OpenRouter 上游 Google 節點限制香港 IP 直連 (HTTP 403)。\n"
                        f"   🔄 自動無縫切換至香港免 VPN 之 POE 通道 ({poe_cfg['model']}) 繼續執行..."
                    )
                    provider_cfg.update(poe_cfg)
                    return call_chat_completions(provider_cfg, messages, tools)
            raise RuntimeError(
                f"HTTP {http_err.code} 錯誤 ({provider_cfg['endpoint']}): {err_body}"
            ) from http_err
        except Exception as net_err:
            if attempt < 3:
                print(f"   ⚠️ 網路連線瞬斷 ({net_err})，正在進行第 {attempt + 1}/3 次自動重試...")
                continue
            raise RuntimeError(
                f"網路連線失敗 ({provider_cfg['endpoint']}): {net_err}"
            ) from net_err


def run_dry_run(case_info: dict, provider_cfg: dict, skill_path: Path, skill_meta: dict) -> int:
    """執行 --dry-run 本地環境、教學規範、技能檔與雙通道設定完整性自檢（不消耗 Token）。"""
    input_path = ROOT_DIR / case_info["input_file"]
    output_dir = WORKSPACE_DIR / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    # 測試沙盒讀取與 Python 子行程是否正常運作
    sample_read = read_workspace_file(case_info["input_file"])
    read_ok = not sample_read.startswith("Error:")
    py_check = run_python_script("import sys; print('Python OK:', sys.version.split()[0])")
    py_ok = "Exit Code: 0" in py_check

    print("=" * 76)
    print("🎓 [Gemini Agent Harness 工作坊] --dry-run 環境與雙通道自檢報告")
    print("=" * 76)
    print(f"📌 選擇情境   : {case_info['title']}")
    print(f"🏛️  適用學科   : {case_info['discipline']}")
    print("-" * 76)
    print("🔌 【雙通道 API 設定狀態】")
    print(f"   • 啟用通道 (Provider) : {provider_cfg['provider'].upper()}")
    print(f"   • 端點網址 (Endpoint) : {provider_cfg['endpoint']}")
    print(f"   • 指定模型 (Model)    : {provider_cfg['model']}")
    key_status = (
        "✅ 已配置有效金鑰"
        if provider_cfg["has_valid_key"]
        else "⚠️ 尚未填入個人金鑰 (目前為範本預設值，Dry-Run 模式無需消耗 Token)"
    )
    print(f"   • 金鑰狀態 (API Key)  : {key_status}")
    print("-" * 76)
    print("📂 【Agent Harness 檔案架構與技能檢查】")
    print(
        f"   • 全域規範 (.agents/AGENTS.md)          : "
        f"{'✅ 存在' if AGENTS_MD_PATH.exists() else '❌ 缺失'} ({AGENTS_MD_PATH.stat().st_size if AGENTS_MD_PATH.exists() else 0} bytes)"
    )
    print(
        f"   • 技能定義 (.agents/skills/{case_info['skill']}/SKILL.md) : "
        f"{'✅ 存在' if skill_path.exists() else '❌ 缺失'}"
    )
    print(f"     ├─ YAML name        : {skill_meta.get('name', '❌ 未定義')}")
    print(f"     └─ YAML description : {skill_meta.get('description', '❌ 未定義')[:60]}...")
    print(
        f"   • 教學輸入 ({case_info['input_file']}) : "
        f"{'✅ 可讀取' if (input_path.exists() and read_ok) else '❌ 無法讀取'} ({len(sample_read)} chars)"
    )
    print(
        f"   • 輸出目錄 (workspace/output/)          : "
        f"{'✅ 就緒' if output_dir.exists() else '❌ 缺失'}"
    )
    print(
        f"   • 預期產出檔案                          : "
        f"{', '.join(case_info['expected_outputs'])}"
    )
    print("-" * 76)
    print("🛠️  【內建沙盒工具鏈 (3 Sandbox Tools & 6-Turn Loop) 自檢】")
    print(f"   • Tool 1: read_workspace_file           : {'✅ 正常' if read_ok else '❌ 異常'}")
    print(f"   • Tool 2: write_workspace_file          : ✅ 沙盒路徑保護已啟用 (僅限 workspace/output/)")
    print(f"   • Tool 3: run_python_script             : {'✅ 正常 (' + py_check.splitlines()[-1] + ')' if py_ok else '❌ 異常'}")
    print(f"   • 最大工具呼叫回合數 (Max Tool Turns)    : {MAX_TOOL_TURNS} 回合")
    print("=" * 76)

    all_passed = (
        AGENTS_MD_PATH.exists()
        and skill_path.exists()
        and bool(skill_meta.get("name"))
        and bool(skill_meta.get("description"))
        and input_path.exists()
        and read_ok
        and py_ok
    )
    if all_passed:
        print(
            f"🎉 Dry-Run 檢核 100% 通過！(Case {case_info['id']} | Provider: {provider_cfg['provider'].upper()})"
        )
        return 0
    print("❌ Dry-Run 發現缺失項目，請檢查上方報告。")
    return 1


def run_agent_loop(case_info: dict, provider_cfg: dict, system_prompt: str) -> int:
    """執行最多 6 回合的 OpenAI 相容 Tool Calling Loop。"""
    if not provider_cfg["has_valid_key"]:
        print(
            f"⚠️ 尚未在 `.env` 設定有效的 `{provider_cfg['provider'].upper()}_API_KEY`。\n"
            f"   請先在 `.env` 填入 API Key，或加上 `--dry-run` 參數進行零 Token 環境自檢。"
        )
        return 1

    print("=" * 76)
    print(f"🚀 啟動 Gemini Agent Harness | {case_info['title']}")
    print(
        f"🔌 通道: {provider_cfg['provider'].upper()} | 模型: {provider_cfg['model']} | "
        f"端點: {provider_cfg['endpoint']}"
    )
    print("=" * 76)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": case_info["user_prompt"]},
    ]

    for turn in range(1, MAX_TOOL_TURNS + 1):
        print(f"\n🔄 [Turn {turn}/{MAX_TOOL_TURNS}] 正在呼叫模型思考與決策...")
        response = call_chat_completions(provider_cfg, messages, TOOLS_SCHEMA)
        choice = response.get("choices", [{}])[0]
        assistant_msg = choice.get("message", {})
        messages.append(assistant_msg)

        tool_calls = assistant_msg.get("tool_calls") or []
        if not tool_calls:
            final_text = assistant_msg.get("content") or ""
            print("\n" + "=" * 76)
            print("🎓 【AI 助教最終匯報】")
            print("=" * 76)
            print(final_text)
            print("=" * 76)
            return 0

        for tc in tool_calls:
            fn_info = tc.get("function", {})
            fn_name = fn_info.get("name", "")
            raw_args = fn_info.get("arguments", "{}")
            try:
                parsed_args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
            except json.JSONDecodeError:
                parsed_args = {}

            print(f"   🛠️  呼叫工具: `{fn_name}`")
            if fn_name in TOOL_DISPATCH:
                tool_output = TOOL_DISPATCH[fn_name](parsed_args)
            else:
                tool_output = f"Error: 未知的工具名稱 '{fn_name}'"

            preview = tool_output.replace("\n", " ")[:120]
            print(f"      ↳ 執行結果: {preview}...")

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.get("id", "call_default"),
                    "name": fn_name,
                    "content": tool_output,
                }
            )

    print(f"\n⚠️ 已達到最大工具呼叫回合數上限 ({MAX_TOOL_TURNS} 回合)，結束執行。")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="香港大專院校跨學科 Gemini Agent Harness 雙通道執行器 (OpenRouter / Poe)"
    )
    parser.add_argument(
        "--case",
        type=int,
        choices=[1, 2, 3, 4],
        default=1,
        help="選擇跨學科教學情境：1=課前互動測驗, 2=英文短文批改, 3=期末問卷分析, 4=香港情境個案模擬",
    )
    parser.add_argument(
        "--provider",
        type=str,
        choices=["openrouter", "poe"],
        default=None,
        help="一秒切換 API 通道：'openrouter' (工作坊預設) 或 'poe' (香港免 VPN 直連)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="僅檢查本地檔案、AGENTS.md、SKILL.md 與雙通道設定狀態，不發送網路請求亦不消耗 Token",
    )
    args = parser.parse_args()

    env_vars = load_dotenv(ENV_PATH)
    provider_cfg = resolve_provider_config(args.provider, env_vars)
    case_info = CASES[args.case]

    skill_path = ROOT_DIR / ".agents" / "skills" / case_info["skill"] / "SKILL.md"
    agents_md_text = (
        AGENTS_MD_PATH.read_text(encoding="utf-8") if AGENTS_MD_PATH.exists() else ""
    )
    skill_md_text = (
        skill_path.read_text(encoding="utf-8") if skill_path.exists() else ""
    )
    skill_meta = parse_skill_frontmatter(skill_md_text)

    if args.dry_run:
        return run_dry_run(case_info, provider_cfg, skill_path, skill_meta)

    system_prompt = (
        f"{agents_md_text}\n\n"
        f"====================================================================\n"
        f"當前啟用之專屬教學技能 ({case_info['skill']})\n"
        f"====================================================================\n"
        f"{skill_md_text}"
    )
    return run_agent_loop(case_info, provider_cfg, system_prompt)


if __name__ == "__main__":
    sys.exit(main())
