#!/usr/bin/env python3
"""Global profile store for Research OS.

Persists cross-project memory in ~/.research-os/:
- user_profile.json: judgment patterns, domain preferences, unresolved seeds,
  insight memory (all in one file for atomic updates)
- project_index.json: lightweight project history index (last 10)
- insight_memory.json: cross-project reusable insights (last 50)

This is the soil for the intent layer. intent_discovery reads it to surface
unresolved seeds and tailor questions; intent_tracker updates it mid-research;
profile_updater writes back resolved intents and new seeds after build.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import config


def _profile_dir() -> Path:
    d = config.PROFILE_DIR
    d.mkdir(parents=True, exist_ok=True)
    return d


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return default


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


# ---------------- user_profile.json ----------------


def read_user_profile() -> dict[str, Any]:
    """Return user profile, initializing if missing. v0.2 adds identity_ref
    and intent_evolution fields. Backward compatible with v0.1."""
    path = _profile_dir() / "user_profile.json"
    profile = _read_json(path, {})
    if not profile:
        profile = {
            "schema_version": "research-os-profile-v0.2",
            "created_at": date.today().isoformat(),
            "last_updated": date.today().isoformat(),
            "identity_ref": "~/.research-os/identity.json",
            "judgment_patterns": [],
            "domain_preferences": [],
            "unresolved_seeds": [],
            "insight_memory": [],
            "intent_evolution": [],
        }
    # Upgrade v0.1 -> v0.2 in place if needed
    if profile.get("schema_version") == "research-os-profile-v0.1":
        profile["schema_version"] = "research-os-profile-v0.2"
        profile.setdefault("identity_ref", "~/.research-os/identity.json")
        profile.setdefault("intent_evolution", [])
    profile.setdefault("schema_version", "research-os-profile-v0.2")
    profile.setdefault("identity_ref", "~/.research-os/identity.json")
    profile.setdefault("judgment_patterns", [])
    profile.setdefault("domain_preferences", [])
    profile.setdefault("unresolved_seeds", [])
    profile.setdefault("insight_memory", [])
    profile.setdefault("intent_evolution", [])
    return profile


def write_user_profile(profile: dict[str, Any]) -> None:
    profile["last_updated"] = date.today().isoformat()
    path = _profile_dir() / "user_profile.json"
    _write_json(path, profile)


# ---------------- project_index.json ----------------


def read_project_index() -> list[dict[str, Any]]:
    """Return last 10 projects, newest first."""
    path = _profile_dir() / "project_index.json"
    data = _read_json(path, [])
    return data if isinstance(data, list) else []


def append_project_to_index(entry: dict[str, Any]) -> None:
    """Insert or update entry by project_id. Keep last 10, newest first."""
    path = _profile_dir() / "project_index.json"
    idx = read_project_index()
    idx = [e for e in idx if e.get("project_id") != entry.get("project_id")]
    idx.insert(0, entry)
    idx = idx[:10]
    _write_json(path, idx)


# ---------------- insight_memory.json ----------------
#
# Separate from user_profile.insight_memory: this file holds AI-extracted
# cross-project insights (used by intent_discovery with anti-recursion scope
# limits). user_profile.insight_memory holds user-facing insights (judgment
# patterns etc). The split prevents AI from recursively reflecting on its
# own previous reflections.


def read_insight_memory() -> list[dict[str, Any]]:
    path = _profile_dir() / "insight_memory.json"
    data = _read_json(path, [])
    return data if isinstance(data, list) else []


def append_insight(insight: dict[str, Any]) -> None:
    path = _profile_dir() / "insight_memory.json"
    items = read_insight_memory()
    items.insert(0, insight)
    items = items[:50]
    _write_json(path, items)


# ---------------- convenience mutators ----------------


def add_unresolved_seed(seed_text: str, project_id: str) -> None:
    """Add a new unresolved seed, or touch an existing one."""
    profile = read_user_profile()
    seeds = profile.setdefault("unresolved_seeds", [])
    for seed in seeds:
        if seed.get("seed") == seed_text:
            touched = seed.setdefault("touched_again", [])
            if project_id not in touched:
                touched.append(project_id)
            seed["status"] = "open"
            write_user_profile(profile)
            return
    seeds.append({
        "seed": seed_text,
        "origin_project_id": project_id,
        "touched_again": [],
        "status": "open",
        "first_seen": date.today().isoformat(),
    })
    write_user_profile(profile)


def resolve_seed(seed_text: str) -> None:
    """Mark an unresolved seed as resolved."""
    profile = read_user_profile()
    for seed in profile.get("unresolved_seeds", []):
        if seed.get("seed") == seed_text:
            seed["status"] = "resolved"
    write_user_profile(profile)


def add_judgment_pattern(pattern: str, project_id: str) -> None:
    """Add a new judgment pattern or extend evidence of an existing one."""
    profile = read_user_profile()
    patterns = profile.setdefault("judgment_patterns", [])
    for p in patterns:
        if p.get("pattern") == pattern:
            ev = p.setdefault("evidence_project_ids", [])
            if project_id not in ev:
                ev.append(project_id)
            write_user_profile(profile)
            return
    patterns.append({
        "pattern": pattern,
        "evidence_project_ids": [project_id],
        "first_seen": date.today().isoformat(),
    })
    write_user_profile(profile)


def add_domain_preference(domain: str, depth: str, project_id: str) -> None:
    profile = read_user_profile()
    prefs = profile.setdefault("domain_preferences", [])
    for p in prefs:
        if p.get("domain") == domain:
            p["frequency"] = int(p.get("frequency", 0)) + 1
            p.setdefault("evidence_project_ids", []).append(project_id)
            write_user_profile(profile)
            return
    prefs.append({
        "domain": domain,
        "depth_tendency": depth,
        "frequency": 1,
        "evidence_project_ids": [project_id],
        "first_seen": date.today().isoformat(),
    })
    write_user_profile(profile)


# ---------------- intent_evolution (v0.2) ----------------
#
# Records the gap between stated_intent (what user said they wanted at start)
# and resolved_intent (what they actually needed by end). When the next
# project is created, intent_discovery reads this to propose L1 draft mode if
# the last gap was large.


def add_intent_evolution(
    project_id: str,
    stated_intent: str,
    resolved_intent: str,
    gap: str,
    implication_for_next: str,
) -> None:
    """Record intent evolution for a project. Appends to intent_evolution list."""
    profile = read_user_profile()
    evo = profile.setdefault("intent_evolution", [])
    evo.append({
        "project_id": project_id,
        "stated_intent": stated_intent,
        "resolved_intent": resolved_intent,
        "gap": gap,
        "implication_for_next": implication_for_next,
        "recorded_at": date.today().isoformat(),
    })
    evo = evo[-10:]  # keep last 10
    write_user_profile(profile)


def read_intent_evolution() -> list[dict[str, Any]]:
    """Return intent_evolution list (last 10, newest last)."""
    return read_user_profile().get("intent_evolution", [])


# ---------------- identity.json (v0.2) ----------------
#
# User identity profile (employment/products/tracks/goals). Extracted from
# CLAUDE.md memory + Obsidian vault by identity_extractor. Stored separately
# from user_profile.json because identity is user-edited while judgment_patterns
# are AI-extracted.


def read_identity() -> dict[str, Any]:
    """Return accepted identity.json. Empty dict if not present."""
    path = _profile_dir() / "identity.json"
    return _read_json(path, {})


def write_identity(identity: dict[str, Any]) -> None:
    """Write identity.json (called by accept-identity after user review)."""
    path = _profile_dir() / "identity.json"
    _write_json(path, identity)


def read_identity_draft() -> dict[str, Any]:
    """Return identity.draft.json (post-extraction, pre-acceptance)."""
    path = _profile_dir() / "identity.draft.json"
    return _read_json(path, {})
