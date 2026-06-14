# Homework A Compact Findings Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Shrink `do-homework [A]` Main Agent context by replacing full intermediate reads with compact source findings and a parent self-check.

**Architecture:** Update policy tests and runtime docs so the ordered scout chain is `metadata_scout -> reading_plan.compact.json -> content_scout -> source_findings.compact.md -> parent self-check`. The Main Agent fully reads only syllabus and direct-spec strong matches, then reads compact findings and writes `review_a.json` plus `recon_summary.md`.

**Tech Stack:** Markdown runtime docs, pytest policy tests, existing AutoStudy homework workbench artifact conventions.

---

## File Structure

- Modify `tests/test_source_body_audit_policy.py`: add policy tests for the compact findings contract and absence of a third source-review child.
- Modify `sub-skills/tasks/do-homework.md`: define parent read allowlist, compact artifacts, appendix artifacts, post-A3 read rules, and parent self-check.
- Modify `sub-skills/tools/assignment-recon.md`: update source/body/self-check sections so compact plan and source findings are first-class.
- Modify `docs/runtime-agent-protocol.md`: mirror the source-flow contract for runtime agents.
- Modify `docs/superpowers/specs/2026-06-14-homework-a-gate-report-design.md`: design source for this plan.

## Task 1: Add Policy Tests

**Files:**
- Modify: `tests/test_source_body_audit_policy.py`

- [ ] **Step 1: Add tests for parent read boundary**

Assert `do-homework.md` contains:

```python
assert "Hybrid Gate Report" in text
assert "direct-spec strong match" in text
assert "source_findings.compact.md" in text
assert "The Main Agent must not normally read full appendix artifacts" in text
assert ("coverage" + "_reviewer") not in text
```

- [ ] **Step 2: Add tests for compact and appendix artifacts**

Assert all three runtime docs name:

```python
assert "reading_plan.compact.json" in combined
assert "source_findings.compact.md" in combined
assert "investigation/_appendix/source_index.json" in combined
assert "investigation/_appendix/body_evidence_fragments/" in combined
for term in ["coverage" + "_reviewer", "coverage" + "_review.full.json", "recon" + "_gate.json"]:
    assert term not in combined
```

- [ ] **Step 3: Run tests and verify they fail before doc updates**

Run:

```bash
.venv/bin/python -m pytest tests/test_source_body_audit_policy.py -q
```

Expected: the new tests fail before the docs contain the compact findings contract.

## Task 2: Update `do-homework [A]` Contract

**Files:**
- Modify: `sub-skills/tasks/do-homework.md`
- Test: `tests/test_source_body_audit_policy.py`

- [ ] **Step 1: Add compact and appendix artifacts to the chain**

Update the required artifact chain near the top of `do-homework.md` to include:

```text
-> investigation/_appendix/source_index.json
-> investigation/reading_plan.compact.json
-> investigation/_appendix/body_evidence_fragments/
-> investigation/source_findings.compact.md
```

- [ ] **Step 2: Replace broad Main Agent reading rules**

Replace broad source reread rules with:

```text
The Main Agent fully reads only the syllabus body and direct-spec strong
matches. It must not normally read full appendix artifacts such as the source
index, body fragments, or scout receipts. It reads
`reading_plan.compact.json`, `source_findings.compact.md`,
`recon_summary.md`, terminal artifacts, and the exact windows listed in
`parent_source_read_requests`.
```

- [ ] **Step 3: Define direct-spec strong match**

Add:

```text
A direct-spec strong match satisfies at least two of: task terms in title/name,
assignment-linked or required source placement, and opening-body evidence of
deliverable/format/deadline/sections/submission/grading/prompt.
```

- [ ] **Step 4: Replace the post-A3 read list**

Change the "After `[A3]`, immediately read" list so the Main Agent reads:

```text
investigation/explore_manifest.json
investigation/explore_context.md
investigation/reading_plan.compact.json
investigation/source_findings.compact.md
investigation/recon_summary.md
canvas/syllabus.json
direct-spec strong match source bodies
exact windows named in parent_source_read_requests
spec.md
investigation/rubric.md
investigation/review_a.json
pipeline_design.md
problem.md
```

Move full `source_candidates.json`, fragments, body audit, raw receipts, and full
source index under "appendix evidence, not normal Main Agent reads."

## Task 3: Update Assignment Recon and Runtime Protocol

**Files:**
- Modify: `sub-skills/tools/assignment-recon.md`
- Modify: `docs/runtime-agent-protocol.md`
- Test: `tests/test_source_body_audit_policy.py`

- [ ] **Step 1: Update assignment recon source flow**

Document this flow:

```text
metadata_scout -> _appendix/source_index.json -> reading_plan.compact.json
content_scout -> _appendix/body_evidence_fragments/ -> source_findings.compact.md
Main Agent -> review_a.json -> recon_summary.md
```

- [ ] **Step 2: Update self-check read rules**

Change Main Agent wording so it reads compact plan, source findings, terminal
artifacts, and explicit parent read requests. Remove the third source-review
child and separate gate wording.

- [ ] **Step 3: Mirror the same contract in runtime protocol**

Add the compact/interface wording to `docs/runtime-agent-protocol.md`, including
compatibility aliases for existing artifact names.

## Task 4: Full Verification

**Files:**
- Test all files touched above.

- [ ] **Step 1: Run policy tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_source_body_audit_policy.py -q
```

Expected: PASS.

- [ ] **Step 2: Inspect diff**

Run:

```bash
git diff -- docs/superpowers/specs/2026-06-14-homework-a-gate-report-design.md docs/superpowers/plans/2026-06-14-homework-a-gate-report.md tests/test_source_body_audit_policy.py sub-skills/tasks/do-homework.md sub-skills/tools/assignment-recon.md docs/runtime-agent-protocol.md
```

Expected: diff only documents and tests the `do-homework [A]` compact findings contract.
