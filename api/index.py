#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vercel Pro Serverless Python Backend (api/run.py)
零外部套件依賴（僅使用 Python 3.12 標準庫），確保 Vercel Serverless 打包小於 250MB 且極速冷啟動。
支援 /tmp/<uuid>/ 獨立請求沙盒、OpenRouter / Poe 雙通道切換、3 大沙盒工具與最多 5 回合 Tool Calling Loop。
"""

import csv
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from pathlib import Path
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import uuid

ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT_DIR / ".env"
PUBLIC_DIR = ROOT_DIR / "public"
MAX_TOOL_TURNS = 5


def load_local_dotenv() -> dict:
    """若在本地端執行且存在 .env，使用標準庫讀取作為環境變數後備值。"""
    env_vars = {}
    if not ENV_PATH.exists():
        return env_vars
    try:
        for raw_line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env_vars[k.strip()] = v.strip().strip("'").strip('"')
    except Exception:
        pass
    return env_vars


def get_env_value(key: str, default: str = "", dotenv_cache: dict | None = None) -> str:
    """優先讀取 Vercel 系統環境變數 os.environ，其次讀取本地 .env。"""
    val = os.environ.get(key, "").strip()
    if val:
        return val
    if dotenv_cache and key in dotenv_cache:
        return dotenv_cache[key]
    return default


def resolve_provider(provider_name: str, custom_api_key: str) -> dict:
    """根據前端傳入的 provider ('openrouter' | 'poe') 與 custom_api_key 決定呼叫端點。"""
    dotenv_cache = load_local_dotenv()
    provider = (provider_name or "openrouter").strip().lower()
    clean_custom_key = (custom_api_key or "").strip()

    if provider == "poe":
        base_url = get_env_value("POE_BASE_URL", "https://api.poe.com/v1", dotenv_cache)
        model = get_env_value("POE_MODEL", "Gemini-3.1-Pro", dotenv_cache)
        api_key = clean_custom_key or get_env_value("POE_API_KEY", "", dotenv_cache)
    else:
        provider = "openrouter"
        base_url = get_env_value(
            "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1", dotenv_cache
        )
        model = get_env_value(
            "OPENROUTER_MODEL", "google/gemini-2.5-flash", dotenv_cache
        )
        api_key = clean_custom_key or get_env_value(
            "OPENROUTER_API_KEY", "", dotenv_cache
        )

    return {
        "provider": provider,
        "endpoint": f"{base_url.rstrip('/')}/chat/completions",
        "model": model,
        "api_key": api_key,
        "dotenv_cache": dotenv_cache,
    }


def create_isolated_sandbox(session_id: str, input_filename: str, input_content: str) -> Path:
    """
    在 Vercel 唯一可寫入的 /tmp/<uuid>/ 目錄下建立隔離沙盒，
    並將前端傳來的 input_content 寫入 /tmp/<uuid>/input/。
    """
    base_tmp = Path("/tmp")
    try:
        base_tmp.mkdir(parents=True, exist_ok=True)
        sandbox_root = base_tmp / session_id
        sandbox_root.mkdir(parents=True, exist_ok=True)
    except Exception:
        sandbox_root = Path(tempfile.gettempdir()) / session_id
        sandbox_root.mkdir(parents=True, exist_ok=True)

    input_dir = sandbox_root / "input"
    output_dir = sandbox_root / "output"
    ws_input_dir = sandbox_root / "workspace" / "input"
    ws_output_dir = sandbox_root / "workspace" / "output"

    for d in (input_dir, output_dir, ws_input_dir, ws_output_dir):
        d.mkdir(parents=True, exist_ok=True)

    safe_name = Path(input_filename or "input_data.txt").name
    # 同步寫入 input/<filename>、workspace/input/<filename> 與沙盒根目錄，確保模型任何相對路徑皆可讀取
    (input_dir / safe_name).write_text(input_content or "", encoding="utf-8")
    (ws_input_dir / safe_name).write_text(input_content or "", encoding="utf-8")
    (sandbox_root / safe_name).write_text(input_content or "", encoding="utf-8")

    return sandbox_root


def sandbox_read_file(sandbox_root: Path, req_path: str) -> str:
    """沙盒工具 1：讀取 /tmp/<uuid>/input/ 內的教材、論文或 CSV。"""
    try:
        clean_name = Path((req_path or "").strip().replace("\\", "/")).name
        candidates = [
            sandbox_root / "input" / clean_name,
            sandbox_root / (req_path or "").strip().lstrip("/"),
            sandbox_root / "workspace" / "input" / clean_name,
        ]
        for candidate in candidates:
            resolved = candidate.resolve()
            if str(resolved).startswith(str(sandbox_root.resolve())) and resolved.is_file():
                return resolved.read_text(encoding="utf-8")

        # 若僅有一個輸入檔，自動回傳該輸入檔內容，避免檔名微小差異導致失敗
        input_files = list((sandbox_root / "input").glob("*"))
        if len(input_files) == 1 and input_files[0].is_file():
            return input_files[0].read_text(encoding="utf-8")

        return f"Error: 在沙盒 input/ 目錄中找不到檔案 '{req_path}'。"
    except Exception as exc:
        return f"Error reading file '{req_path}': {exc}"


def sandbox_write_file(sandbox_root: Path, req_path: str, content: str) -> str:
    """沙盒工具 2：將生成的檔案寫入 /tmp/<uuid>/output/。"""
    try:
        safe_name = Path((req_path or "output.txt").strip().replace("\\", "/")).name
        if not safe_name:
            safe_name = "output.txt"
        target = (sandbox_root / "output" / safe_name).resolve()
        if not str(target).startswith(str((sandbox_root / "output").resolve())):
            return f"Error: 禁止寫入沙盒 output/ 以外的路徑 ({req_path})。"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content or "", encoding="utf-8")
        return (
            f"Success: 已成功寫入 '/tmp/{sandbox_root.name}/output/{safe_name}' "
            f"（共 {len(content or '')} 字元）。"
        )
    except Exception as exc:
        return f"Error writing file '{req_path}': {exc}"


def sandbox_run_python(sandbox_root: Path, code: str) -> str:
    """沙盒工具 3：在 /tmp/<uuid>/ 執行 Python 3.12 標準庫腳本（如 re, csv, statistics）。"""
    try:
        script_path = sandbox_root / f"_runner_{uuid.uuid4().hex[:8]}.py"
        script_path.write_text(code or "", encoding="utf-8")
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"

        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(sandbox_root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=25,
            env=env,
        )
        if script_path.exists():
            script_path.unlink()

        # 若 Python 腳本直接將檔案寫在 workspace/output/，同步複製至 output/
        ws_out = sandbox_root / "workspace" / "output"
        if ws_out.exists():
            for f in ws_out.iterdir():
                if f.is_file():
                    shutil.copy2(f, sandbox_root / "output" / f.name)

        parts = [f"Exit Code: {result.returncode}"]
        if result.stdout.strip():
            parts.append(f"STDOUT:\n{result.stdout.strip()}")
        if result.stderr.strip():
            parts.append(f"STDERR:\n{result.stderr.strip()}")
        return "\n".join(parts)
    except Exception as exc:
        return f"Error executing Python script: {exc}"


TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "read_workspace_file",
            "description": "讀取沙盒 input/ 目錄下的教學輸入檔案（如講義、學生短文或問卷 CSV）。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "檔案名稱或相對路徑，例如 'input/lecture_notes.md' 或 'workspace/input/student_essay.txt'",
                    }
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_python_script",
            "description": (
                "在沙盒目錄中執行 Python 3.12 標準庫腳本（僅限標準庫如 re, csv, statistics, math, json；"
                "請勿使用 pandas 或 matplotlib）。用於精確計算字數、Regex 提取 APA 引用、驗算 100 分制 Rubric 配分、"
                "或計算 CSV 問卷的平均值 (Mean) 與標準差 (SD)。請使用 print() 印出結果。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "要執行的完整 Python 3 標準庫程式碼",
                    }
                },
                "required": ["code"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_workspace_file",
            "description": (
                "將生成的檔案寫入沙盒 output/ 目錄（如 pre_class_quiz.html, essay_feedback.md, "
                "grading_sheet.csv, eval_report.html, department_summary.md, student_case_brief.md, instructor_debrief_guide.md）。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "輸出檔案路徑或檔名，例如 'output/pre_class_quiz.html'",
                    },
                    "content": {
                        "type": "string",
                        "description": "完整的檔案文字內容（HTML、Markdown 或 CSV）",
                    },
                },
                "required": ["path", "content"],
            },
        },
    },
]


def call_llm_api(provider_cfg: dict, messages: list, tools: list) -> dict:
    """呼叫 OpenAI 相容之 /chat/completions 端點，支援自動重試與香港本地 IP 403 自動切換。"""
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
        "User-Agent": "gemini-faculty-workshop-vercel/1.0",
    }
    if provider_cfg["provider"] == "openrouter":
        headers["HTTP-Referer"] = "https://gemini-faculty-workshop.vercel.app"
        headers["X-Title"] = "HK Faculty Gemini Agent Workshop"

    for attempt in range(1, 4):
        req = urllib.request.Request(
            provider_cfg["endpoint"], data=data, headers=headers, method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=110) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as http_err:
            err_body = http_err.read().decode("utf-8", errors="replace")
            # 若 OpenRouter 因地區限制回傳 403 且系統有設定 POE_API_KEY，自動無縫切換至 Poe
            if http_err.code == 403 and provider_cfg["provider"] == "openrouter":
                poe_fallback = resolve_provider("poe", "")
                if (
                    poe_fallback["api_key"]
                    and "replace-with-your" not in poe_fallback["api_key"]
                ):
                    provider_cfg.update(poe_fallback)
                    provider_cfg["failover_note"] = (
                        "偵測到 OpenRouter 地區限制 (HTTP 403)，已自動切換至系統 Poe 通道 (Gemini-3.1-Pro)"
                    )
                    return call_llm_api(provider_cfg, messages, tools)
            raise RuntimeError(
                f"API HTTP {http_err.code} 錯誤 ({provider_cfg['provider']}): {err_body}"
            ) from http_err
        except Exception as net_err:
            if attempt < 3:
                continue
            raise RuntimeError(
                f"連線至 {provider_cfg['endpoint']} 失敗: {net_err}"
            ) from net_err


def execute_agent_harness(payload: dict) -> dict:
    """執行完整的沙盒建立、最多 5 回合 Tool Calling Loop 與產出收集。"""
    use_case = str(payload.get("use_case", "1")).strip()
    provider_name = str(payload.get("provider", "openrouter")).strip()
    custom_api_key = str(payload.get("custom_api_key", "")).strip()
    agents_md = str(payload.get("agents_md", "")).strip()
    skill_md = str(payload.get("skill_md", "")).strip()
    input_filename = str(payload.get("input_filename", "input.txt")).strip()
    input_content = str(payload.get("input_content", ""))
    task_prompt = str(payload.get("task_prompt", "")).strip()

    provider_cfg = resolve_provider(provider_name, custom_api_key)
    if (
        not provider_cfg["api_key"]
        or "replace-with-your" in provider_cfg["api_key"]
    ):
        raise ValueError(
            f"尚未配置有效的 {provider_cfg['provider'].upper()} API Key。"
            "請在 Vercel Environment Variables 設定金鑰，或在網頁右上角切換為「個人 Poe / 自訂 API Key」並貼上您的金鑰。"
        )

    session_id = f"workshop-{uuid.uuid4().hex[:12]}"
    sandbox_root = create_isolated_sandbox(session_id, input_filename, input_content)

    serverless_note = (
        "\n\n[Serverless 沙盒環境重要提醒]\n"
        f"1. 當前工作階段隔離沙盒位於 `/tmp/{session_id}/`，輸入檔 `{input_filename}` 已放置於 `input/{input_filename}`（亦相容 `workspace/input/{input_filename}`）。\n"
        "2. `run_python_script` 運行於純 Python 3.12 標準庫環境（請使用 `re`, `csv`, `statistics`, `math`, `json`，切勿 `import pandas` 或 `import matplotlib`）。\n"
        "3. 若執行 Use Case 3（問卷統計分析），請先用 `run_python_script`（透過 `csv` 與 `statistics` 模組）計算精確的 Mean、SD 與相關係數，再透過 `write_workspace_file` 生成內嵌 Chart.js CDN（或 SVG 圖表）的互動視覺化網頁 `output/eval_report.html` 以及文字檢討報告 `output/department_summary.md`。\n"
        "4. 所有產出檔案請一律透過 `write_workspace_file` 寫入 `output/` 目錄下。\n"
    )

    system_prompt = (
        f"{agents_md}\n\n"
        f"====================================================================\n"
        f"當前啟用之學科技能規範 (Use Case {use_case})\n"
        f"====================================================================\n"
        f"{skill_md}"
        f"{serverless_note}"
    )

    if not task_prompt:
        task_prompt = (
            f"請根據上方技能步驟處理輸入檔案 `input/{input_filename}`，"
            "務必先執行必要的工具驗證（`read_workspace_file` / `run_python_script`），"
            "並呼叫 `write_workspace_file` 將所有最終成果檔案寫入 `output/`。"
        )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": task_prompt},
    ]

    logs = []
    final_reply = ""

    try:
        for turn in range(1, MAX_TOOL_TURNS + 1):
            resp_data = call_llm_api(provider_cfg, messages, TOOLS_SCHEMA)
            if provider_cfg.get("failover_note"):
                logs.append(
                    {
                        "turn": turn,
                        "tool": "system_failover",
                        "args": {},
                        "output": provider_cfg["failover_note"],
                        "summary": f"🔄 {provider_cfg['failover_note']}",
                    }
                )
                provider_cfg.pop("failover_note", None)

            choice = (resp_data.get("choices") or [{}])[0]
            assistant_msg = choice.get("message") or {}
            messages.append(assistant_msg)

            tool_calls = assistant_msg.get("tool_calls") or []
            if not tool_calls:
                final_reply = assistant_msg.get("content") or "已完成所有步驟並生成檔案。"
                break

            for tc in tool_calls:
                fn_obj = tc.get("function") or {}
                fn_name = fn_obj.get("name", "")
                raw_args = fn_obj.get("arguments", "{}")
                try:
                    args = (
                        json.loads(raw_args)
                        if isinstance(raw_args, str)
                        else (raw_args or {})
                    )
                except Exception:
                    args = {}

                if fn_name == "read_workspace_file":
                    path_arg = args.get("path", input_filename)
                    tool_out = sandbox_read_file(sandbox_root, path_arg)
                    summary = f"回合 {turn}：讀取教材檔案 `{Path(path_arg).name}`（共 {len(tool_out)} 字元）"
                elif fn_name == "run_python_script":
                    code_arg = args.get("code", "")
                    tool_out = sandbox_run_python(sandbox_root, code_arg)
                    summary = f"回合 {turn}：執行 Python 實證腳本 (`run_python_script`)"
                elif fn_name == "write_workspace_file":
                    path_arg = args.get("path", "output.txt")
                    content_arg = args.get("content", "")
                    tool_out = sandbox_write_file(sandbox_root, path_arg, content_arg)
                    summary = f"回合 {turn}：寫入產出檔案 `{Path(path_arg).name}`（{len(content_arg)} 字元）"
                else:
                    tool_out = f"Error: 未定義的工具 '{fn_name}'"
                    summary = f"回合 {turn}：未知工具 `{fn_name}`"

                logs.append(
                    {
                        "turn": turn,
                        "tool": fn_name,
                        "args": args,
                        "output": tool_out,
                        "summary": summary,
                    }
                )

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.get("id", f"call_{turn}"),
                        "name": fn_name,
                        "content": tool_out,
                    }
                )
        else:
            final_reply = (
                messages[-1].get("content")
                if messages and messages[-1].get("role") == "assistant"
                else "已達到最大工具呼叫回合數上限（5 回合），請查看下方已生成的檔案。"
            )

        # 收集 /tmp/<uuid>/output/ 內所有生成的檔案
        output_files = {}
        out_dir = sandbox_root / "output"
        if out_dir.exists():
            for fpath in sorted(out_dir.iterdir()):
                if fpath.is_file():
                    output_files[fpath.name] = fpath.read_text(
                        encoding="utf-8", errors="replace"
                    )

        return {
            "status": "ok",
            "sandbox_id": f"/tmp/{session_id}",
            "provider_used": provider_cfg["provider"],
            "model_used": provider_cfg["model"],
            "logs": logs,
            "final_reply": final_reply,
            "output_files": output_files,
        }
    finally:
        # 清理 /tmp/<uuid> 暫存目錄，避免 Serverless 容器磁碟空間累積
        try:
            if sandbox_root.exists():
                shutil.rmtree(sandbox_root, ignore_errors=True)
        except Exception:
            pass


class handler(BaseHTTPRequestHandler):
    """Vercel Python Serverless 預設入口類別 (BaseHTTPRequestHandler)。"""

    def _send_json(self, status_code: int, data: dict) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:
        self._send_json(200, {"status": "ok"})

    def do_GET(self) -> None:
        # 若為本地測試伺服器訪問 "/" 或 "/index.html"，自動回傳 public/index.html
        req_path = self.path.split("?", 1)[0]
        if req_path in ("/", "/index.html", "/public/index.html"):
            index_file = PUBLIC_DIR / "index.html"
            if index_file.exists():
                html_bytes = index_file.read_text(encoding="utf-8").encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(html_bytes)))
                self.end_headers()
                self.wfile.write(html_bytes)
                return

        dotenv_cache = load_local_dotenv()
        has_or = bool(
            get_env_value("OPENROUTER_API_KEY", "", dotenv_cache)
            and "replace-with-your"
            not in get_env_value("OPENROUTER_API_KEY", "", dotenv_cache)
        )
        has_poe = bool(
            get_env_value("POE_API_KEY", "", dotenv_cache)
            and "replace-with-your"
            not in get_env_value("POE_API_KEY", "", dotenv_cache)
        )
        self._send_json(
            200,
            {
                "status": "ok",
                "service": "gemini-faculty-workshop Vercel Serverless API",
                "python_version": sys.version.split()[0],
                "max_turns": MAX_TOOL_TURNS,
                "channels_ready": {"openrouter": has_or, "poe": has_poe},
            },
        )

    def do_POST(self) -> None:
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
            payload = json.loads(raw_body)
            result = execute_agent_harness(payload)
            self._send_json(200, result)
        except Exception as exc:
            self._send_json(
                400,
                {
                    "status": "error",
                    "error": str(exc),
                    "logs": [],
                    "final_reply": f"❌ 執行發生錯誤：{exc}",
                    "output_files": {},
                },
            )


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    port = int(os.environ.get("PORT", "3000"))
    server = HTTPServer(("127.0.0.1", port), handler)
    print(f"[OK] Local Vercel Test Server running at http://127.0.0.1:{port}", flush=True)
    print(f"  - Frontend UI : http://127.0.0.1:{port}/", flush=True)
    print(f"  - API Endpoint: http://127.0.0.1:{port}/api/run", flush=True)
    server.serve_forever()

