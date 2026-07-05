import importlib.util
import sys
from pathlib import Path

from elvex.llms.errors import LLMQuotaError


def _load_main_local_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "main_local.py"
    spec = importlib.util.spec_from_file_location("main_local", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_main_local_prints_friendly_provider_error(monkeypatch, capsys):
    main_local = _load_main_local_module()

    monkeypatch.setattr(sys, "argv", ["main_local.py", "--prompt", "demo"])
    monkeypatch.setattr(main_local, "landing_intro", lambda: None)
    monkeypatch.setattr(main_local, "loading_animation", lambda: lambda: None)
    monkeypatch.setattr(
        main_local,
        "create_workflow",
        lambda prompt: (_ for _ in ()).throw(LLMQuotaError("Insufficient quota on OpenAI API.")),
    )

    exit_code = main_local.main()

    assert exit_code == 1
    assert "Error: Insufficient quota on OpenAI API." in capsys.readouterr().out
