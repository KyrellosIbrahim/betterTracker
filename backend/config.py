# Loads environment variables and exposes them as a typed settings object.
# All API keys, secrets, and external URLs are configured here.

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # Google / Fitbit OAuth credentials
    GOOGLE_CLIENT_ID: str = os.environ.get("CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.environ.get("CLIENT_SECRET", "")
    FITBIT_REDIRECT_URI: str = os.environ.get("FITBIT_REDIRECT_URI", "http://localhost:8000/auth/fitbit/callback")

    # Steam API credentials
    STEAM_API_KEY: str = os.environ.get("STEAM_API_KEY", "")
    STEAM_USER_ID: str = os.environ.get("STEAM_USER_ID", "")

    # Steam API URLs (constructed from key + user ID)
    @property
    def STEAM_GET_PLAYER_SUMMARIES_URL(self) -> str:
        return f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key={self.STEAM_API_KEY}&steamids={self.STEAM_USER_ID}"

    @property
    def STEAM_GET_RECENTLY_PLAYED_GAMES_URL(self) -> str:
        return f"https://api.steampowered.com/IPlayerService/GetRecentlyPlayedGames/v1/?key={self.STEAM_API_KEY}&steamid={self.STEAM_USER_ID}"

    @staticmethod
    def STEAM_GET_GAME_DETAILS_URL(app_id: int) -> str:
        return f"https://store.steampowered.com/api/appdetails?appid={app_id}"

    # Database
    DATABASE_URL: str = os.environ.get("DATABASE_URL", "sqlite:///./bettertracker.db")

    # Polling interval for Steam currently-playing check (seconds)
    STEAM_POLL_INTERVAL: int = int(os.environ.get("STEAM_POLL_INTERVAL", "30"))


settings = Settings()
