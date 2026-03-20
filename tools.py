import prompts
from nba_api.stats.static import players, teams
from nba_api.stats.endpoints import playercareerstats, commonplayerinfo
from utils import nba_tool, tool_error, format_json
import json


@nba_tool(prompts.GET_PLAYER_INFO_DOC)
def get_player_info(full_name: str | None = None) -> str:
    try:
        if full_name == "":
            found_players = players.get_players()
        else:
            found_players = players.find_players_by_full_name(full_name)
        if not found_players:
            return tool_error(
                f"No player found with name '{full_name}'. Please check the spelling."
            )
        return json.dumps(found_players)
    except Exception as e:
        return tool_error(str(e))


@nba_tool(prompts.GET_TEAM_INFO_DOC)
def get_team_info(team_name: str | None = None) -> str:
    try:
        if team_name == "" or team_name is None:
            found_teams = teams.get_teams()
        else:
            found_teams = teams.find_teams_by_full_name(team_name)
        if not found_teams:
            return tool_error(
                f"No team found with name '{team_name}'. Please check the spelling."
            )
        return json.dumps(found_teams)
    except Exception as e:
        return tool_error(str(e))


@nba_tool(prompts.GET_PLAYER_CAREER_STATS_DOC)
def get_player_career_stats(player_id: int) -> str:
    try:
        career = playercareerstats.PlayerCareerStats(player_id=player_id)
        df = career.get_data_frames()[0]

        data = df.to_dict(orient="records")
        if not data:
            return tool_error(
                f"No career statistics found for player ID {player_id}. Please check the ID."
            )

        total_games = sum(row.get("GP", 0) for row in data)
        total_pts = sum(row.get("PTS", 0) for row in data)
        total_ast = sum(row.get("AST", 0) for row in data)
        total_reb = sum(row.get("REB", 0) for row in data)

        summary = {
            "total_seasons": len(data),
            "total_games": total_games,
            "career_total_points": total_pts,
            "career_total_assists": total_ast,
            "career_total_rebounds": total_reb,
            "last_season": data[-1] if data else {},
        }
        return format_json(summary)
    except Exception as e:
        return tool_error(str(e))


@nba_tool(prompts.THINK_TOOL_DOC)
def think(thought: str) -> str:
    """Record internal reasoning."""
    return f"Thought recorded: {thought}"


@nba_tool(prompts.WEB_SEARCH_DOC)
def web_search(query: str) -> str:
    """Search the web for fresh NBA information."""
    try:
        from tavily import TavilyClient
        from config import settings

        client = TavilyClient(api_key=settings.tavily_api_key)
        response = client.search(query=query, search_depth="advanced")

        # Format the results into a readable string
        results = response.get("results", [])
        if not results:
            return f"No search results found for '{query}'."

        summary = "Search Results:\n"
        for i, res in enumerate(results[:3], 1):
            summary += f"{i}. {res['title']}\n   Content: {res['content']}\n   URL: {res['url']}\n\n"

        return summary
    except Exception as e:
        return tool_error(str(e))
