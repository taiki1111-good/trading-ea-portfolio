import json

from src.persistence.jsonl_log_writer import JsonlLogWriter


def test_jsonl_log_writer_creates_jsonl(tmp_path):
    path = tmp_path / "logs.jsonl"
    records = [{"a": 1}, {"b": "two"}]

    result = JsonlLogWriter.write(str(path), records, append=False)

    assert result.success
    assert result.record_count == 2
    assert result.persistence_reason

    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) == 2
    assert json.loads(lines[0]) == {"a": 1}
    assert json.loads(lines[1]) == {"b": "two"}


def test_jsonl_log_writer_appends_records(tmp_path):
    path = tmp_path / "logs.jsonl"

    JsonlLogWriter.write(str(path), [{"a": 1}], append=False)
    result = JsonlLogWriter.write(str(path), [{"b": 2}], append=True)

    assert result.success
    assert result.record_count == 1
    assert result.persistence_reason

    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) == 2
    assert json.loads(lines[1]) == {"b": 2}


def test_jsonl_log_writer_overwrites_file_when_append_false(tmp_path):
    path = tmp_path / "logs.jsonl"

    JsonlLogWriter.write(str(path), [{"a": 1}], append=False)
    JsonlLogWriter.write(str(path), [{"c": 3}], append=False)

    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) == 1
    assert json.loads(lines[0]) == {"c": 3}
