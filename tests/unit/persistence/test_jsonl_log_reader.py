from src.persistence.jsonl_log_reader import JsonlLogReader


def test_jsonl_log_reader_reads_jsonl_and_ignores_empty_lines(tmp_path):
    path = tmp_path / "logs.jsonl"
    path.write_text('{"a": 1}\n\n{"a": 2}\n', encoding="utf-8")

    result = JsonlLogReader.read(str(path), skip_invalid=False)

    assert result.success
    assert result.record_count == 2
    assert len(result.data) == 2
    assert result.persistence_reason


def test_jsonl_log_reader_skips_invalid_lines_with_warning(tmp_path):
    path = tmp_path / "logs.jsonl"
    path.write_text('{"a": 1}\n{invalid}\n{"a": 2}\n', encoding="utf-8")

    result = JsonlLogReader.read(str(path), skip_invalid=True)

    assert result.success
    assert result.record_count == 2
    assert len(result.data) == 2
    assert len(result.warnings) == 1
    assert result.persistence_reason


def test_jsonl_log_reader_fails_on_invalid_line_when_skip_invalid_false(tmp_path):
    path = tmp_path / "logs.jsonl"
    path.write_text('{"a": 1}\n{invalid}\n{"a": 2}\n', encoding="utf-8")

    result = JsonlLogReader.read(str(path), skip_invalid=False)

    assert not result.success
    assert result.record_count == 1
    assert result.data == []
    assert result.warnings
    assert result.persistence_reason
