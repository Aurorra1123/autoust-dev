from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_root_agent_bootstrap_points_to_skill_without_replacing_development_entry():
    readme = read("README.md")
    readme_en = read("README.en.md")
    runtime_protocol = read("docs/runtime-agent-protocol.md")
    normalized_runtime_protocol = " ".join(runtime_protocol.split())
    gitignore = read(".gitignore")
    agents = read("AGENTS.md")
    claude = read("CLAUDE.md")

    assert (ROOT / "AGENTS.md").exists()
    assert (ROOT / "CLAUDE.md").exists()
    assert "docs/DEVELOPMENT.md" in readme
    assert "docs/DEVELOPMENT.md" in readme_en
    assert "[AGENTS.md](./AGENTS.md)" not in readme
    assert "[AGENTS.md](./AGENTS.md)" not in readme_en
    assert "`docs/DEVELOPMENT.md`" in runtime_protocol
    assert "\nAGENTS.md\n" not in f"\n{gitignore}\n"
    assert "\nCLAUDE.md\n" not in f"\n{gitignore}\n"

    for bootstrap in (agents, claude):
        assert "skill.md" in bootstrap
        assert "docs/DEVELOPMENT.md" in bootstrap
        assert "Do not preload" in bootstrap
        assert "sub-skills/tasks/*.md" in bootstrap
        assert "sub-skills/tasks/index.md" not in bootstrap
        assert "background-recon.md = clean-start task background recon" not in bootstrap
        assert "alignment-planning.md = user alignment" not in bootstrap

    assert (
        "Committed root `AGENTS.md` and `CLAUDE.md` files are bootstrap pointers to `skill.md`"
        in normalized_runtime_protocol
    )
