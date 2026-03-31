from __future__ import annotations

import re
from typing import Any, Dict, List

import httpx
from pydantic import BaseModel, ConfigDict, Field, field_validator
from simpleeval import SimpleEval
import math

MAX_CALC_EXPRESSION_LEN = 200
CALC_ALLOWED_CHARS = re.compile(r"^[0-9A-Za-z_+\-*/().,\s]*$")

_s_eval = SimpleEval(
    functions={
        "sqrt": math.sqrt,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "log": math.log,
        "exp": math.exp,
        "pow": math.pow,
    },
    names={"pi": math.pi, "e": math.e},
)


class CalculateToolInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expression: str = Field(min_length=1, max_length=MAX_CALC_EXPRESSION_LEN)

    @field_validator("expression")
    @classmethod
    def validate_expression(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Expression is empty.")
        if not CALC_ALLOWED_CHARS.fullmatch(value):
            raise ValueError("Expression contains unsupported characters.")
        if value.count("**") > 2 or re.search(r"\*\*\s*\d{4,}", value):
            raise ValueError("Exponentiation pattern too complex.")
        return value


class ExchangeRateToolInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    from_currency: str = Field(min_length=3, max_length=3)
    to_currency: str = Field(min_length=3, max_length=3)

    @field_validator("from_currency", "to_currency")
    @classmethod
    def validate_currency_code(cls, value: str) -> str:
        value = value.strip().upper()
        if not re.fullmatch(r"[A-Z]{3}", value):
            raise ValueError("Currency code must be exactly 3 letters (ISO style).")
        return value


def get_openai_tool_definitions() -> List[Dict[str, Any]]:
    return [
        {
            "type": "function",
            "name": "calculate",
            "description": "Scientific calculator for arithmetic and basic math functions.",
            "parameters": CalculateToolInput.model_json_schema(),
        },
        {
            "type": "function",
            "name": "get_exchange_rate",
            "description": "Get latest exchange rate between two currencies.",
            "parameters": ExchangeRateToolInput.model_json_schema(),
        },
    ]


def execute_local_tool(name: str, arguments: Dict[str, Any]) -> str:
    try:
        if name == "calculate":
            payload = CalculateToolInput.model_validate(arguments)
            result = _s_eval.eval(payload.expression)
            return str(result)

        if name == "get_exchange_rate":
            payload = ExchangeRateToolInput.model_validate(arguments)
            url = f"https://api.exchangerate-api.com/v4/latest/{payload.from_currency}"
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url)
                response.raise_for_status()
                data = response.json()
            rate = data.get("rates", {}).get(payload.to_currency)
            if rate is None:
                return f"Error: Currency '{payload.to_currency}' not found."
            return f"1 {payload.from_currency} = {rate} {payload.to_currency}"

        return f"Error: Unknown tool '{name}'."
    except Exception as e:
        return f"Error: {str(e)}"


OPENAI_LOCAL_TOOLS = get_openai_tool_definitions()
