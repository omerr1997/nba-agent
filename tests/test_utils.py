"""Unit tests for utils.py helper functions."""

import json
import pytest
from utils import tool_error, format_json


class TestToolError:
    def test_returns_string(self):
        result = tool_error("something went wrong")
        assert isinstance(result, str)

    def test_message_is_included(self):
        msg = "invalid player ID"
        result = tool_error(msg)
        assert msg in result

    def test_error_prefix_included(self):
        result = tool_error("test")
        assert "mistake" in result.lower() or "fix" in result.lower()


class TestFormatJson:
    def test_returns_valid_json_string(self):
        data = {"key": "value", "number": 42}
        result = format_json(data)
        parsed = json.loads(result)
        assert parsed == data

    def test_is_indented(self):
        result = format_json({"a": 1})
        assert "\n" in result  # indented output has newlines

    def test_handles_nested_dict(self):
        data = {"player": {"name": "LeBron", "id": 2544}}
        result = format_json(data)
        parsed = json.loads(result)
        assert parsed["player"]["id"] == 2544

    def test_handles_empty_dict(self):
        result = format_json({})
        assert result == "{}"
