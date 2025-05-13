# modules/action.py

from typing import Dict, Any, Union
from pydantic import BaseModel
import ast

# Optional logging fallback
try:
    from agent import log
except ImportError:
    import datetime
    def log(stage: str, msg: str):
        now = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"[{now}] [{stage}] {msg}")


class ToolCallResult(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]
    result: Union[str, list, dict]
    raw_response: Any


def parse_function_call(response: str) -> tuple[str, Dict[str, Any]]:
    """
    Parses a FUNCTION_CALL string like:
    "FUNCTION_CALL: add|a=5|b=7"
    Into a tool name and a dictionary of arguments.
    """
    try:
        if not response.startswith("FUNCTION_CALL:"):
            raise ValueError("Invalid function call format.")
        
        _, raw = response.split(":", 1)
        if "write_data_to_sheet" in response:
            index = raw.index("|")
            parts = []
            parts.append(raw[:index].strip())
            parts.append(raw[index+1:].strip())

        else:
            parts = [p.strip() for p in raw.split("|")]
        tool_name, param_parts = parts[0], parts[1:]

        args = {}
        print(f"param_parts: {param_parts}")
        for part in param_parts:
            if "=" not in part:
                raise ValueError(f"Invalid parameter: {part}")
            key, val = part.split("=", 1)
            print(f"key: {key} val:{val}")
            # Try parsing as literal, fallback to string
            try:
                parsed_val = ast.literal_eval(val)
            except Exception:
                parsed_val = val.strip()

            print(f"parsed_val: {parsed_val}")

            # Support nested keys (e.g., input.value)
            keys = key.split(".")
            current = args
            for k in keys[:-1]:
                current = current.setdefault(k, {})
            current[keys[-1]] = parsed_val
            print(f"current: {current}")

        log("parser", f"Parsed: {tool_name} → {args}")
        return tool_name, args

    except Exception as e:
        log("parser", f"❌ Parse failed: {e}")
        raise
