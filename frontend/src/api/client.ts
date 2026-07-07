// Thin fetch client for the BetterTracker backend.
// One function per endpoint; all return parsed JSON typed to api/types.ts.

import type {
  ActiveSession,
  BreathingRateResponse,
  CompetitiveInsight,
  CurrentlyPlaying,
  GameDetails,
  GameSession,
  GenreInsight,
  HealthSnapshot,
  HeartRateResponse,
  RecentlyPlayedGame,
  SleepImpactCompetitive,
  SleepResponse,
} from './types'

const BASE_URL = 'http://localhost:8000'

// Visiting this URL starts the Google OAuth flow (redirect, not fetch).
export const GOOGLE_LOGIN_URL = `${BASE_URL}/auth/google/login`

async function get<T>(path: string): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`)
  if (!response.ok) throw new Error(`${path} failed: ${response.status}`)
  return response.json()
}

// --- Health ---

export const getSleep = (date?: string) =>
  get<SleepResponse>(`/health/sleep${date ? `?target_date=${date}` : ''}`)

export const getHeartRate = (date?: string) =>
  get<HeartRateResponse>(`/health/heartrate${date ? `?target_date=${date}` : ''}`)

export const getBreathingRate = (date?: string) =>
  get<BreathingRateResponse>(`/health/breathing-rate${date ? `?target_date=${date}` : ''}`)

// Fetches from Google Health AND persists the day to the DB.
export const getSnapshot = (date?: string) =>
  get<HealthSnapshot>(`/health/snapshot${date ? `?target_date=${date}` : ''}`)

// Reads stored snapshots (no external calls). Oldest first — feed to trend charts.
export const getSnapshotHistory = (days = 30) =>
  get<HealthSnapshot[]>(`/health/snapshots?days=${days}`)

// --- Steam ---

export const getCurrentlyPlaying = () => get<CurrentlyPlaying>('/steam/currently-playing')

export const getRecentlyPlayed = () =>
  get<{ total_count: number; games: RecentlyPlayedGame[] }>('/steam/recently-played')

export const getGames = () => get<GameDetails[]>('/steam/games')

// --- Sessions ---

export const getSessions = (date?: string, limit = 50) =>
  get<GameSession[]>(`/sessions/?limit=${limit}${date ? `&target_date=${date}` : ''}`)

export const getActiveSession = () => get<ActiveSession | null>('/sessions/active')

// --- Insights ---

export const getInsightsByGenre = () => get<GenreInsight[]>('/insights/by-genre')

export const getInsightsByCompetitive = () =>
  get<CompetitiveInsight[]>('/insights/by-competitive')

export const getSleepImpactCompetitive = () =>
  get<SleepImpactCompetitive>('/insights/sleep-impact-competitive')
