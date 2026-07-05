from __future__ import annotations

from typing import Any, Callable, Dict, List, Tuple

from pydantic import ValidationError

from elvex.core.errors import MalformedAgentResponseError

JSON_REPAIR_MESSAGE = (
    "Your previous response was not valid JSON or did not match the required schema. "
    "Return only valid JSON matching the required schema. Do not include markdown fences or commentary."
)
DEFAULT_JSON_MAX_RETRIES = 1


def call_json_agent_with_retry(
    *,
    client: Any,
    messages: List[Dict[str, Any]],
    parse_and_validate: Callable[[str], Any],
    error_context: str,
    chat_kwargs: Dict[str, Any],
    observation_metadata: Dict[str, Any],
    max_retries: int = DEFAULT_JSON_MAX_RETRIES,
) -> Tuple[Any, str]:
    last_error: Exception | None = None

    for retry_number in range(max_retries + 1):
        attempt_messages = messages
        if retry_number > 0:
            attempt_messages = [
                *messages,
                {
                    "role": "user",
                    "content": JSON_REPAIR_MESSAGE,
                },
            ]

        response = client.chat(
            messages=attempt_messages,
            **chat_kwargs,
            observation_metadata={
                **observation_metadata,
                "retry_number": retry_number,
                "max_retries": max_retries,
                "is_retry": retry_number > 0,
                "retry_reason": str(last_error) if last_error else None,
            },
        )
        response_text = response.text if hasattr(response, "text") else response

        try:
            return parse_and_validate(response_text), response_text
        except (ValueError, TypeError, ValidationError) as exc:
            last_error = exc

    raise MalformedAgentResponseError(
        f"{error_context} returned malformed JSON after {max_retries + 1} attempts. "
        f"Last error: {last_error}"
    )
