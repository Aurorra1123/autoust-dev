# Homework Source Body Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Strengthen homework reconnaissance so candidate source discovery, body reading, subagent responsibilities, reference organization, and real UCUG1808 validation are explicit and test-protected.

**Architecture:** Add policy tests first, then update the runtime documents that drive `do-homework`: `assignment-recon.md`, `do-homework.md`, `runtime-agent-protocol.md`, and `PITFALLS.md`. The design keeps the Main Agent as coordinator/final judge, moves broad source body reading to content scouts, stores per-scout body evidence fragments, and has the Main Agent merge them into `investigation/source_body_audit.json`.

**Tech Stack:** Markdown runtime docs, pytest policy tests, Canvas workbench files under `data/homework/...`.

---

## File Structure

- Create `tests/test_source_body_audit_policy.py`: policy assertions for source candidate ranking, source body audit, scout boundaries, long-document reading, reference organization, and UCUG1808 acceptance.
- Modify `sub-skills/tools/assignment-recon.md`: workbench contract, Stage 3 body audit, content scout templates, reference organization, Stage 4 review fields, quality bar.
- Modify `sub-skills/tasks/do-homework.md`: artifact chain, Main Agent/subagent boundary, scout dispatch rules, pre-alignment gates, UCUG1808 acceptance note.
- Modify `docs/runtime-agent-protocol.md`: source/spec scout split into metadata/content/coverage roles and reference layout.
- Modify `docs/PITFALLS.md`: generic UCUG1808-style pitfall for proposal/research assignments.
- Optionally modify `skill.md`: short source-of-truth chain update if needed after the detailed docs are stable.

## Task 1: Add Failing Policy Tests

**Files:**
- Create: `tests/test_source_body_audit_policy.py`

- [ ] **Step 1: Write tests for the new reconnaissance contract**

Create `tests/test_source_body_audit_policy.py` with:

```python
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_assignment_recon_requires_source_body_audit_and_read_modes():
    text = read("sub-skills/tools/assignment-recon.md")

    assert "source_body_audit.json" in text
    assert "source_body_audit_fragments/" in text
    assert "Main Agent merges" in text
    assert "source_candidates.json" in text
    assert "reading_plan.json" in text
    assert "source_coverage_feedback.json" in text
    assert "metadata_only" in text
    assert "pdf_text_plus_links" in text
    assert "keyword windows" in text
    assert "references/**/*.pdf.links.json" in text
    assert "references/syllabus/" not in text


def test_do_homework_defines_main_agent_and_scout_boundaries():
    text = read("sub-skills/tasks/do-homework.md")

    assert "metadata_scout" in text
    assert "content_scout" in text
    assert "coverage_reviewer" in text
    assert "The Main Agent reviews `source_candidates.json`" in text
    assert "Subagents must not write final `spec.md`" in text
    assert "proposal/research/open-ended" in text
    assert "source_body_audit_fragments/" in text
    assert "Main Agent merges content-scout fragments" in text
    assert "source_coverage_feedback.json`, or a recorded inline" in text
    assert "supporting topic context" in text
    assert "reading budget" in text


def test_do_homework_stage_four_reviews_source_audit_inputs():
    text = read("sub-skills/tasks/do-homework.md")

    stage_four = text.split("4. **Stage 4 review investigation**", 1)[1]
    stage_four = stage_four.split("5. **Stage 5 classify-output**", 1)[0]

    assert "source_candidates.json" in stage_four
    assert "reading_plan.json" in stage_four
    assert "source_body_audit.json" in stage_four
    assert "source_coverage_feedback.json" in stage_four
    assert "content scout receipts" in stage_four


def test_runtime_protocol_splits_source_spec_scout_roles():
    text = read("docs/runtime-agent-protocol.md")

    assert "metadata_scout" in text
    assert "content_scout" in text
    assert "coverage_reviewer" in text
    assert "source_body_audit.json" in text
    assert "source_body_audit_fragments/" in text
    assert "Main Agent remains the final reconnaissance judge" in text
    assert "references/syllabus/" not in text


def test_pitfalls_record_generic_proposal_methods_failure_mode():
    text = read("docs/PITFALLS.md")

    assert "proposal framework is not complete reconnaissance" in text
    assert "methods/topic-selection" in text
    assert "source_body_audit.json" in text


def test_source_body_policy_keeps_ucug1808_only_in_acceptance_context():
    policy_text = "\n".join(
        [
            read("sub-skills/tools/assignment-recon.md"),
            read("sub-skills/tasks/do-homework.md"),
            read("docs/runtime-agent-protocol.md"),
        ]
    )

    assert "UCUG1808" not in policy_text

    design_text = read("docs/superpowers/specs/2026-06-13-homework-source-body-audit-design.md")
    assert "UCUG1808 Acceptance Scenario" in design_text
```

- [ ] **Step 2: Run tests and verify RED**

Run:

```bash
.venv/bin/python -m pytest tests/test_source_body_audit_policy.py -q
```

Expected: failures because the runtime docs do not yet mention the new audit contract and scout roles.

## Task 2: Update Assignment Recon Contract

**Files:**
- Modify: `sub-skills/tools/assignment-recon.md`
- Test: `tests/test_source_body_audit_policy.py`

- [ ] **Step 1: Add source body audit to the workbench contract**

Update the workbench structure so `investigation/` includes:

```text
│   ├── source_candidates.json
│   ├── reading_plan.json
│   ├── source_body_audit_fragments/
│   ├── source_body_audit.json
│   ├── source_coverage_feedback.json
```

- [ ] **Step 2: Add Stage 3 source body audit rules**

Add a Stage 3 subsection requiring candidate ranking, bounded `reading_plan.json`, per-content-scout `source_body_audit_fragments/`, merged `source_body_audit.json`, `read_mode`, evidence windows, and these classifications:

```text
required | high_signal | supporting | low_signal | forbidden | blocked
precise_match | supporting_context | weak_related | excluded | forbidden | blocked
```

Include the rule that `metadata_only` cannot be used as `precise_match`.

- [ ] **Step 3: Add long-document reading and reference organization rules**

Document that long PDFs/PPTX files use extracted text, keyword windows, page/slide evidence, and escalation to full read only when needed. Add the organized `references/` layout and preserve companion artifacts beside their source. Mention `references/**/*.pdf.links.json` while allowing old flat `references/*.pdf.links.json`.

- [ ] **Step 4: Extend Stage 4 review schema**

Add review fields:

```json
{
  "source_body_audit_checked": true,
  "source_candidates_complete": true,
  "unread_source_candidates": [],
  "open_ended_coverage": {
    "assignment_spec_body_read": true,
    "methods_or_topic_guidance_body_read": true,
    "supporting_topic_context_checked": true
  }
}
```

- [ ] **Step 5: Run focused tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_source_body_audit_policy.py::test_assignment_recon_requires_source_body_audit_and_read_modes -q
```

Expected: PASS.

## Task 3: Update Do-Homework Coordinator Contract

**Files:**
- Modify: `sub-skills/tasks/do-homework.md`
- Test: `tests/test_source_body_audit_policy.py`

- [ ] **Step 1: Add artifacts to required chain**

Add:

```text
-> investigation/source_candidates.json
-> investigation/reading_plan.json
-> investigation/source_body_audit.json
-> investigation/source_coverage_feedback.json
```

- [ ] **Step 2: Define Main Agent and child scout boundaries**

Document:

```text
The Main Agent reviews `source_candidates.json`, approves `reading_plan.json`,
dispatches content scouts, reads content receipts, and writes final `spec.md`.
Subagents must not write final `spec.md`, `review_a.json`, `pipeline_design.md`,
or user alignment decisions.
```

- [ ] **Step 3: Define dispatch decision rules**

Document when to use:

```text
metadata_scout: non-trivial source-heavy homework; full Canvas/source indexing.
content_scout: required/high_signal body reading or selected supporting context.
coverage_reviewer: proposal/research/open-ended tasks and other non-trivial multi-source runs.
```

- [ ] **Step 4: Add open-ended gate**

Require proposal/research/open-ended runs to have assignment/spec body evidence plus methods/topic-selection coverage before `review_a.verdict: proceed`.

- [ ] **Step 5: Run focused tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_source_body_audit_policy.py::test_do_homework_defines_main_agent_and_scout_boundaries -q
```

Expected: PASS.

## Task 4: Update Runtime Protocol And Pitfalls

**Files:**
- Modify: `docs/runtime-agent-protocol.md`
- Modify: `docs/PITFALLS.md`
- Test: `tests/test_source_body_audit_policy.py`

- [ ] **Step 1: Update runtime protocol source/spec scout model**

Replace the single broad source/spec scout description with a split model:

```text
metadata_scout
content_scout
coverage_reviewer
```

Include the line:

```text
Main Agent remains the final reconnaissance judge.
```

- [ ] **Step 2: Update runtime workbench contract**

Add `source_candidates.json`, `reading_plan.json`, `source_body_audit_fragments/`, `source_body_audit.json`, and organized `references/` guidance. Keep Canvas-native bodies canonical under `canvas/*.json`; any readable syllabus/page export is an optional derived convenience copy, not an evidence gate.

- [ ] **Step 3: Add a generic pitfall**

Add a pitfall section titled:

```text
proposal framework is not complete reconnaissance
```

Explain that proposal/research assignments require methods/topic-selection and course-topic coverage when available.

- [ ] **Step 4: Run focused tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_source_body_audit_policy.py::test_runtime_protocol_splits_source_spec_scout_roles tests/test_source_body_audit_policy.py::test_pitfalls_record_generic_proposal_methods_failure_mode tests/test_source_body_audit_policy.py::test_source_body_policy_keeps_ucug1808_only_in_acceptance_context -q
```

Expected: PASS.

## Task 5: Full Policy Verification

**Files:**
- Test: `tests/test_source_body_audit_policy.py`
- Test: `tests/test_pdf_link_annotation_policy.py`
- Test: `tests/test_spec_hard_requirement_policy.py`

- [ ] **Step 1: Run related policy tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_source_body_audit_policy.py tests/test_pdf_link_annotation_policy.py tests/test_spec_hard_requirement_policy.py -q
```

Expected: PASS.

- [ ] **Step 2: Inspect git diff**

Run:

```bash
git diff -- docs/superpowers/specs/2026-06-13-homework-source-body-audit-design.md docs/superpowers/plans/2026-06-13-homework-source-body-audit.md tests/test_source_body_audit_policy.py sub-skills/tools/assignment-recon.md sub-skills/tasks/do-homework.md docs/runtime-agent-protocol.md docs/PITFALLS.md
```

Expected: only source-body audit design, tests, and runtime policy docs changed.

## Task 6: UCUG1808 Reconnaissance Acceptance Run

**Files:**
- Runtime target: `data/homework/UCUG1808/23014-project-proposal-files`

- [ ] **Step 1: Archive or remove the current workbench**

Before deletion, verify no user-visible draft is needed for this test. Then archive/remove the workbench so the run simulates a first attempt.

- [ ] **Step 2: Dispatch a child agent for a reconnaissance-only do-homework run**

Prompt the child to run `do-homework` for UCUG1808 Project Proposal through reconnaissance only. It must stop before draft production and report child scout dispatches, receipts, and coverage verdict.

- [ ] **Step 3: Verify acceptance criteria**

Check:

```text
metadata_scout indexed all modules and module items
content_scout read direct proposal/final-project files
content_scout read Week 8 research-methods source
coverage_reviewer blocked proceed if methods/topic-selection coverage was absent
source_body_audit.json exists and contains read modes/evidence windows
source_body_audit_fragments/ exists when content scouts ran
prior submitted artifacts stayed forbidden and unread
reading cost stayed bounded
```

- [ ] **Step 4: Iterate if acceptance fails**

If the run misses a high-signal source, over-reads unrelated materials, or relies on Main Agent manual rescue, update the docs/tests and rerun focused verification before accepting the workflow.
