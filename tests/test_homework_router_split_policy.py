import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ALIGNMENT_PLANNING_PATH = "sub-skills/tasks/alignment-planning.md"
FIRST_STAGE_ROUTE_PATHS = {
    "sub-skills/tasks/background-recon.md",
    "sub-skills/tasks/existing-work-recon.md",
}
OLD_RUNTIME_PATHS = [
    "assignment-source-intake.md",
    "assignment-workflow-planner.md",
    "current-state-intake.md",
    "assignment-recon.md",
]


def read(path: str) -> str:
    target = ROOT / path
    assert target.exists(), f"Expected policy file to exist: {path}"
    return target.read_text(encoding="utf-8")


def referenced_runtime_paths(text: str) -> set[str]:
    return set(re.findall(r"sub-skills/(?:tasks|tools)/[-A-Za-z0-9_.]+\.md", text))


def assert_alignment_handoff_only_in_tail(text: str) -> None:
    assert text.count("## Tail Handoff") == 1
    assert text.count(ALIGNMENT_PLANNING_PATH) == 1

    before_tail, tail = text.split("## Tail Handoff", 1)
    assert ALIGNMENT_PLANNING_PATH not in before_tail
    assert ALIGNMENT_PLANNING_PATH in tail


def test_staged_route_files_exist_and_old_names_are_retired():
    assert (ROOT / "sub-skills/tasks/background-recon.md").exists()
    assert (ROOT / "sub-skills/tasks/existing-work-recon.md").exists()
    assert (ROOT / "sub-skills/tasks/alignment-planning.md").exists()

    assert not (ROOT / "sub-skills/tasks/assignment-source-intake.md").exists()
    assert not (ROOT / "sub-skills/tasks/assignment-workflow-planner.md").exists()
    assert not (ROOT / "sub-skills/tools/current-state-intake.md").exists()
    assert not (ROOT / "sub-skills/tools/assignment-recon.md").exists()


def test_router_exposes_only_first_stage_routes():
    router = read("sub-skills/tasks/do-homework.md")

    assert "sub-skills/tasks/background-recon.md" in router
    assert "sub-skills/tasks/existing-work-recon.md" in router
    assert referenced_runtime_paths(router) == FIRST_STAGE_ROUTE_PATHS
    assert "prelaunch_startup_inventory.json" in router
    assert "recommended_action" in router

    assert ALIGNMENT_PLANNING_PATH not in router
    assert "alignment-planning.md" not in router
    assert "task-orchestrator.md" not in router
    assert "assignment-workflow-planner.md" not in router
    assert "assignment-source-intake.md" not in router
    assert "current-state-intake.md" not in router
    assert "assignment-recon.md" not in router


def test_router_does_not_inline_source_existing_or_planner_bodies():
    router = read("sub-skills/tasks/do-homework.md")

    assert "### [B] Recon Summary + Alignment Loop" not in router
    assert "### [C] Design Pipeline" not in router
    assert "#### [A3] Canvas Generic Reconnaissance - Mandatory" not in router
    assert "Follow the Canvas Generic stages:" not in router
    assert "Retained Current-State Intake" not in router


def test_background_recon_owns_clean_start_and_tail_handoff_only():
    background = read("sub-skills/tasks/background-recon.md")

    assert "reference_collector" in background
    assert "canvas/announcements.json" in background
    assert "references/REFERENCE_INDEX.md" in background
    assert "references/canvas_native/" in background
    assert "investigation/review_a.json" in background
    assert "PDF Link Annotation Extraction" in background
    assert_alignment_handoff_only_in_tail(background)

    assert "### [B] Recon Summary + Alignment Loop" not in background
    assert "### [C] Design Pipeline" not in background
    assert "repair_plan.md" not in background


def test_existing_work_recon_owns_retained_state_and_tail_handoff_only():
    existing = read("sub-skills/tasks/existing-work-recon.md")

    assert "prelaunch_startup_inventory.json" in existing
    assert "retained user-visible artifacts" in existing
    assert "artifact/codebase/process-history/verification" in existing
    assert "allowlisted_history_files" in existing
    assert "investigation/explore_manifest.json" in existing
    assert "investigation/explore_context.md" in existing
    assert "investigation/repair_recon.md" in existing
    assert "must not write `spec.md`" in existing
    assert "must not run clean-start Canvas/source recon" in existing
    assert_alignment_handoff_only_in_tail(existing)

    assert "#### [A3] Canvas Generic Reconnaissance - Mandatory" not in existing
    assert "### [B] Recon Summary + Alignment Loop" not in existing
    assert "### [C] Design Pipeline" not in existing


def test_alignment_planning_owns_shared_alignment_and_refuses_first_stage_recon():
    planner = read("sub-skills/tasks/alignment-planning.md")
    normalized_planner = " ".join(planner.split())

    assert "### [B] Alignment Loop" in planner
    assert "### [B] Recon Summary + Alignment Loop" not in planner
    assert "### [C] Design Pipeline" in planner
    assert "repair_plan.md" in planner
    assert "repair_pipeline_design.md" in planner
    assert "Pipeline Review Status" in planner
    assert "does not run clean-start Canvas/source reconnaissance" in normalized_planner
    assert "sub-skills/tasks/background-recon.md" in planner
    assert "sub-skills/tasks/existing-work-recon.md" in planner

    assert "#### [A3] Canvas Generic Reconnaissance - Mandatory" not in planner
    assert "### [A5] Recon Briefing + Source Confirmation" not in planner
    assert "../tools/current-state-intake.md" not in planner


def test_startup_inventory_records_workbench_path():
    router = read("sub-skills/tasks/do-homework.md")
    background = read("sub-skills/tasks/background-recon.md")
    existing = read("sub-skills/tasks/existing-work-recon.md")

    assert '"work_dir": "data/homework/<COURSE>/<assignment>"' in router
    assert "work_dir is missing" in background
    assert "does not match the active workbench" in background
    assert "work_dir is missing" in existing
    assert "does not match the active workbench" in existing


def test_tools_index_no_longer_registers_routed_homework_stages_as_tools():
    index = read("sub-skills/tools/_index.md")

    assert "assignment-recon" not in index
    assert "current-state-intake" not in index
    assert "background-recon.md" not in index
    assert "existing-work-recon.md" not in index
    assert "alignment-planning.md [C]" in index


def test_active_docs_do_not_reference_retired_runtime_paths():
    active_docs = [
        "skill.md",
        "docs/runtime-agent-protocol.md",
        "docs/skills-architecture-spec.md",
        "docs/canvas-pilot-reference.md",
    ]

    policy_text = "\n".join(read(path) for path in active_docs)

    for old_path in OLD_RUNTIME_PATHS:
        assert old_path not in policy_text
