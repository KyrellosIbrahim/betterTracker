# Loads environment variables and exposes them as a typed settings object.
# All API keys, secrets, and external URLs are configured here.

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # Google OAuth credentials (used for Google Health API, formerly Fitbit)
    GOOGLE_CLIENT_ID: str = os.environ.get("CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.environ.get("CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI: str = os.environ.get("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback")

    # Google OAuth URLs
    GOOGLE_AUTH_URL: str = "https://accounts.google.com/o/oauth2/v2/auth"
    GOOGLE_TOKEN_URL: str = "https://oauth2.googleapis.com/token"

    # Google Health API
    GOOGLE_HEALTH_API_BASE: str = os.environ.get("GOOGLE_HEALTH_API_BASE", "https://health.googleapis.com")
    GOOGLE_HEALTH_SCOPES: str = " ".join([
        "https://www.googleapis.com/auth/googlehealth.health_metrics_and_measurements.readonly",
        "https://www.googleapis.com/auth/googlehealth.sleep.readonly",
        "https://www.googleapis.com/auth/googlehealth.activity_and_fitness.readonly",
    ])

    # Steam API credentials
    STEAM_API_KEY: str = os.environ.get("STEAM_API_KEY", "")
    STEAM_USER_ID: str = os.environ.get("STEAM_USER_ID", "")

    # Steam API URLs
    STEAM_PLAYER_SUMMARIES_BASE_URL: str = os.environ.get("STEAM_GET_PLAYER_SUMMARIES_URL", "")
    STEAM_RECENTLY_PLAYED_GAMES_BASE_URL: str = os.environ.get("STEAM_GET_RECENTLY_PLAYED_GAMES_URL", "")

    # Steam API URLs (constructed from key + user ID)
    @property
    def STEAM_GET_PLAYER_SUMMARIES_URL(self) -> str:
        return f"{self.STEAM_PLAYER_SUMMARIES_BASE_URL}?key={self.STEAM_API_KEY}&steamids={self.STEAM_USER_ID}"

    @property
    def STEAM_GET_RECENTLY_PLAYED_GAMES_URL(self) -> str:
        return f"{self.STEAM_RECENTLY_PLAYED_GAMES_BASE_URL}?key={self.STEAM_API_KEY}&steamid={self.STEAM_USER_ID}"

    @staticmethod
    def STEAM_GET_GAME_DETAILS_URL(app_id: int) -> str:
        return f"https://store.steampowered.com/api/appdetails?appids={app_id}"

    # Database
    DATABASE_URL: str = os.environ.get("DATABASE_URL", "sqlite:///./bettertracker.db")

    # Polling interval for Steam currently-playing check (seconds)
    STEAM_POLL_INTERVAL: int = int(os.environ.get("STEAM_POLL_INTERVAL", "30"))


settings = Settings()
