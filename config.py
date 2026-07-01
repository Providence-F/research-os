"""Research OS configuration.

All paths and external resources are read from environment variables with
defaults pointing inside the Research OS home directory. Override them when
integrating with an Obsidian vault or other external layout.
"""
from __future__ import annotations

import os
from pathlib import Path

# Research OS home: the directory containing this package by default.
# Override with RESEARCH_OS_HOME to point at a different install location.
HOME = Path(os.environ.get("RESEARCH_OS_HOME", Path(__file__).resolve().parent)).resolve()

# Templates: shipped with the repo by default (./templates).
# Override with RESEARCH_OS_TEMPLATES to point at an Obsidian vault or custom set.
TEMPLATES = Path(os.environ.get("RESEARCH_OS_TEMPLATES", HOME / "templates")).resolve()

# Default project output directory. Override with RESEARCH_OS_PROJECTS_DIR.
PROJECTS_DIR = Path(os.environ.get("RESEARCH_OS_PROJECTS_DIR", HOME / "projects")).resolve()

# MiMo search integration (optional). Key file path and temp payload path.
MIMO_KEY_PATH = Path(os.environ.get("MIMO_KEY_PATH", HOME / ".mimo_search_key"))
MIMO_PAYLOAD_PATH = Path(os.environ.get("MIMO_PAYLOAD_PATH", HOME / "_mimo_payload.json"))


def ensure_runtime_dirs() -> None:
    """Create the runtime directories if missing. Safe to call repeatedly."""
    HOME.mkdir(parents=True, exist_ok=True)
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)


def as_dict() -> dict:
    """Return current config as a dict for diagnostic output."""
    return {
        "RESEARCH_OS_HOME": str(HOME),
        "RESEARCH_OS_TEMPLATES": str(TEMPLATES),
        "RESEARCH_OS_PROJECTS_DIR": str(PROJECTS_DIR),
        "MIMO_KEY_PATH": str(MIMO_KEY_PATH),
        "MIMO_PAYLOAD_PATH": str(MIMO_PAYLOAD_PATH),
        "templates_exist": TEMPLATES.exists(),
        "mimo_key_exists": MIMO_KEY_PATH.exists(),
    }
