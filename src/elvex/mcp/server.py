# mcp --> tools. Prompts too??
# mcp inspector for debugging

from __future__ import annotations

import asyncio
import json
import logging
import ast
import os
import re
import socket
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from simpleeval import SimpleEval
import math
import httpx

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("elvex-mcp-server")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("elvex-mcp-logger")

# -----------------------------
# 1. Calculator tool
# -----------------------------

# for accessing securely
s_eval = SimpleEval(functions={
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "log": math.log,
    "exp": math.exp,
    "pow": math.pow,
}, names={"pi": math.pi, "e": math.e})

@mcp.tool(
    name="calculate", 
    description="Scientific calculator. Supports: +, -, *, /, **, sqrt(), sin(), cos(), log(), etc. Constants: pi, e."
)
async def calculate(expression: str) -> str:
    """
    Evaluates scientific mathematical expressions safely.
    """
    logger.info(f"Tool Accessed: 'calculate' with expression: {expression}")
    
    try:
        result = s_eval.eval(expression)
        return str(result)
    except Exception as e:
        logger.error(f"Calculation failed: {str(e)}")
        return f"Error: Invalid scientific expression. {str(e)}"


# -----------------------------
# 2. Exchange rate tool
# -----------------------------

@mcp.tool(
    name="get_exchange_rate", 
    description="Get real-time currency exchange rates. Example: from_currency='USD', to_currency='EUR'."
)
async def get_exchange_rate(from_currency: str, to_currency: str) -> str:
    """
    Fetch current exchange rate between two currencies using an external API.
    """
    logger.info(f"Tool Accessed: 'get_exchange_rate' from {from_currency} to {to_currency}")
    
    url = f"https://api.exchangerate-api.com/v4/latest/{from_currency.upper()}"
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            
            # 200 OK ?
            response.raise_for_status()
            
            data = response.json()
            rates = data.get("rates", {})
            rate = rates.get(to_currency.upper())
            
            if rate:
                logger.info(f"Exchange rate found: {rate}")
                return f"1 {from_currency.upper()} = {rate} {to_currency.upper()}"
            else:
                logger.warning(f"Currency {to_currency} not found in rates.")
                return f"Error: Currency '{to_currency}' not found."
                
    except httpx.HTTPStatusError as e:
        logger.error(f"API Error: {e.response.status_code} for {from_currency}")
        return f"Error: Unable to fetch rates for {from_currency}. Please check the currency code."
    except Exception as e:
        logger.error(f"Unexpected error in get_exchange_rate: {str(e)}")
        return "Error: An unexpected error occurred while fetching exchange rates."

if __name__ == "__main__":
    # better to use mcp inspector for visualizing the tools without wasting any api token
    mcp.run(transport="stdio")