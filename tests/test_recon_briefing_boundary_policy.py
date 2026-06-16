from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_source_intake_owns_recon_briefing_confirmation_gate():
    source_intake = read("sub-skills/tasks/background-recon.md")

    assert "### [A5] Recon Briefing + Source Confirmation" in source_intake
    assert "State the main assignment conclusion first" in source_intake
    assert "source-category evidence map" in source_intake
    assert "Ask only whether the reconnaissance understanding is correct" in source_intake
    assert "Do not ask for topic, research question, group facts, or method choice" in source_intake
    assert "Only after the user confirms the reconnaissance briefing" in source_intake


def test_workflow_planner_starts_after_recon_confirmation_and_owns_alignment_only():
    planner = read("sub-skills/tasks/alignment-planning.md")

    assert "requires a confirmed reconnaissance briefing" in planner
    assert "does not own the first full reconnaissance-results briefing" in planner
    assert "Do not repeat the full source-category evidence map" in planner
    assert "### [B] Alignment Loop" in planner
    assert "### [B] Recon Summary + Alignment Loop" not in planner
    assert "Conclusion-first `[B]` response rule" not in planner


def test_top_level_checkpoints_split_recon_confirmation_from_alignment():
    skill = read("skill.md")

    assert "After exploration, present the reconnaissance briefing and ask the user to confirm the source understanding." in skill
    assert "After reconnaissance confirmation, run the alignment loop." in skill
    assert "For the source-intake reconnaissance confirmation checkpoint" in skill
    assert "For the homework workflow-planner `[B]` alignment checkpoint" not in skill
