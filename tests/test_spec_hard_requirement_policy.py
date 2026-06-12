from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_do_homework_records_non_downgradable_spec_requirements():
    text = read("sub-skills/tasks/do-homework.md")

    assert "Spec Hard Requirements / No-Downgrade Policy" in text
    assert "required_spec_constraints" in text
    assert "fallback_allowed_for_final: false" in text
    assert "Do not rewrite a hard requirement into a softer fallback" in text


def test_orchestrator_blocks_requirement_drift_before_draft_ready():
    text = read("sub-skills/tasks/task-orchestrator.md")

    assert "Spec hard requirement no-downgrade gate" in text
    assert "spec -> pipeline -> stage brief -> artifact -> verification" in text
    assert "hard_requirement_inventory" in text
    assert "diff it against `required_spec_constraints`" in text
    assert "source, requirement, applies_to, required_evidence, status" in text
    assert "must not mark `draft_ready`" in text
    assert "fallback output is only preview/debug" in text


def test_tools_treat_fallback_as_non_final_for_any_hard_requirement():
    writing_helper = read("sub-skills/tools/writing-helper.md")
    pdf_renderer = read("sub-skills/tools/pdf-renderer.md")

    assert "required_spec_constraints" in writing_helper
    assert "must not weaken" in writing_helper
    assert "prose deliverable or stage artifact" in writing_helper
    assert "required_spec_constraints" in pdf_renderer
    assert "does not satisfy" in pdf_renderer
    assert "final deliverable" in pdf_renderer


def test_architecture_docs_describe_general_no_downgrade_policy():
    runtime_protocol = read("docs/runtime-agent-protocol.md")
    architecture_spec = read("docs/skills-architecture-spec.md")

    assert "required_spec_constraints" in runtime_protocol
    assert "no-downgrade" in runtime_protocol.lower()
    assert "required_spec_constraints" in architecture_spec
    assert "fallback_allowed_for_final: false" in architecture_spec
    assert "spec_compliance: true" in architecture_spec
