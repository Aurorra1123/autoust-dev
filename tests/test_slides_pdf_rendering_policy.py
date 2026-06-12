from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_slide_maker_declares_controlled_renderer_paths_and_no_unrecorded_fallbacks():
    text = read("sub-skills/tools/slide-maker.md")

    assert "Controlled Renderer Policy" in text
    assert "guizang" in text
    assert "beamer" in text
    assert "PyMuPDF" in text
    assert "not a third final renderer path" in text
    assert "render script" in text
    assert "font strategy" in text
    assert "replacement-glyph" in text


def test_orchestrator_preserves_tool_contracts_in_stage_briefs():
    text = read("sub-skills/tasks/task-orchestrator.md")

    assert "Tool Contract Preservation Gate" in text
    assert "renderer_path" in text
    assert "allowed_renderer_paths" in text
    assert "do not invent a new final renderer" in text
    assert "render_command_or_script" in text


def test_final_verification_checks_slides_pdf_glyph_and_font_evidence():
    text = read("sub-skills/tasks/task-orchestrator.md")
    runtime = read("docs/runtime-agent-protocol.md")

    for required in [
        "pdffonts",
        "pdftotext",
        "replacement-glyph",
        "line-leading question marks",
        "font embedding",
    ]:
        assert required in text
        assert required in runtime
