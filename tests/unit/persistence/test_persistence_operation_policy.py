def test_gitignore_includes_logs_directory():
    from pathlib import Path

    gitignore_path = Path(__file__).resolve().parents[3] / ".gitignore"
    gitignore_text = gitignore_path.read_text(encoding="utf-8")

    assert "logs/" in gitignore_text.splitlines()
