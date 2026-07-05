import sys
from types import SimpleNamespace

from elvex.observability import langfuse_observer


class FakeObservation:
    def __init__(self):
        self.children = []
        self.updates = []
        self.ended = False

    def start_observation(self, **kwargs):
        child = FakeObservation()
        child.start_kwargs = kwargs
        self.children.append(child)
        return child

    def update(self, **kwargs):
        self.updates.append(kwargs)

    def end(self):
        self.ended = True


class FakeLangfuse:
    instances = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.root_observations = []
        self.flushed = False
        FakeLangfuse.instances.append(self)

    def start_observation(self, **kwargs):
        observation = FakeObservation()
        observation.start_kwargs = kwargs
        self.root_observations.append(observation)
        return observation

    def flush(self):
        self.flushed = True


def test_langfuse_observer_reads_dotenv_and_enables_client(tmp_path, monkeypatch):
    FakeLangfuse.instances = []
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_BASE_URL", raising=False)
    monkeypatch.setitem(sys.modules, "langfuse", SimpleNamespace(Langfuse=FakeLangfuse))
    (tmp_path / ".env").write_text(
        "\n".join(
            [
                "LANGFUSE_PUBLIC_KEY=pk-test",
                "LANGFUSE_SECRET_KEY=sk-test",
                "LANGFUSE_BASE_URL=https://example.langfuse.test",
            ]
        )
    )

    observer = langfuse_observer.LangfuseObserver()

    assert observer.enabled is True
    assert FakeLangfuse.instances[0].kwargs == {
        "public_key": "pk-test",
        "secret_key": "sk-test",
        "base_url": "https://example.langfuse.test",
    }


def test_langfuse_observer_stays_disabled_without_keys(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_BASE_URL", raising=False)

    observer = langfuse_observer.LangfuseObserver()

    assert observer.enabled is False
    assert observer.start_trace(name="workflow") is None


def test_langfuse_observer_creates_and_ends_observations(tmp_path, monkeypatch):
    FakeLangfuse.instances = []
    monkeypatch.chdir(tmp_path)
    monkeypatch.setitem(sys.modules, "langfuse", SimpleNamespace(Langfuse=FakeLangfuse))
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")
    monkeypatch.setenv("LANGFUSE_BASE_URL", "https://example.langfuse.test")

    observer = langfuse_observer.LangfuseObserver()
    trace = observer.start_trace(
        name="create_workflow",
        input_payload={"prompt": "demo"},
        metadata={"provider": "openai"},
    )
    generation = observer.start_generation(
        parent=trace,
        name="openai.chat",
        model="gpt-test",
        input_payload=[{"role": "user", "content": "demo"}],
        metadata={"agent": "specifier"},
    )
    observer.end(generation, output="ok", usage={"input": 1, "output": 2, "total": 3})
    observer.flush()

    assert trace.start_kwargs["as_type"] == "span"
    assert trace.start_kwargs["name"] == "create_workflow"
    assert generation.start_kwargs["as_type"] == "generation"
    assert generation.start_kwargs["model"] == "gpt-test"
    assert generation.updates == [
        {
            "output": "ok",
            "usage_details": {"input": 1, "output": 2, "total": 3},
        }
    ]
    assert generation.ended is True
    assert FakeLangfuse.instances[0].flushed is True
