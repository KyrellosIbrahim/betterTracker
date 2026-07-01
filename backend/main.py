from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from datetime import datetime
import requests

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "ok"}

@app.get("/current_game")
def get_current_game():
    steam_url = settings.STEAM_URL
    current_timestamp = int(datetime.now().timestamp())
    response = requests.get(steam_url)

    if response.status_code == 200:
        return response.json()
    else:
        return {"error": "Failed to fetch current game"}
    
@app.get("/current_metrics")
def get_current_metrics():
    cid = settings.GOOGLE_CLIENT_ID
    csecret = settings.GOOGLE_CLIENT_SECRET

    