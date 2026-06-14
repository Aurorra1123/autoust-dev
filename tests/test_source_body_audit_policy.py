from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_assignment_recon_requires_source_body_audit_and_read_modes():
    text = read("sub-skills/tools/assignment-recon.md")

    assert "investigation/_appendix/source_index.json" in text
    assert "investigation/_appendix/body_evidence_fragments/" in text
    assert "source_findings.compact.md" in text
    assert "reading_plan.compact.json" in text
    assert "compatibility aliases" in text
    assert "metadata_only" in text
    assert "pdf_text_plus_links" in text
    assert "keyword windows" in text
    assert "references/**/*.pdf.links.json" in text
    assert "references/syllabus/" not in text


def test_do_homework_defines_main_agent_and_scout_boundaries():
    text = read("sub-skills/tasks/do-homework.md")

    assert "metadata_scout" in text
    assert "content_scout" in text
    assert "The Main Agent approves `reading_plan.compact.json`" in text
    assert "Subagents must not write final `spec.md`" in text
    assert "proposal/research/open-ended" in text
    assert "investigation/_appendix/body_evidence_fragments/" in text
    assert "source_findings.compact.md" in text
    assert "The Main Agent must not normally read full appendix artifacts" in text
    assert "`investigation/_appendix/compatibility_aliases/`" in text
    assert "Multi-writer parent-interface rule" in text
    assert "append-only scoped sections" in text
    assert "Main Agent read boundary" in text
    assert "Never load the whole appendix directory" in text
    assert "as context" in text
    assert "supporting topic context" in text
    assert "reading budget" in text


def test_do_homework_stage_four_reviews_source_audit_inputs():
    text = read("sub-skills/tasks/do-homework.md")

    stage_four = text.split("4. **Stage 4 review investigation**", 1)[1]
    stage_four = stage_four.split("5. **Stage 5 classify-output**", 1)[0]

    assert "reading_plan.compact.json" in stage_four
    assert "source_findings.compact.md" in stage_four
    assert "recovery/debug evidence, not default parent reads" in stage_four


def test_runtime_protocol_splits_source_spec_domain_into_subagent_roles():
    text = read("docs/runtime-agent-protocol.md")

    assert "metadata_scout" in text
    assert "content_scout" in text
    assert "source_findings.compact.md" in text
    assert "body_evidence_fragments/" in text
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


def test_hybrid_gate_report_limits_main_agent_source_reads():
    policy_text = "\n".join(
        [
            read("sub-skills/tools/assignment-recon.md"),
            read("sub-skills/tasks/do-homework.md"),
            read("sub-skills/tasks/task-orchestrator.md"),
            read("docs/runtime-agent-protocol.md"),
        ]
    )

    assert "Hybrid Gate Report" in policy_text
    assert "direct-spec strong match" in policy_text
    assert "The Main Agent must not normally read full appendix artifacts" in policy_text
    assert "standard reconnaissance must not read\n`investigation/_appendix/` as task context" in policy_text
    assert "source_findings.compact.md" in policy_text
    assert "parent_source_read_requests" in policy_text
    assert "Scout summaries are routing hints, not source" in policy_text
    assert "supporting sources are delegated to content scouts" in policy_text
    assert "required/allowed reads must include the source files or raw `canvas/*.json` paths" in policy_text


def test_homework_a_gate_report_artifacts_are_documented():
    combined = "\n".join(
        [
            read("sub-skills/tasks/do-homework.md"),
            read("sub-skills/tools/assignment-recon.md"),
            read("docs/runtime-agent-protocol.md"),
        ]
    )

    assert "reading_plan.compact.json" in combined
    assert "source_findings.compact.md" in combined
    assert "investigation/_appendix/source_index.json" in combined
    assert "investigation/_appendix/body_evidence_fragments/" in combined
    assert "compatibility aliases" in combined
    forbidden_terms = [
        "coverage" + "_reviewer",
        "coverage" + "_review.full.json",
        "recon" + "_gate.json",
    ]
    for term in forbidden_terms:
        assert term not in combined


def test_pitfalls_record_generic_proposal_methods_failure_mode():
    text = read("docs/PITFALLS.md")

    assert "proposal framework is not complete reconnaissance" in text
    assert "methods/topic-selection" in text
    assert "reading_plan.compact.json" in text
    assert "source_findings.compact.md" in text
    assert "parent self-check" in text


def test_skill_entrypoint_uses_compact_homework_a_chain():
    text = read("skill.md")

    homework_section = text.split("### Homework / Drafting", 1)[1]
    homework_section = homework_section.split("Never draft from just", 1)[0]

    assert "investigation/reading_plan.compact.json" in homework_section
    assert "investigation/source_findings.compact.md" in homework_section
    assert "investigation/_appendix/source_index.json" in homework_section
    assert "investigation/_appendix/body_evidence_fragments/" in homework_section
    assert "audit/recovery evidence" in homework_section
    forbidden_terms = [
        "source" + "_coverage_feedback.json",
        "coverage" + "_reviewer",
        "recon" + "_gate.json",
    ]
    for term in forbidden_terms:
        assert term not in homework_section


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

    assert "parent self-check" in policy_text
    assert "Scout output is\nnot a terminal reconnaissance verdict" in policy_text
    assert "missing `spec.md`, `investigation/rubric.md`, or `investigation/review_a.json`" in policy_text
    assert "must write a recover/blocking `review_a.json` or `stage_reviews/process_concerns.jsonl`" in policy_text


def test_acceptance_scenario_fails_on_main_agent_manual_rescue_or_missing_terminal_artifacts():
    design_text = read(
        "docs/superpowers/specs/2026-06-13-homework-source-body-audit-design.md"
    )

    assert "Missing terminal reconnaissance artifacts are a failed acceptance run" in design_text
    assert "source_findings.compact.md alone is insufficient" in design_text
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
    assert "`scout_type` values `metadata_scout` and `content_scout`" in policy_text
    assert "Main Agent inline recovery must be recorded as recovery evidence" in policy_text
    assert "not as a\n  Subagent receipt" in policy_text
    assert "`content_scout` is the Subagent role" in policy_text
    assert "Content subdivisions are `scope` values" in policy_text
    assert "Do not create successful child identities named" in policy_text


def test_clean_start_proposal_checklist_blocks_self_certified_json_completion():
    text = read("sub-skills/tasks/do-homework.md")

    assert "Clean-Start Proposal Runtime Checklist" in text
    assert "STOP before `[B]` unless metadata and content child evidence exists" in text
    assert "Do not turn \"simulate I am the user\" into Main-Agent permission to choose the project direction" in text
    assert "Write `investigation/recon_summary.md` as the human-readable entrance to reconnaissance" in text
    assert "JSON files are machine evidence, not the user-facing completion story" in text


def test_recon_summary_scales_with_investigation_depth():
    policy_text = "\n".join(
        [
            read("sub-skills/tasks/do-homework.md"),
            read("docs/runtime-agent-protocol.md"),
        ]
    )

    assert "depth-adaptive" in policy_text
    assert "Scale the\n   amount of user-facing detail with reconnaissance depth" in policy_text
    assert "methods/topic guidance, timeline/calendar facts" in policy_text
    assert "Do not collapse it into \"supporting context checked.\"" in policy_text
    assert "Important source bodies should not be\ncollapsed into vague phrases" in policy_text


def test_source_scout_pipeline_has_strict_stage_order():
    policy_text = "\n".join(
        [
            read("sub-skills/tasks/do-homework.md"),
            read("sub-skills/tools/assignment-recon.md"),
            read("docs/runtime-agent-protocol.md"),
        ]
    )

    assert "strict sequential gates, not parallel phases" in policy_text
    assert "Do not dispatch `content_scout` until `metadata_scout` has produced" in policy_text
    assert "metadata_scout -> reading_plan.compact.json -> content_scout -> source_findings.compact.md" in policy_text
    assert ("coverage" + "_reviewer") not in policy_text
