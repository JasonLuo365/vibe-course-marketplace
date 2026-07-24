from pathlib import Path


def test_claude_installer_uses_the_release_tag_and_production_server() -> None:
    root = Path(__file__).resolve().parents[3]
    script = (root / "scripts" / "install-claude-submit.ps1").read_text(encoding="utf-8")

    assert 'v0.1.8' in script
    assert 'https://vibe.planlabopc.com' in script
    assert 'VIBE_SUBMIT_SERVER_URL' in script
    assert 'submit-homework' in script
