#!/usr/bin/env python3
"""Research OS v0.9 WebCapture 层.

把"网页抓取"从靠人手动操作，升级成 Research OS 工作流的一等公民。

有机融入 agent-browser skill 的核心能力：
  - 浏览器自动化（导航/截图/提取）
  - JS 渲染页面处理
  - 登录态会话保持
  - SPA（单页应用）抓取

设计原则：
  1. 如果 agent-browser CLI 在 PATH 里，优先用它（增强模式）
  2. 否则 fallback 到 requests + BeautifulSoup（基础模式，无 JS 渲染）
  3. 抓取结果自动写入 02-sources/web_capture/ 并归入证据矩阵

WebCapture 产出的每条证据自动带：
  - capture_method: "agent_browser" | "requests" | "manual"
  - capture_timestamp: ISO 8601
  - capture_screenshot: 截图路径（agent-browser 模式才有）
  - raw_html_path: 原始 HTML 保存路径
"""
from __future__ import annotations
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


def is_agent_browser_available() -> bool:
    """检查 agent-browser CLI 是否在 PATH"""
    return shutil.which("agent-browser") is not None


def capture_with_agent_browser(url: str, output_dir: Path,
                                session_name: Optional[str] = None) -> dict:
    """用 agent-browser 抓取网页（增强模式，含 JS 渲染+截图）

    有机融入 agent-browser 的核心能力：
      - open + wait --load networkidle（等页面加载完）
      - snapshot -i（提取可交互元素）
      - get text body（提取正文）
      - screenshot（截图存证）
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = url.split("/")[-1][:30] or "capture"
    safe_name = "".join(c for c in base_name if c.isalnum() or c in "-_") or "capture"

    session_flag = ["--session-name", session_name] if session_name else []
    ab_cmd = ["agent-browser"] + session_flag

    try:
        # Step 1: open + wait
        subprocess.run(ab_cmd + ["open", url], check=True, capture_output=True, timeout=30)
        subprocess.run(ab_cmd + ["wait", "--load", "networkidle"],
                       check=True, capture_output=True, timeout=30)

        # Step 2: 提取正文
        text_result = subprocess.run(ab_cmd + ["get", "text", "body"],
                                      capture_output=True, text=True, timeout=30)
        text_content = text_result.stdout

        # Step 3: 截图存证
        screenshot_path = output_dir / f"{safe_name}_{timestamp}.png"
        subprocess.run(ab_cmd + ["screenshot", "--full", str(screenshot_path)],
                       check=True, capture_output=True, timeout=30)

        # Step 4: 保存原始文本
        text_path = output_dir / f"{safe_name}_{timestamp}.txt"
        text_path.write_text(text_content, encoding="utf-8")

        return {
            "capture_method": "agent_browser",
            "capture_timestamp": datetime.now().isoformat(),
            "url": url,
            "raw_text_path": str(text_path),
            "screenshot_path": str(screenshot_path),
            "content_length": len(text_content),
            "success": True,
        }
    except subprocess.CalledProcessError as e:
        return {
            "capture_method": "agent_browser",
            "url": url,
            "success": False,
            "error": f"agent-browser failed: {e.stderr[:200] if e.stderr else str(e)}",
        }
    except subprocess.TimeoutExpired:
        return {
            "capture_method": "agent_browser",
            "url": url,
            "success": False,
            "error": "agent-browser timeout (30s)",
        }


def capture_with_requests(url: str, output_dir: Path) -> dict:
    """fallback: 用 requests + BeautifulSoup 抓取（基础模式，无 JS 渲染）"""
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        return {
            "capture_method": "requests",
            "url": url,
            "success": False,
            "error": "requests/bs4 not installed",
        }

    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = url.split("/")[-1][:30] or "capture"
    safe_name = "".join(c for c in base_name if c.isalnum() or c in "-_") or "capture"

    try:
        resp = requests.get(url, timeout=20, headers={
            "User-Agent": "Research-OS/0.9 (web-capture)"
        })
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        # 去掉 script/style
        for tag in soup(["script", "style"]):
            tag.decompose()
        text_content = soup.get_text(separator="\n", strip=True)

        text_path = output_dir / f"{safe_name}_{timestamp}.txt"
        text_path.write_text(text_content, encoding="utf-8")

        return {
            "capture_method": "requests",
            "capture_timestamp": datetime.now().isoformat(),
            "url": url,
            "raw_text_path": str(text_path),
            "screenshot_path": None,  # requests 模式无截图
            "content_length": len(text_content),
            "success": True,
        }
    except Exception as e:
        return {
            "capture_method": "requests",
            "url": url,
            "success": False,
            "error": str(e)[:200],
        }


def capture(url: str, project_dir: Path | str,
            session_name: Optional[str] = None,
            force_method: Optional[str] = None) -> dict:
    """统一入口：根据 agent-browser 是否在自动选模式。

    force_method: "agent_browser" | "requests" | "manual" 强制指定
    """
    project = Path(project_dir)
    output_dir = project / "02-sources" / "web_capture"

    if force_method == "manual":
        return {
            "capture_method": "manual",
            "url": url,
            "success": True,
            "note": "人工抓取，请手动填写证据",
        }

    if force_method == "agent_browser" or (force_method is None and is_agent_browser_available()):
        result = capture_with_agent_browser(url, output_dir, session_name)
        if result["success"]:
            return result
        # agent-browser 失败，fallback
        print(f"[warn] agent-browser failed, falling back to requests", file=sys.stderr)

    return capture_with_requests(url, output_dir)


def capture_to_evidence(url: str, project_dir: Path | str,
                        evidence_id: str, claim: str,
                        grade: str = "B") -> dict:
    """抓取网页 + 自动归入证据矩阵。

    有机融入：
      - 抓取（agent-browser / requests）
      - 归档（写入 02-sources/web_capture/）
      - 入证据矩阵（evidence_matrix.md 自动追加一行）
      - 证据等级标记
    """
    project = Path(project_dir)
    capture_result = capture(url, project)

    if not capture_result["success"]:
        return capture_result

    # 追加到 evidence_matrix.md
    matrix_path = project / "02-sources" / "evidence_matrix.md"
    matrix_path.parent.mkdir(parents=True, exist_ok=True)

    row = f"| {evidence_id} | {claim} | {url} | {grade} | {capture_result.get('capture_timestamp', '')[:10]} | {capture_result['capture_method']} |\n"
    with open(matrix_path, "a", encoding="utf-8") as f:
        f.write(row)

    return {
        **capture_result,
        "evidence_id": evidence_id,
        "grade": grade,
        "claim": claim,
    }


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("usage: web_capture.py <url> <project_dir> [--evidence-id E001 --claim '...']")
        sys.exit(1)
    url = sys.argv[1]
    project = Path(sys.argv[2])

    evidence_id = None
    claim = ""
    for i, arg in enumerate(sys.argv):
        if arg == "--evidence-id" and i + 1 < len(sys.argv):
            evidence_id = sys.argv[i + 1]
        elif arg == "--claim" and i + 1 < len(sys.argv):
            claim = sys.argv[i + 1]

    if evidence_id:
        result = capture_to_evidence(url, project, evidence_id, claim)
    else:
        result = capture(url, project)

    print(json.dumps(result, ensure_ascii=False, indent=2))
