"""E2E tests for the NBA Agent API using the return-direct test mode.

These tests hit the live backend at localhost:8000.
The session_id="-1" triggers test mode, bypassing the LLM and returning
raw tool output directly, so we can assert on structured data.

Run with:
    pytest tests/test_e2e.py -v

Requirements:
    - Backend must be running: `bash start.sh` or `python main.py`
"""

import json
import pytest
import requests

BASE_URL = "http://localhost:8000"
TEST_SESSION_ID = "-1"


def _chat(message: str) -> dict:
    """Helper to call the API in test mode."""
    response = requests.post(
        f"{BASE_URL}/api/chat",
        json={"message": message, "session_id": TEST_SESSION_ID},
        timeout=15,
    )
    response.raise_for_status()
    return response.json()


# ─── Health ────────────────────────────────────────────────────────────────────

class TestAPIHealth:
    def test_server_is_reachable(self):
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        assert response.status_code == 200

    def test_chat_endpoint_exists(self):
        """Missing message field should give 422, not 404."""
        response = requests.post(f"{BASE_URL}/api/chat", json={})
        assert response.status_code == 422


# ─── Player Info ───────────────────────────────────────────────────────────────

class TestGetPlayerInfoE2E:
    def test_lebron_james_returned(self):
        data = _chat("get_player_info:LeBron James")
        players = json.loads(data["response"])
        assert len(players) >= 1
        names = [p["full_name"] for p in players]
        assert any("LeBron" in n for n in names)

    def test_player_has_required_fields(self):
        data = _chat("get_player_info:Stephen Curry")
        players = json.loads(data["response"])
        player = players[0]
        for field in ("id", "full_name", "is_active"):
            assert field in player, f"Missing field: {field}"

    def test_unknown_player_returns_error(self):
        data = _chat("get_player_info:Nonexistent Player XYZ999")
        assert "mistake" in data["response"].lower() or "no player" in data["response"].lower()

    def test_empty_name_returns_all_players(self):
        data = _chat("get_player_info:")
        players = json.loads(data["response"])
        assert isinstance(players, list)
        assert len(players) > 100  # NBA has many players


# ─── Team Info ─────────────────────────────────────────────────────────────────

class TestGetTeamInfoE2E:
    def test_lakers_returned(self):
        data = _chat("get_team_info:Los Angeles Lakers")
        teams = json.loads(data["response"])
        assert len(teams) >= 1
        names = [t["full_name"] for t in teams]
        assert any("Lakers" in n for n in names)

    def test_team_has_required_fields(self):
        data = _chat("get_team_info:Golden State Warriors")
        teams = json.loads(data["response"])
        team = teams[0]
        for field in ("id", "full_name", "abbreviation"):
            assert field in team, f"Missing field: {field}"

    def test_unknown_team_returns_error(self):
        data = _chat("get_team_info:Fake Team XYZ999")
        assert "mistake" in data["response"].lower() or "no team" in data["response"].lower()

    def test_empty_name_returns_all_teams(self):
        data = _chat("get_team_info:")
        teams = json.loads(data["response"])
        assert isinstance(teams, list)
        assert len(teams) >= 30  # At least 30 NBA teams


# ─── Career Stats ──────────────────────────────────────────────────────────────

class TestGetPlayerCareerStatsE2E:
    LEBRON_ID = 2544

    def test_returns_career_summary_for_lebron(self):
        data = _chat(f"get_player_career_stats:{self.LEBRON_ID}")
        stats = json.loads(data["response"])
        assert "total_seasons" in stats
        assert "career_total_points" in stats
        assert "total_games" in stats

    def test_career_points_are_positive(self):
        data = _chat(f"get_player_career_stats:{self.LEBRON_ID}")
        stats = json.loads(data["response"])
        assert stats["career_total_points"] > 0

    def test_last_season_is_present(self):
        data = _chat(f"get_player_career_stats:{self.LEBRON_ID}")
        stats = json.loads(data["response"])
        assert "last_season" in stats
        assert isinstance(stats["last_season"], dict)
        assert len(stats["last_season"]) > 0

    def test_invalid_player_id_returns_error(self):
        data = _chat("get_player_career_stats:99999999")
        # Could be an error string or an empty stats object
        response = data["response"]
        # Either an API error message or a tool_error is acceptable
        is_error = "mistake" in response.lower() or "no career" in response.lower()
        is_empty_stats = '"total_seasons": 0' in response
        assert is_error or is_empty_stats


# ─── Test Mode Validation ──────────────────────────────────────────────────────

class TestTestModeValidation:
    def test_bad_format_returns_400(self):
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={"message": "no colon here", "session_id": TEST_SESSION_ID},
            timeout=5,
        )
        assert response.status_code == 400

    def test_unknown_tool_returns_400(self):
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={"message": "fake_tool:arg", "session_id": TEST_SESSION_ID},
            timeout=5,
        )
        assert response.status_code == 400
