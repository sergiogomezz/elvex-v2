import sys

from elvex.core.errors import WorkflowReliabilityError
from elvex.cli import main as cli_main
from elvex.llms.errors import LLMQuotaError


def test_cli_prints_friendly_provider_error(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["elvex", "--prompt", "demo"])
    monkeypatch.setattr(cli_main, "landing_intro", lambda: None)
    monkeypatch.setattr(cli_main, "loading_animation", lambda: lambda: None)
    monkeypatch.setattr(
        cli_main,
        "create_workflow",
        lambda prompt: (_ for _ in ()).throw(LLMQuotaError("Insufficient quota on OpenAI API.")),
    )

    exit_code = cli_main.main()

    assert exit_code == 1
    assert "Error: Insufficient quota on OpenAI API." in capsys.readouterr().out


def test_cli_prints_friendly_workflow_error(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["elvex", "--prompt", "demo"])
    monkeypatch.setattr(cli_main, "landing_intro", lambda: None)
    monkeypatch.setattr(cli_main, "loading_animation", lambda: lambda: None)
    monkeypatch.setattr(
        cli_main,
        "create_workflow",
        lambda prompt: (_ for _ in ()).throw(WorkflowReliabilityError("Worker failed cleanly.")),
    )

    exit_code = cli_main.main()

    assert exit_code == 1
    assert "Error: Worker failed cleanly." in capsys.readouterr().out
