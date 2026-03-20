"""Unit tests for tools.py — NBA API tool functions.

All NBA API network calls are mocked so tests run offline.
"""

import json
import pytest
from unittest.mock import patch, MagicMock


class TestGetPlayerInfo:
    def test_returns_player_data_for_known_name(self):
        mock_player = [{"id": 2544, "full_name": "LeBron James", "is_active": True}]
        with patch("api.tools.players.find_players_by_full_name", return_value=mock_player):
            from api.tools import get_player_info
            result = get_player_info.invoke({"full_name": "LeBron James"})
            parsed = json.loads(result)
            assert len(parsed) == 1
            assert parsed[0]["id"] == 2544
            assert parsed[0]["full_name"] == "LeBron James"

    def test_returns_error_when_player_not_found(self):
        with patch("api.tools.players.find_players_by_full_name", return_value=[]):
            from api.tools import get_player_info
            result = get_player_info.invoke({"full_name": "Unknown Player XYZ"})
            assert "mistake" in result.lower() or "no player" in result.lower()

    def test_returns_all_players_when_name_is_empty(self):
        mock_all = [{"id": 1, "full_name": "Player A"}, {"id": 2, "full_name": "Player B"}]
        with patch("api.tools.players.get_players", return_value=mock_all):
            from api.tools import get_player_info
            result = get_player_info.invoke({"full_name": ""})
            parsed = json.loads(result)
            assert len(parsed) == 2


class TestGetTeamInfo:
    def test_returns_team_data_for_known_name(self):
        mock_team = [{"id": 1610612747, "full_name": "Los Angeles Lakers"}]
        with patch("api.tools.teams.find_teams_by_full_name", return_value=mock_team):
            from api.tools import get_team_info
            result = get_team_info.invoke({"team_name": "Los Angeles Lakers"})
            parsed = json.loads(result)
            assert parsed[0]["id"] == 1610612747

    def test_returns_error_when_team_not_found(self):
        with patch("api.tools.teams.find_teams_by_full_name", return_value=[]):
            from api.tools import get_team_info
            result = get_team_info.invoke({"team_name": "Fake Team XYZ"})
            assert "mistake" in result.lower() or "no team" in result.lower()

    def test_returns_all_teams_when_name_is_none(self):
        mock_all = [{"id": 1, "full_name": "Team A"}]
        with patch("api.tools.teams.get_teams", return_value=mock_all):
            from api.tools import get_team_info
            result = get_team_info.invoke({"team_name": None})
            parsed = json.loads(result)
            assert len(parsed) == 1


class TestGetPlayerCareerStats:
    def _make_mock_career(self, seasons: list[dict]):
        """Helper to build a mock PlayerCareerStats response."""
        import pandas as pd
        mock_df = pd.DataFrame(seasons)
        mock_career = MagicMock()
        mock_career.get_data_frames.return_value = [mock_df]
        return mock_career

    def test_returns_career_summary(self):
        seasons = [
            {"SEASON_ID": "2003-04", "GP": 79, "PTS": 1654, "AST": 465, "REB": 432},
            {"SEASON_ID": "2004-05", "GP": 80, "PTS": 2111, "AST": 577, "REB": 588},
        ]
        mock_career = self._make_mock_career(seasons)
        with patch("api.tools.playercareerstats.PlayerCareerStats", return_value=mock_career):
            from api.tools import get_player_career_stats
            result = get_player_career_stats.invoke({"player_id": 2544})
            parsed = json.loads(result)
            assert parsed["total_seasons"] == 2
            assert parsed["total_games"] == 159
            assert parsed["career_total_points"] == 3765

    def test_returns_error_for_empty_stats(self):
        import pandas as pd
        mock_career = MagicMock()
        mock_career.get_data_frames.return_value = [pd.DataFrame()]
        with patch("api.tools.playercareerstats.PlayerCareerStats", return_value=mock_career):
            from api.tools import get_player_career_stats
            result = get_player_career_stats.invoke({"player_id": 99999999})
            assert "mistake" in result.lower() or "no career" in result.lower()
