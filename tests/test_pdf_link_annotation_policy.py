from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_assignment_recon_extracts_pdf_link_annotations_generically():
    text = read("sub-skills/tasks/background-recon.md")

    assert "PDF Link Annotation Extraction" in text
    assert "page.get_links()" in text
    assert "pdf_links.json" in text
    assert "anchor_text" in text
    assert "uri" in text
    assert "write an empty `[]` manifest" in text
    assert "record the failure in `investigation/unreachable.txt`" in text
    assert "Do not specialize this rule by URL domain" in text


def test_pdf_link_policy_does_not_name_course_or_resource_type_special_cases():
    policy_text = "\n".join(
        [
            read("tests/test_pdf_link_annotation_policy.py"),
            read("sub-skills/tasks/background-recon.md"),
            read("sub-skills/tasks/do-homework.md"),
            read("docs/runtime-agent-protocol.md"),
        ]
    )

    course_specific_name = "DSAA" + "2011"
    assert course_specific_name not in policy_text

    background_recon = read("sub-skills/tasks/background-recon.md")
    pdf_link_section = background_recon.split("### PDF Link Annotation Extraction", 1)[1]
    pdf_link_section = pdf_link_section.split("Record resources that cannot be fetched", 1)[0]

    for resource_type in ["Air Quality", "Student Dropout", "GitHub", "style file"]:
        assert resource_type not in pdf_link_section


def test_do_homework_requires_pdf_link_manifests_before_alignment():
    text = "\n".join(
        [
            read("sub-skills/tasks/do-homework.md"),
            read("sub-skills/tasks/background-recon.md"),
        ]
    )

    assert "PDF link annotation manifests" in text
    assert "references/*.pdf.links.json" in text
    assert "do not treat PDF text extraction as complete" in text


def test_runtime_protocol_preserves_rich_pdf_links_as_source_evidence():
    text = read("docs/runtime-agent-protocol.md")

    assert "PDF link annotations" in text
    assert "visible text layer" in text
    assert "references/*.pdf.links.json" in text
