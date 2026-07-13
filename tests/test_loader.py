import json

import pytest

from elvex.utils import loader


def test_parse_json_accepts_plain_json():
    assert loader.parse_json('{"task_desc": "demo"}') == {"task_desc": "demo"}


def test_parse_json_accepts_fenced_json():
    assert loader.parse_json('```json\n{"task_desc": "demo"}\n```') == {"task_desc": "demo"}


def test_parse_json_extracts_first_json_payload_from_text():
    assert loader.parse_json('Here is the result:\n{"task_desc": "demo"}\nThanks') == {
        "task_desc": "demo"
    }


def test_parse_json_raises_helpful_error_for_empty_response():
    with pytest.raises(ValueError, match="empty response"):
        loader.parse_json("   ")


def test_save_output_json_uses_safe_task_directory(tmp_path, monkeypatch):
    monkeypatch.setattr(loader, "load_project_root_path", lambda: str(tmp_path))

    payload = {"task_desc": "demo_task", "answer": "ok"}
    with loader.workflow_output_context("run_20260709_120000_deadbeef") as output_dir:
        returned = loader.save_output_json(payload, "divider")

    assert returned == payload
    expected_output_dir = tmp_path / "outputs" / "runs" / "run_20260709_120000_deadbeef"
    assert output_dir == str(expected_output_dir)
    assert json.loads((expected_output_dir / "divider_output.json").read_text()) == payload


def test_save_output_json_rejects_unsafe_identifiers(tmp_path, monkeypatch):
    monkeypatch.setattr(loader, "load_project_root_path", lambda: str(tmp_path))

    with pytest.raises(ValueError, match="Invalid task_desc"):
        loader.save_output_json({"task_desc": "../escape"}, "divider")


def test_save_output_json_orchestrator_rejects_empty_plan(tmp_path, monkeypatch):
    monkeypatch.setattr(loader, "load_project_root_path", lambda: str(tmp_path))

    with pytest.raises(IndexError):
        loader.save_output_json_orchestrator([])
