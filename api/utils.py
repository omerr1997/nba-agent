from langchain_core.tools import tool
import json


def nba_tool(docstring: str):
    """
    Custom decorator that wraps Langchain's @tool and
    dynamically populates the docstring from the provided string.
    """

    def decorator(func):
        func.__doc__ = docstring
        return tool(func)

    return decorator


def tool_error(msg: str) -> str:
    """
    Standardizes error messages for the agent to ensure
    it realizes when it has made a mistake and needs to fix its input.
    """
    return f"You have made a mistake, please fix: {msg}"


def format_json(data: dict) -> str:
    """
    Helper to consistently format JSON responses for tools.
    """
    return json.dumps(data, indent=2)
