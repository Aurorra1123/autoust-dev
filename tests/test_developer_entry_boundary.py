from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_developer_entry_is_not_root_agents_for_user_mode_boundary():
    readme = read("README.md")
    readme_en = read("README.en.md")
    runtime_protocol = read("docs/runtime-agent-protocol.md")

    assert not (ROOT / "AGENTS.md").exists()
    assert "docs/DEVELOPMENT.md" in readme
    assert "docs/DEVELOPMENT.md" in readme_en
    assert "[AGENTS.md](./AGENTS.md)" not in readme
    assert "[AGENTS.md](./AGENTS.md)" not in readme_en
    assert "`docs/DEVELOPMENT.md`" in runtime_protocol
