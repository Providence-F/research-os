#!/usr/bin/env python3
"""Validate view-model.json field names against build_research_html.py rendering contract.

Usage: python validate_view_model.py <project_dir>

Exit code 0 = pass, 1 = fail.
"""
import json
import sys
from pathlib import Path

ERRORS = []
WARNINGS = []

def validate_view_model(vm):
    """Validate view-model.json against rendering contract."""
    # Check hero
    hero = vm.get("hero") or {}
    if hero:
        if not hero.get("verdict"):
            ERRORS.append("hero: missing 'verdict' field")
        if not hero.get("summary"):
            ERRORS.append("hero: missing 'summary' field")

    # Check summary_cards - should have label/value, NOT company names
    cards = vm.get("summary_cards") or []
    for i, card in enumerate(cards):
        if not card.get("label") and not card.get("title"):
            ERRORS.append(f"summary_cards[{i}]: missing 'label' field")
        if not card.get("value") and not card.get("summary") and not card.get("body"):
            ERRORS.append(f"summary_cards[{i}]: missing 'value' field")

    # Check object_cards
    objects = vm.get("object_cards") or vm.get("advisor_cards") or vm.get("objects") or []
    for i, obj in enumerate(objects):
        if not obj.get("name") and not obj.get("title"):
            ERRORS.append(f"object_cards[{i}]: missing 'name' field")

    # Check strategy_tabs - MOST COMMON FAILURE
    tabs = vm.get("strategy_tabs") or vm.get("tabs") or []
    for i, tab in enumerate(tabs):
        title = tab.get("title") or tab.get("label")
        body = tab.get("body") or tab.get("summary") or tab.get("content") or tab.get("items")
        if not title:
            found = list(tab.keys())
            ERRORS.append(f"strategy_tabs[{i}]: missing 'title' field. Found: {found}")
        if not body:
            found = list(tab.keys())
            ERRORS.append(f"strategy_tabs[{i}]: missing 'body' field. Tab will be EMPTY. Found: {found}")

    # Check comparison_matrix
    matrix = vm.get("comparison_matrix") or vm.get("matrix") or {}
    if matrix:
        if not matrix.get("columns"):
            ERRORS.append("comparison_matrix: missing 'columns'")
        if not matrix.get("rows"):
            ERRORS.append("comparison_matrix: missing 'rows'")

    # Check for content overlap between summary_cards and object_cards
    card_titles = set()
    for c in cards:
        card_titles.add(c.get("label", "") or c.get("title", ""))
    obj_names = set()
    for o in objects:
        obj_names.add(o.get("name", "") or o.get("title", ""))
    overlap = card_titles & obj_names
    if len(overlap) > 2:
        WARNINGS.append(f"summary_cards and object_cards overlap: {overlap}. summary_cards=key metrics, object_cards=object details.")

def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_view_model.py <project_dir>")
        sys.exit(1)
    project = Path(sys.argv[1])
    vm_path = project / "07-output" / "view-model.json"
    if not vm_path.exists():
        print(f"[skip] {vm_path} not found")
        sys.exit(0)
    vm = json.loads(vm_path.read_text(encoding="utf-8-sig"))
    validate_view_model(vm)
    if WARNINGS:
        print("\n[warnings]")
        for w in WARNINGS:
            print(f"  WARNING: {w}")
    if ERRORS:
        print("\n[errors]")
        for e in ERRORS:
            print(f"  ERROR: {e}")
        print(f"\nValidation FAILED with {len(ERRORS)} errors")
        sys.exit(1)
    else:
        print("view-model.json validation passed")
        sys.exit(0)

if __name__ == "__main__":
    main()
