# One-off script to seed the game cache from Steam's recently played list.
# Pulls genre from the Steam store API and guesses is_competitive from PvP
# categories — review the output and fix any flags via POST /steam/games
# (e.g. RuneScape bossing isn't competitive even if the store says PvP).
#
# Run from backend/: venv/bin/python seed_games.py

import requests
from config import settings
from database import SessionLocal
from services import steam_service

# Steam store categories that suggest a game is played competitively.
COMPETITIVE_CATEGORIES = {"PvP", "Online PvP", "Cross-Platform Multiplayer"}


def fetch_store_details(app_id: int) -> dict:
    """Fetch a game's store page details (genres, categories). Returns {} on failure."""
    try:
        response = requests.get(settings.STEAM_GET_GAME_DETAILS_URL(app_id), timeout=10)
        response.raise_for_status()
        entry = response.json().get(str(app_id), {})
        return entry.get("data", {}) if entry.get("success") else {}
    except (requests.RequestException, ValueError):
        return {}


def main():
    recent = steam_service.get_recently_played()
    games = recent.get("games", [])
    if not games:
        print("No recently played games returned by Steam.")
        return

    db = SessionLocal()
    try:
        for game in games:
            app_id = game["appid"]
            name = game["name"]

            existing = steam_service.get_game_metadata(app_id, db)
            if existing:
                print(f"skip     {name} (already cached: {existing.genre}, competitive={existing.is_competitive})")
                continue

            details = fetch_store_details(app_id)
            genres = [g["description"] for g in details.get("genres", [])]
            categories = {c["description"] for c in details.get("categories", [])}
            genre = genres[0] if genres else None
            is_competitive = bool(categories & COMPETITIVE_CATEGORIES)

            steam_service.upsert_game(app_id, name, genre, is_competitive, db)
            print(f"added    {name} (genre={genre}, competitive={is_competitive})")
    finally:
        db.close()

    print("\nDone. Review flags and adjust via POST /steam/games where the guess is wrong.")


if __name__ == "__main__":
    main()
