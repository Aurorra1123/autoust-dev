from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    target = ROOT / path
    assert target.exists(), f"Expected policy file to exist: {path}"
    return target.read_text(encoding="utf-8")


def test_split_files_exist_and_router_names_routes():
    router = read("sub-skills/tasks/do-homework.md")

    assert (ROOT / "sub-skills/tasks/assignment-source-intake.md").exists()
    assert (ROOT / "sub-skills/tasks/assignment-workflow-planner.md").exists()
    assert (ROOT / "sub-skills/tools/current-state-intake.md").exists()
    assert "sub-skills/tasks/assignment-source-intake.md" in router
    assert "sub-skills/tasks/assignment-workflow-planner.md" in router
    assert "prelaunch_startup_inventory.json" in router
    assert "recommended_action" in router


def test_router_does_not_inline_source_or_planner_bodies():
    router = read("sub-skills/tasks/do-homework.md")

    assert "### [B] Recon Summary + Alignment Loop" not in router
    assert "### [C] Design Pipeline" not in router
    assert "#### [A3] Canvas Generic Reconnaissance - Mandatory" not in router
    assert "Follow the Canvas Generic stages:" not in router


def test_source_intake_owns_clean_start_recon_only():
    source = read("sub-skills/tasks/assignment-source-intake.md")

    assert "assignment-recon.md" in source
    assert "reference_collector" in source
    assert "references/REFERENCE_INDEX.md" in source
    assert "investigation/review_a.json" in source
    assert "sub-skills/tasks/assignment-workflow-planner.md" in source
    assert "### [B] Recon Summary + Alignment Loop" not in source
    assert "### [C] Design Pipeline" not in source


def test_workflow_planner_owns_alignment_pipeline_and_retained_entry():
    planner = read("sub-skills/tasks/assignment-workflow-planner.md")

    assert "### [B] Recon Summary + Alignment Loop" in planner
    assert "### [C] Design Pipeline" in planner
    assert "../tools/current-state-intake.md" in planner
    assert "repair_plan.md" in planner
    assert "repair_pipeline_design.md" in planner
    assert "Pipeline Review Status" in planner
    assert "#### [A3] Canvas Generic Reconnaissance - Mandatory" not in planner


def test_current_state_intake_tool_boundary():
    text = read("sub-skills/tools/current-state-intake.md")

    assert "prelaunch_startup_inventory.json" in text
    assert "retained user-visible artifacts" in text
    assert "artifact/codebase/process-history/verification" in text
    assert "allowlisted_history_files" in text
    assert "investigation/explore_manifest.json" in text
    assert "investigation/explore_context.md" in text
    assert "investigation/repair_recon.md" in text
    assert "must not write `spec.md`" in text
    assert "must not run clean-start Canvas/source recon" in text


def test_tools_index_registers_current_state_intake():
    index = read("sub-skills/tools/_index.md")

    assert "current-state-intake" in index
    assert "[current-state-intake.md](./current-state-intake.md)" in index
    assert "retained" in index
