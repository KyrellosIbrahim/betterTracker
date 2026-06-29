# BetterTracker

A personal dashboard that pulls data from the Fitbit and Steam APIs to track health metrics and gaming activity in one place.

## Tech Stack

- **Frontend:** React + TypeScript (Vite)
- **Backend:** Python FastAPI
- **APIs:** Fitbit Web API, Steam Web API

## Project Structure

```
betterTracker/
├── frontend/    # React + Vite app
├── backend/     # FastAPI server
```

## Setup

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Environment Variables

Create a `backend/.env` file with:

```
FITBIT_CLIENT_ID=
FITBIT_CLIENT_SECRET=
STEAM_API_KEY=
STEAM_USER_ID=
```

## Features (Planned)

- Fitbit health/activity data visualization
- Real-time Steam game tracking (currently playing)
- Unified personal stats dashboard
