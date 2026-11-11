import sys
from types import SimpleNamespace

import pytest

from rave import cli


def test_cli_reports_provider_error_without_traceback(monkeypatch, capsys):
    class FailingHive:
        async def run(self, question, scope):
            raise RuntimeError("LLM provider returned HTTP 429 (code=credit_balance_exhausted)")

    settings = SimpleNamespace(api_key="test", base_url="https://api.openai.com/v1", model="test",
        temperature=0.2, timeout_seconds=30, output_dir="data/runs", web_search_enabled=False,
        web_search_model="test", max_concurrent_requests=1)
    monkeypatch.setattr(cli.Settings, "from_env", lambda: settings)
    monkeypatch.setattr(cli, "HiveCore", lambda *_args: FailingHive())
    monkeypatch.setattr(sys, "argv", ["rave", "hive", "question"])

    with pytest.raises(SystemExit) as error:
        cli.main()

    stderr = capsys.readouterr().err
    assert error.value.code == 1
    assert "credit_balance_exhausted" in stderr
    assert "Traceback" not in stderr
