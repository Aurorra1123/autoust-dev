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
    assert "`content_scout` Subagent receipts" in stage_four


def test_runtime_protocol_splits_source_spec_domain_into_subagent_roles():
    text = read("docs/runtime-agent-protocol.md")

    assert "metadata_scout" in text
    assert "content_scout" in text
    assert "coverage_reviewer" in text
    assert "source_body_audit.json" in text
    assert "source_body_audit_fragments/" in text
    assert "Main Agent remains the final reconnaissance judge" in text
    assert "references/syllabus/" not in text


def test_raw_canvas_json_is_canonical_not_lossy_reference_extract():
    policy_text = "\n".join(
        [
            read("sub-skills/tools/assignment-recon.md"),
            read("sub-skills/tasks/do-homework.md"),
            read("docs/runtime-agent-protocol.md"),
            read("sub-skills/tasks/task-orchestrator.md"),
        ]
    )

    assert "raw Canvas JSON is the canonical evidence" in policy_text
    assert "derived readable artifacts are optional convenience copies" in policy_text
    assert "summary-only scout output must never replace raw Canvas JSON" in policy_text
    assert "stage briefs must explicitly allow relevant `canvas/*.json` reads" in policy_text
    assert "Do not require `references/*syllabus*` as the evidence gate" in policy_text


def test_content_scouts_narrow_but_do_not_replace_main_agent_source_reads():
    policy_text = "\n".join(
        [
            read("sub-skills/tools/assignment-recon.md"),
            read("sub-skills/tasks/do-homework.md"),
            read("sub-skills/tasks/task-orchestrator.md"),
            read("docs/runtime-agent-protocol.md"),
        ]
    )

    assert "Content scouts narrow the read set; they do not replace Main Agent source reading" in policy_text
    assert "scout summaries are routing hints, not source evidence" in policy_text
    assert "Main Agent must read the narrowed source bodies before writing or revising `spec.md`" in policy_text
    assert "required/allowed reads must include the source files or raw `canvas/*.json` paths" in policy_text


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

    design_text = read(
        "docs/superpowers/specs/2026-06-13-homework-source-body-audit-design.md"
    )
    assert "UCUG1808 Acceptance Scenario" in design_text


def test_reconvergence_gate_requires_terminal_recon_artifacts():
    policy_text = "\n".join(
        [
            read("sub-skills/tasks/do-homework.md"),
            read("sub-skills/tools/assignment-recon.md"),
            read("docs/runtime-agent-protocol.md"),
        ]
    )

    assert "reconvergence gate" in policy_text
    assert "coverage feedback is not a terminal reconnaissance verdict" in policy_text
    assert "missing `spec.md`, `investigation/rubric.md`, or `investigation/review_a.json`" in policy_text
    assert "must write a recover/blocking `review_a.json` or `stage_reviews/process_concerns.jsonl`" in policy_text


def test_acceptance_scenario_fails_on_main_agent_manual_rescue_or_missing_terminal_artifacts():
    design_text = read(
        "docs/superpowers/specs/2026-06-13-homework-source-body-audit-design.md"
    )

    assert "Missing terminal reconnaissance artifacts are a failed acceptance run" in design_text
    assert "source_coverage_feedback.json alone is insufficient" in design_text
    assert "filesystem receipts without transcript evidence are recovery evidence, not clean child-isolation validation" in design_text


def test_source_scout_taxonomy_requires_real_child_dispatch_not_simulated_scouts():
    policy_text = "\n".join(
        [
            read("sub-skills/tasks/do-homework.md"),
            read("sub-skills/tools/assignment-recon.md"),
            read("docs/runtime-agent-protocol.md"),
            read("docs/development-validation-standard.md"),
        ]
    )

    assert "`source_spec` is a Main Agent exploration domain, not a dispatchable Subagent" in policy_text
    assert "must dispatch real child subagents with" in policy_text
    assert "`scout_type` values `metadata_scout`, `content_scout`" in policy_text
    assert "`coverage_reviewer`" in policy_text
    assert "Main Agent inline recovery must be recorded as recovery evidence" in policy_text
    assert "not as a\n  Subagent receipt" in policy_text
    assert "`content_scout` is the Subagent role" in policy_text
    assert "Content subdivisions are `scope` values" in policy_text
    assert "Do not create successful child identities named" in policy_text


def test_clean_start_proposal_checklist_blocks_self_certified_json_completion():
    text = read("sub-skills/tasks/do-homework.md")

    assert "Clean-Start Proposal Runtime Checklist" in text
    assert "STOP before `[B]` unless all three required child subagents have real dispatch ids" in text
    assert "A `recover` from `coverage_reviewer` is a gate failure until coverage is re-run by a child subagent" in text
    assert "Do not turn \"simulate I am the user\" into Main-Agent permission to choose the project direction" in text
    assert "Write `investigation/recon_summary.md` as the human-readable entrance to reconnaissance" in text
    assert "JSON files are machine evidence, not the user-facing completion story" in text
