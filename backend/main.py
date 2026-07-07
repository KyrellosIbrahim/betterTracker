# FastAPI application entrypoint.
# Registers all controller routers, sets up CORS, and creates DB tables on startup.

from contextlib import asynccontextmanager
from fastapi import FastAPI
import asyncio
from config import settings
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from controllers.steam_controller import router as steam_router
from controllers.fitbit_controller import router as fitbit_router
from controllers.session_controller import router as session_router
from controllers.insights_controller import router as insights_router

# Create all DB tables on startup
Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(poll_currently_playing())
    yield


app = FastAPI(
    title="BetterTracker API",
    description="Personal dashboard correlating Fitbit health data with Steam gaming sessions.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register route controllers
app.include_router(steam_router)
app.include_router(fitbit_router)
app.include_router(session_router)
app.include_router(insights_router)


@app.get("/")
def root():
    return {"status": "ok"}

async def poll_currently_playing():
    """Poll Steam every N seconds to track game sessions."""
    from database import SessionLocal
    from services import steam_service

    while True:
        await asyncio.sleep(settings.STEAM_POLL_INTERVAL)
        db = SessionLocal()
        try:
            player = steam_service.get_currently_playing()
            game_id = player.get("gameid")
            active_session = steam_service.get_active_session(db)

            if game_id:
                game_id = int(game_id)
                game_name = player.get("gameextrainfo", "Unknown")

                if active_session and active_session.game_id == game_id:
                    # Still playing the same game — do nothing
                    pass
                else:
                    # Switched games or started a new one
                    if active_session:
                        steam_service.close_session(active_session, db)
                    metadata = steam_service.get_game_metadata(game_id, db)
                    genre = metadata.genre if metadata else None
                    is_competitive = metadata.is_competitive if metadata else False
                    steam_service.open_session(game_id, game_name, genre, is_competitive, db)
                    competitive = ", competitive" if is_competitive else ""
                    print(f"Session started: {game_name} ({genre}{competitive})")
            else:
                # Not playing — close any active session
                if active_session:
                    steam_service.close_session(active_session, db)
                    print(f"Session ended: {active_session.game_name}")
        except Exception as e:
            print(f"Polling error: {e}")
        finally:
            db.close()



