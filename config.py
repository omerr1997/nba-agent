import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from datetime import datetime


class Settings(BaseSettings):
    openrouter_api_key: str
    tavily_api_key: str = ""
    openai_api_base: str = "https://openrouter.ai/api/v1"
    model_name: str = "openai/gpt-4o-mini"
    # Comma-separated list of allowed CORS origins.
    # Set to your frontend URL in production (e.g. "https://yourapp.com").
    # Defaults to "*" (allow all) for local development.
    cors_origins: str = "*"

    # Tool descriptions for the system prompt
    tools_list: str = (
        "1. think: Use this to reason about the problem. 2. get_player_info: Get basic player info. 3. get_team_info: Get basic team info. 4. get_player_career_stats: Get career stats by player ID. 5. web_search: Search the web for fresh NBA info."
    )
    current_date: str = datetime.now().strftime("%B %d, %Y")

    # Follow-up parsing constants
    FOLLOW_UP_INDICATOR: str = "FOLLOW_UP:"
    FOLLOW_UP_SEP: str = "|"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    def setup_environment(self):
        """Configure external API environments."""
        os.environ["OPENAI_API_BASE"] = self.openai_api_base
        os.environ["OPENAI_API_KEY"] = self.openrouter_api_key


settings = Settings()
settings.setup_environment()
