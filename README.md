# Research OS

Depth research workflow toolkit. Goes from a research question to an evidence-graded, reader-first HTML report.

## What it does

Research OS turns a research question into a structured, evidence-graded, reader-first HTML report. It is built around four principles:

1. **Evidence grading first** — every claim must trace back to a source with explicit grade (A/B/C/D) and independence marker.
2. **Reader-first delivery** — the final HTML report serves readers, not the researcher. Audit trails, evidence matrices, and trace manifests are folded into appendices.
3. **Hypothesis-driven** — every project starts with explicit hypotheses that get revised, downgraded, or rejected as evidence comes in.
4. **Traceable conclusions** — strong claims in the final report must link to hypothesis IDs and evidence IDs in a trace manifest.

## Install

```bash
git clone https://github.com/your-name/research-os.git
cd research-os
pip install -e .
```

Optional: configure MiMo search integration by creating a `.mimo_search_key` file with your MiMo API key, or set `MIMO_KEY_PATH` env var.

## Quick start

```bash
# Create a new research project
ros new --name "Mizzen Insight 产品深度拆解" --type product --depth R2 --html

# Generate the execution plan (questions + hypotheses seed)
ros plan "projects/Mizzen Insight 产品深度拆解"

# Fill task-card.md, candidate_pool.json, evidence_matrix.md, etc.
# Then check status to see the next required action:
ros status "projects/Mizzen Insight 产品深度拆解"

# Run the next safe mechanical step (planner / html builder / manual instructions)
ros run "projects/Mizzen Insight 产品深度拆解"

# Validate against quality gates
ros validate "projects/Mizzen Insight 产品深度拆解"

# Build the reader-first HTML from final-report.md
ros build --project "projects/Mizzen Insight 产品深度拆解"
```

## Depth levels

| Level | Description |
|-------|-------------|
| R0    | Lightweight, single-question, narrative report |
| R1    | Standard research with evidence matrix |
| R2    | Full workflow with candidate pool, hypothesis ledger, trace manifest, and HTML |
| R3    | Multi-stage deep research with all R2 features plus extended analysis |

## Research types

`company-jd`, `product`, `user-research`, `industry`, `competitor`, `topic`, `portfolio`, `mixed`

Each type routes to a research mode (`evidence_intelligence`, `thinking_decision`, `opportunity_map`, `product_teardown`, `user_voice`, `career_strategy`) that determines the questions, hypotheses, and HTML view type.

## Configuration

All paths are configurable via environment variables (see `.env.example`):

- `RESEARCH_OS_HOME` — install root (defaults to repo directory)
- `RESEARCH_OS_TEMPLATES` — template library location (defaults to `<home>/templates`)
- `RESEARCH_OS_PROJECTS_DIR` — where new projects are scaffolded (defaults to `<home>/projects`)
- `MIMO_KEY_PATH` — MiMo API key file path
- `MIMO_PAYLOAD_PATH` — temp payload file for MiMo API calls

## Project structure

Each research project gets scaffolded with:

```
project-name/
├── 00-task/           # task-card.md
├── 01-plan/           # research-plan.md, research-execution-plan.md
├── 02-sources/        # candidate_pool.json, platform-audit.md, user-voice.md, jd-breakdown.md
├── 03-evidence/       # evidence_matrix.md, hypothesis_ledger.json
├── 04-captures/       # raw captures
├── 05-analysis/       # analysis notes
├── 06-review/         # red_team.md
├── 07-output/         # final-report.md, view-model.json, trace-manifest.json
├── 08-html/           # index.html (generated)
└── 09-publish/        # published artifacts
```

## Quality gates

The validator checks for:

- Final report has all required reader sections (verdict, key findings, mechanism, users, differentiation, risks, recommendations)
- Audit material (evidence standards, source appendix) is in the latter half, not burying reader content
- Evidence matrix has `来源独立性` and MiMo downgrade rule
- Research plan includes SSR/login-wall handling
- Red team requires final-report writeback and at least one downgraded conclusion
- R2/R3: candidate pool, hypothesis ledger, trace manifest all present
- Strong claims in trace manifest link to existing hypothesis IDs and evidence IDs
- HTML is reader-first (not a paste of process files), has visual modules for non-narrative views

## License

Apache-2.0
