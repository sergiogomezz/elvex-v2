from __future__ import annotations

import os
from typing import Any, Dict, Optional


class LangfuseObserver:
    """Best-effort Langfuse observer with graceful no-op fallback."""

    def __init__(self) -> None:
        self._enabled = False
        self._client = None

        public_key = _clean_env("LANGFUSE_PUBLIC_KEY")
        secret_key = _clean_env("LANGFUSE_SECRET_KEY")
        base_url = _clean_env("LANGFUSE_BASE_URL")

        if not public_key or not secret_key:
            return

        try:
            from langfuse import Langfuse  # type: ignore

            kwargs: Dict[str, Any] = {
                "public_key": public_key,
                "secret_key": secret_key,
            }
            if base_url:
                kwargs["host"] = base_url
            self._client = Langfuse(**kwargs)
            self._enabled = True
        except Exception:
            self._enabled = False
            self._client = None

    @property
    def enabled(self) -> bool:
        return self._enabled and self._client is not None

    def start_trace(
        self,
        *,
        name: str,
        input_payload: Optional[Any] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Any:
        if not self.enabled:
            return None
        try:
            return self._client.start_observation(
                name=name,
                as_type="span",
                input=input_payload,
                metadata=metadata,
            )
        except Exception:
            return None

    def start_span(
        self,
        *,
        parent: Any,
        name: str,
        input_payload: Optional[Any] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Any:
        if not self.enabled:
            return None
        try:
            if parent is not None and hasattr(parent, "start_observation"):
                return parent.start_observation(
                    name=name,
                    as_type="span",
                    input=input_payload,
                    metadata=metadata,
                )
            if hasattr(self._client, "start_observation"):
                return self._client.start_observation(
                    name=name,
                    as_type="span",
                    input=input_payload,
                    metadata=metadata,
                )
        except Exception:
            return None
        return None

    def start_generation(
        self,
        *,
        parent: Any,
        name: str,
        model: str,
        input_payload: Optional[Any] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Any:
        if not self.enabled:
            return None

        kwargs: Dict[str, Any] = {
            "name": name,
            "as_type": "generation",
            "model": model,
            "input": input_payload,
            "metadata": metadata,
        }

        try:
            if parent is not None and hasattr(parent, "start_observation"):
                return parent.start_observation(**kwargs)
            if hasattr(self._client, "start_observation"):
                return self._client.start_observation(**kwargs)
        except Exception:
            return None
        return None

    def end(
        self,
        obs: Any,
        *,
        output: Optional[Any] = None,
        metadata: Optional[Dict[str, Any]] = None,
        level: Optional[str] = None,
        status_message: Optional[str] = None,
        usage: Optional[Dict[str, Any]] = None,
    ) -> None:
        if not self.enabled or obs is None:
            return

        kwargs: Dict[str, Any] = {}
        if output is not None:
            kwargs["output"] = output
        if metadata:
            kwargs["metadata"] = metadata
        if level:
            kwargs["level"] = level
        if status_message:
            kwargs["status_message"] = status_message

        if usage:
            kwargs["usage_details"] = usage

        try:
            if kwargs and hasattr(obs, "update"):
                obs.update(**kwargs)
            obs.end()
        except Exception:
            return

    def flush(self) -> None:
        if not self.enabled:
            return
        try:
            self._client.flush()
        except Exception:
            return


def _clean_env(key: str) -> Optional[str]:
    raw = os.getenv(key)
    if raw is None:
        return None
    value = raw.strip().strip('"').strip("'")
    return value or None


_OBSERVER: Optional[LangfuseObserver] = None


def get_observer() -> LangfuseObserver:
    global _OBSERVER
    if _OBSERVER is None:
        _OBSERVER = LangfuseObserver()
    return _OBSERVER
