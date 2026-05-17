# 2026-05-03 pytest import path stabilization

## 対応内容
- `pytest -q` 実行時に `src` / `scripts` が見えず collection error になる問題に対応。
- repo ルートに `conftest.py` を追加し、実行時に repo root を `sys.path` 先頭へ追加するようにした。
- これにより `PYTHONPATH=.` を毎回明示しなくても import 解決できる構成に統一した。

## 方針
- 売買ロジック・backtestロジック・Candidate Freeze v0.1 の内容は変更しない。
- テスト標準実行は `pytest -q` とする。
