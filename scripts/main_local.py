from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
# Ensure both "src" namespace imports and direct "elvex" imports work.
for path in (ROOT, SRC):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from elvex.core.workflow import create_workflow
from elvex.utils.utils import landing_intro, loading_animation
   

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run local agent workflow.")
    parser.add_argument(
        "--prompt",
        help="User prompt to send to the task specifier.",
    )
    return parser


def main() -> int:
    landing_intro()

    parser = _build_parser()
    args = parser.parse_args()

    user_prompt = args.prompt or input("What do you want to do?: ").strip()
    if not user_prompt:
        print("No prompt provided.")
        return 1
    
    stop_loading = loading_animation()
    try:
        result = create_workflow(user_prompt)
    finally:
        stop_loading()
        print()

    print(result)


if __name__ == "__main__":
    main()
