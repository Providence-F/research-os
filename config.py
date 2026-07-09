"""Research OS configuration.


# 系统版本号——单一真相源，所有文件应与此一致
SYSTEM_VERSION = "v1.0"
All paths and external resources are read from environment variables with
defaults pointing inside the Research OS home directory. Override them when
integrating with an Obsidian vault or other external layout.

A .env file in the Research OS home directory is loaded automatically - no
need for python-dotenv. The .env file is gitignored.
"""
from __future__ import annotations

import os
from pathlib import Path

# Research OS home: the directory containing this package by default.
# Override with RESEARCH_OS_HOME to point at a different install location.
HOME = Path(os.environ.get("RESEARCH_OS_HOME", Path(__file__).resolve().parent)).resolve()


def _load_dotenv() -> None:
    """Load .env from RESEARCH_OS_HOME. Does not override existing env vars.

    Minimal implementation - no python-dotenv dependency. Handles KEY=VALUE,
    quotes, comments, and blank lines.
    """
    env_path = HOME / ".env"
    if not env_path.exists():
        return
    try:
        text = env_path.read_text(encoding="utf-8-sig")
    except OSError:
        return
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


_load_dotenv()

# Templates: shipped with the repo by default (./templates).
# Override with RESEARCH_OS_TEMPLATES to point at an Obsidian vault or custom set.
TEMPLATES = Path(os.environ.get("RESEARCH_OS_TEMPLATES", HOME / "templates")).resolve()

# Default project output directory. Override with RESEARCH_OS_PROJECTS_DIR.
PROJECTS_DIR = Path(os.environ.get("RESEARCH_OS_PROJECTS_DIR", HOME / "projects")).resolve()

# MiMo search integration (optional). Key file path and temp payload path.
MIMO_KEY_PATH = Path(os.environ.get("MIMO_KEY_PATH", HOME / ".mimo_search_key"))
MIMO_PAYLOAD_PATH = Path(os.environ.get("MIMO_PAYLOAD_PATH", HOME / "_mimo_payload.json"))

# DeepSeek API key for the intent layer (discovery / tracker / updater).
# Read from env after _load_dotenv() so .env values are picked up.
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")

# Global profile directory: cross-project memory for the intent layer.
# Stores user_profile.json / project_index.json / insight_memory.json.
# Defaults to ~/.research-os/ - outside the repo so it survives clones and
# isn't committed even by accident.
PROFILE_DIR = Path(
    os.environ.get("RESEARCH_OS_PROFILE_DIR", Path.home() / ".research-os")
).resolve()


def ensure_runtime_dirs() -> None:
    """Create the runtime directories if missing. Safe to call repeatedly."""
    HOME.mkdir(parents=True, exist_ok=True)
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)


def as_dict() -> dict:
    """Return current config as a dict for diagnostic output."""
    return {
        "RESEARCH_OS_HOME": str(HOME),
        "RESEARCH_OS_TEMPLATES": str(TEMPLATES),
        "RESEARCH_OS_PROJECTS_DIR": str(PROJECTS_DIR),
        "RESEARCH_OS_PROFILE_DIR": str(PROFILE_DIR),
        "MIMO_KEY_PATH": str(MIMO_KEY_PATH),
        "MIMO_PAYLOAD_PATH": str(MIMO_PAYLOAD_PATH),
        "DEEPSEEK_API_KEY_set": bool(DEEPSEEK_API_KEY),
        "templates_exist": TEMPLATES.exists(),
        "mimo_key_exists": MIMO_KEY_PATH.exists(),
        "profile_dir_exists": PROFILE_DIR.exists(),
    }