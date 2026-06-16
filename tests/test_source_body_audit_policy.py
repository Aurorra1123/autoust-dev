from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def normalize_ws(text: str) -> str:
    return " ".join(text.split())


def assert_artifact_only_appears_in_forbidden_creation_context(
    policy_text: str, artifact: str
) -> None:
    allowed_markers = (
        "Do not create",
        "do not create",
        "must not write",
        "must not create",
        "Normal runs do not write",
        "no longer create",
        "not create",
        "not write",
        "not read",
        "not rely on",
        "ignore stale",
        "stale copies",
        "stale source",
        "stale artifact",
        "stale artifacts",
        "ignore",
        "remove",
        "clean rerun",
        "cleaning",
        "migration",
        "historical",
        "older runs",
        "old artifacts",
        "compatibility aliases",
    )
    lines = policy_text.splitlines()
    offenders = []
    for index, line in enumerate(lines):
        if artifact not in line:
            continue

        context = "\n".join(lines[max(0, index - 1) : index + 2])
        normalized_context = context.lower()
        if not any(marker.lower() in normalized_context for marker in allowed_markers):
            offenders.append(f"{index + 1}: {line.strip()}")

    assert offenders == []


def test_assignment_recon_uses_reference_collector_and_announcements():
    text = read("sub-skills/tasks/background-recon.md")

    assert "reference_collector" in text
    assert "canvas/announcements.json" in text
    assert "references/REFERENCE_INDEX.md" in text
    assert "references/canvas_native/" in text
    assert "copy" in text
    assert "verbatim" in text
    assert "references/**/*.pdf.links.json" in text
    assert "references/syllabus/" not in text


def test_do_homework_defines_direct_source_reference_boundary():
    text = "\n".join(
        [
            read("sub-skills/tasks/do-homework.md"),
            read("sub-skills/tasks/background-recon.md"),
        ]
    )

    assert "reference_collector" in text
    assert "references/REFERENCE_INDEX.md" in text
    assert "references/canvas_native/" in text
    assert "Main Agent" in text
    assert "complete original" in text
    assert "Do not create `reading_plan.compact.json`" in text
    assert "Do not create `source_findings.compact.md`" in text
    assert "Subagents must not write final `spec.md`" in text
    assert "proposal/research/open-ended" in text


def test_standard_homework_recon_removes_source_scout_pipeline():
    policy_text = "\n".join(
        [
            read("skill.md"),
            read("sub-skills/tasks/do-homework.md"),
            read("sub-skills/tasks/background-recon.md"),
            read("docs/runtime-agent-protocol.md"),
        ]
    )

    assert "source_scout_pipeline_used" in policy_text
    assert "source_scout_pipeline_used\": false" in policy_text or '"source_scout_pipeline_used": false' in policy_text
    assert "metadata_scout -> reading_plan.compact.json -> content_scout -> source_findings.compact.md" not in policy_text
    assert "must dispatch real child subagents with" not in policy_text
    assert "Do not dispatch `content_scout` until `metadata_scout` has produced" not in policy_text


def test_reference_collector_preserves_canvas_native_sources_verbatim():
    policy_text = "\n".join(
        [
            read("skill.md"),
            read("sub-skills/tasks/do-homework.md"),
            read("sub-skills/tasks/background-recon.md"),
            read("sub-skills/tasks/task-orchestrator.md"),
            read("docs/runtime-agent-protocol.md"),
        ]
    )

    assert "references/canvas_native/" in policy_text
    assert "source.json" in policy_text
    assert "source.txt" in policy_text
    assert "ORIGIN.md" in policy_text
    assert "verbatim" in policy_text
    assert "must not summarize" in policy_text or "must not paraphrase" in policy_text


def test_reference_collector_preserves_announcements_per_relevant_object():
    policy_text = "\n".join(
        [
            read("skill.md"),
            read("sub-skills/tasks/do-homework.md"),
            read("sub-skills/tasks/background-recon.md"),
            read("docs/runtime-agent-protocol.md"),
        ]
    )
    normalized_policy_text = normalize_ws(policy_text)

    assert "Announcement arrays are collection snapshots, not source objects." in policy_text
    assert "Do not copy the full `canvas/announcements.json` array" in normalized_policy_text
    assert "references/canvas_native/announcement-<id-or-slug>/source.json" in policy_text
    assert "canvas/announcements.json#id=" in policy_text
    assert (
        "Non-empty `review_a.json.relevant_announcements` entries must all be "
        "preserved `references/canvas_native/announcement-<id-or-slug>/source.json` paths"
    ) in normalized_policy_text
    assert "When no announcement is relevant, `relevant_announcements` must be `[]`" in normalized_policy_text
    assert "entire announcements array" not in policy_text
    assert "entire announcements JSON array" not in policy_text


def test_reference_collector_dispatch_is_auditable():
    policy_text = "\n".join(
        [
            read("sub-skills/tasks/do-homework.md"),
            read("sub-skills/tasks/background-recon.md"),
            read("docs/runtime-agent-protocol.md"),
            read("docs/development-validation-standard.md"),
        ]
    )
    normalized_policy_text = normalize_ws(policy_text)

    assert (
        "The `reference_collector` dispatch must be recorded in "
        "`stage_reviews/child_dispatch_ledger.json`"
    ) in normalized_policy_text
    assert "handwritten alias such as `reference_collector_<course>_<assignment>`" in policy_text
    assert "An empty dispatch ledger cannot prove `reference_collector_used: true`" in normalized_policy_text
    assert '"role": "reference_collector"' in policy_text
    assert '"agent_id"' in policy_text
    assert '"transcript_handle"' in policy_text


def test_entry_docs_describe_reference_collector_not_old_source_scout_chain():
    entry_text = "\n".join(
        [
            read("README.md"),
            read("README.en.md"),
            read("README.quick.md"),
            read("docs/COLLABORATION.md"),
            read("docs/ROADMAP.md"),
            read("sub-skills/tools/canvascli-api.md"),
        ]
    )
    normalized_entry_text = normalize_ws(entry_text)

    assert "reference_collector" in entry_text
    assert "references/REFERENCE_INDEX.md" in entry_text
    assert "references/canvas_native/announcement-<id-or-slug>/source.json" in entry_text
    assert "canvas/announcements.json#id=" in entry_text
    assert "metadata_scout builds the source index" not in normalized_entry_text
    assert "content_scout reads assigned source bodies" not in normalized_entry_text
    assert "source_findings.compact.md` as normal" not in normalized_entry_text


def test_main_agent_reads_references_not_old_source_findings():
    policy_text = "\n".join(
        [
            read("skill.md"),
            read("sub-skills/tasks/do-homework.md"),
            read("sub-skills/tasks/background-recon.md"),
            read("sub-skills/tasks/task-orchestrator.md"),
            read("docs/runtime-agent-protocol.md"),
        ]
    )

    assert "references/REFERENCE_INDEX.md" in policy_text
    assert "references/source_docs/" in policy_text
    assert "references/canvas_native/" in policy_text

    forbidden_legacy_interfaces = [
        "parent_source_read_requests",
        "metadata_scout -> reading_plan.compact.json -> content_scout -> source_findings.compact.md",
        "source_findings.compact.md is the only multi-writer parent interface",
        "Multi-writer parent-interface rule: `source_findings.compact.md`",
        "normal parent read interface",
        "`source_findings.compact.md` as the Main Agent read interface",
        "source_findings.compact.md as the Main Agent read interface",
        "Main Agent must read `source_findings.compact.md`",
        "Main Agent reads `source_findings.compact.md`",
        "`source_findings.compact.md` summarizes the task-relevant result",
        "source_findings.compact.md summarizes the task-relevant result",
        "`source_findings.compact.md` as source scout output",
        "source_findings.compact.md as source scout output",
        "supporting sources are delegated to content scouts",
    ]
    for phrase in forbidden_legacy_interfaces:
        assert phrase not in policy_text


def test_reference_collector_review_fields_are_documented():
    policy_text = "\n".join(
        [
            read("sub-skills/tasks/do-homework.md"),
            read("sub-skills/tasks/background-recon.md"),
            read("docs/runtime-agent-protocol.md"),
        ]
    )

    assert '"announcements_checked": true' in policy_text
    assert '"reference_collector_used": true' in policy_text
    assert '"source_scout_pipeline_used": false' in policy_text
    assert '"assignment_shell_checked": true' in policy_text
    assert '"rubric_checked": true' in policy_text
    assert '"syllabus_checked": true' in policy_text
    assert '"reference_index_checked": true' in policy_text
    assert '"canvas_native_sources": []' in policy_text
    assert '"downloaded_references": []' in policy_text
    assert '"pdf_link_manifests_checked": true' in policy_text
    assert '"direct_spec_sources": []' in policy_text
    assert '"rubric_sources": []' in policy_text
    assert '"required_inputs": []' in policy_text
    assert '"relevant_announcements": []' in policy_text
    assert '"blocked_sources": []' in policy_text
    assert '"forbidden_or_stale_sources": []' in policy_text
    assert '"supporting_sources_skipped": []' in policy_text
    assert '"inputs_complete": true' in policy_text
    assert '"parent_self_check_complete": true' in policy_text
    assert '"verdict": "proceed"' in policy_text

    old_review_fields = [
        '"compact_reading_plan_approved"',
        '"source_findings_checked"',
        '"required_high_signal_body_evidence_checked"',
        '"appendix_paths"',
        '"parent_source_read_requests"',
    ]
    for field in old_review_fields:
        assert field not in policy_text


def test_reference_collector_forbids_old_artifacts_as_normal_run_outputs():
    policy_text = "\n".join(
        [
            read("sub-skills/tasks/do-homework.md"),
            read("sub-skills/tasks/background-recon.md"),
            read("docs/runtime-agent-protocol.md"),
        ]
    )

    assert "Do not create `reading_plan.compact.approved.json`" in policy_text
    assert "Do not create `investigation/_appendix/source_index.json`" in policy_text
    assert (
        "Do not create `body_evidence_fragments/`" in policy_text
        or "Do not create `investigation/_appendix/body_evidence_fragments/`" in policy_text
    )
    assert (
        "Do not create `scout_receipts/`" in policy_text
        or "Do not create `investigation/_appendix/scout_receipts/`" in policy_text
    )

    for artifact in [
        "reading_plan.compact.json",
        "reading_plan.compact.approved.json",
        "source_findings.compact.md",
        "source_index.json",
        "investigation/_appendix/source_index.json",
        "body_evidence_fragments/",
        "scout_receipts/",
    ]:
        assert_artifact_only_appears_in_forbidden_creation_context(
            policy_text, artifact
        )


def test_source_body_policy_keeps_ucug1808_only_in_acceptance_context():
    policy_text = "\n".join(
        [
            read("sub-skills/tasks/do-homework.md"),
            read("sub-skills/tasks/background-recon.md"),
            read("docs/runtime-agent-protocol.md"),
        ]
    )

    assert "UCUG1808" not in policy_text

    design_text = read(
        "docs/superpowers/specs/2026-06-13-homework-source-body-audit-design.md"
    )
    assert "UCUG1808 Acceptance Scenario" in design_text


def test_acceptance_scenario_fails_on_main_agent_manual_rescue_or_missing_terminal_artifacts():
    design_text = read(
        "docs/superpowers/specs/2026-06-13-homework-source-body-audit-design.md"
    )

    assert "Missing terminal reconnaissance artifacts are a failed acceptance run" in design_text
    assert "source_findings.compact.md alone is insufficient" in design_text
    assert "filesystem receipts without transcript evidence are recovery evidence, not clean child-isolation validation" in design_text


def test_recon_summary_scales_with_investigation_depth():
    policy_text = "\n".join(
        [
            read("sub-skills/tasks/background-recon.md"),
            read("docs/runtime-agent-protocol.md"),
        ]
    )

    assert "depth-adaptive" in policy_text
    assert "Scale the amount of user-facing detail with reconnaissance depth" in policy_text
    assert "methods guidance" in policy_text
    assert "timelines" in policy_text
    assert "important findings without opening audit JSON" in policy_text


def test_source_intake_confirmation_response_is_conclusion_first_not_artifact_inventory():
    text = read("sub-skills/tasks/background-recon.md")
    router_text = read("sub-skills/tasks/do-homework.md")
    skill_text = read("skill.md")
    planner_text = read("sub-skills/tasks/alignment-planning.md")
    normalized_text = normalize_ws(text)

    assert "### [A5] Recon Briefing + Source Confirmation" in text
    assert "The user-facing recon briefing must be conclusion-first" in text
    assert "State the main assignment conclusion first" in text
    assert "what the student must produce and which source controls that conclusion" in normalized_text
    assert "Give source findings before file links" in text
    assert "grading signals, due-date or source conflicts" in text
    assert "stale/forbidden context" in text
    assert "Ask only whether the reconnaissance understanding is correct" in text
    assert "file links only as a short optional audit appendix" in text

    assert "For the background-recon reconnaissance confirmation checkpoint" in skill_text
    assert "sub-skills/tasks/background-recon.md" in router_text
    assert "conclusion-first recon briefing" in skill_text

    assert "does not own the first full reconnaissance-results briefing" in planner_text
    assert "Do not repeat the full source-category evidence map" in planner_text


def test_source_intake_briefing_maps_findings_to_reference_categories():
    text = read("sub-skills/tasks/background-recon.md")
    planner_text = read("sub-skills/tasks/alignment-planning.md")
    normalized_text = normalize_ws(text)

    assert "source-category evidence map" in text
    assert "`references/source_docs/`" in text
    assert "`references/slides/`" in text
    assert "`references/external/`" in text
    assert "`references/canvas_native/`" in text
    assert "assignment shell" in text
    assert "syllabus" in text
    assert "announcements" in text
    assert "modules/pages" in text
    assert "rubric status" in text
    assert "For each relevant source category" in text
    assert "state what was learned from the body" in text
    assert "Do not collapse all evidence into `references/` or `Canvas sources`" in text
    assert "specific Canvas-native body such as the assignment shell, syllabus, announcement, module/page, or rubric status" in normalized_text

    assert "Do not repeat the full source-category evidence map" in planner_text
