# FastAPI application entrypoint.
# Registers all controller routers, sets up CORS, and creates DB tables on startup.

from contextlib import asynccontextmanager
from datetime import date, timedelta
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

# Strong references to background tasks. asyncio only holds a weak reference,
# so without this the tasks can be garbage-collected mid-flight.
_background_tasks: set[asyncio.Task] = set()


def _spawn(coro) -> None:
    """Start a background task and keep a reference to it until it finishes."""
    task = asyncio.create_task(coro)
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)


@asynccontextmanager
async def lifespan(app: FastAPI):
    _spawn(poll_currently_playing())
    _spawn(sync_health_snapshots())
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
            # requests is blocking — keep it off the event loop
            player = await asyncio.to_thread(steam_service.get_currently_playing)
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


async def sync_health_snapshots():
    """
    Keep a trailing window of health snapshots topped up.

    Runs on an interval rather than once a day so downtime or a restart can't
    skip a day: every tick re-fetches the last HEALTH_SYNC_WINDOW_DAYS days and
    upserts them, which also picks up data the watch synced late.
    """
    from database import SessionLocal
    from services import fitbit_service

    while True:
        await asyncio.sleep(settings.HEALTH_SYNC_INTERVAL)
        db = SessionLocal()
        try:
            # Covers both "never connected" and "grant is dead" — no point making
            # a dozen failing API calls every hour against a token we know is bad.
            status = fitbit_service.fetch_token_status(db)
            if not status["connected"]:
                print(f"Health sync skipped: {status['last_error'] or 'Google not connected'}")
                continue

            synced_any = False
            for offset in range(settings.HEALTH_SYNC_WINDOW_DAYS):
                target = date.today() - timedelta(days=offset)
                # build_snapshot_data makes blocking HTTP calls — run it in a thread
                data = await asyncio.to_thread(fitbit_service.build_snapshot_data, target)
                if any(value is not None for value in data.values()):
                    fitbit_service.save_health_snapshot(target, data, db)
                    synced_any = True

            if synced_any:
                fitbit_service.record_sync_success(db)
        except Exception as e:
            print(f"Health sync error: {e}")
        finally:
            db.close()



