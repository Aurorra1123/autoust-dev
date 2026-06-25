from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    target = ROOT / path
    assert target.exists(), f"Expected policy file to exist: {path}"
    return target.read_text(encoding="utf-8")


def normalize_ws(text: str) -> str:
    return " ".join(text.split())


def test_tools_index_exposes_single_literature_search_tool():
    index = read("sub-skills/tools/_index.md")

    assert "| **literature-search** | [literature-search.md](./literature-search.md)" in index
    assert "search_literature" in index
    assert "| **paper-search** |" not in index
    assert "Literature search via arxiv" not in index
    assert "search_papers" not in index


def test_literature_search_contract_outputs_auditable_best_effort_results():
    text = read("sub-skills/tools/literature-search.md")
    normalized_text = normalize_ws(text)

    for artifact in [
        "literature/search_log.jsonl",
        "literature/candidates.json",
        "literature/included_sources.json",
        "literature/excluded_sources.json",
        "literature/access_blockers.md",
        "literature/references.bib",
        "literature/literature_search_report.md",
    ]:
        assert artifact in text

    for status in [
        "metadata_only",
        "abstract_read",
        "outline_read",
        "full_text_available",
        "full_text_read",
        "needs_manual_download",
        "blocked",
    ]:
        assert status in text

    assert "search_plan.md" not in text
    assert "automatic fallback" in normalized_text
    assert "parallel Subagents" in text
    assert "must not treat abstracts or metadata as full-text evidence" in normalized_text


def test_literature_search_documents_provider_auth_and_degraded_mode():
    text = read("sub-skills/tools/literature-search.md")
    normalized_text = normalize_ws(text)

    assert "Provider authentication" in text
    assert "OpenAlex" in text
    assert "API key required" in text
    assert "CORE" in text
    assert "Semantic Scholar" in text
    assert "degraded mode" in normalized_text
    assert "Crossref" in text
    assert "PubMed/NCBI E-utilities" in text
    assert "Europe PMC" in text
    assert "ERIC" in text
    assert "arXiv" in text
    assert "skip" in normalized_text or "unavailable" in normalized_text


def test_legacy_paper_search_is_compatibility_alias_not_active_contract():
    text = read("sub-skills/tools/paper-search.md")
    normalized_text = normalize_ws(text)

    assert "compatibility" in normalized_text
    assert "literature-search.md" in text
    assert "arXiv" in text
    assert "not a standalone active pipeline tool" in normalized_text


def test_pipeline_guidance_uses_literature_search_not_paper_search():
    planner = read("sub-skills/tasks/alignment-planning.md")
    orchestrator = read("sub-skills/tasks/task-orchestrator.md")
    policy_text = "\n".join([planner, orchestrator])

    assert "literature-search" in policy_text
    assert "paper-search →" not in policy_text
    assert "`paper-search.md`" not in policy_text
    assert "`literature-search.md`" in policy_text


def test_writing_helper_consumes_literature_outputs_with_root_bib_compatibility():
    text = read("sub-skills/tools/writing-helper.md")
    normalized_text = normalize_ws(text)

    assert "literature/references.bib" in text
    assert "literature/literature_search_report.md" in text
    assert "references.bib" in text
    assert "compatibility" in normalized_text
    assert "from paper-search" not in text
