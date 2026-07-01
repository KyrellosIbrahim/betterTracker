# FastAPI application entrypoint.
# Registers all controller routers, sets up CORS, and creates DB tables on startup.

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from controllers.steam_controller import router as steam_router
from controllers.fitbit_controller import router as fitbit_router
from controllers.session_controller import router as session_router
from controllers.insights_controller import router as insights_router

# Create all DB tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="BetterTracker API",
    description="Personal dashboard correlating Fitbit health data with Steam gaming sessions."
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
