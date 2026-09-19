// Thin fetch client for the BetterTracker backend.
// One function per endpoint; all return parsed JSON typed to api/types.ts.

import type {
  ActiveSession,
  AuthStatus,
  BreathingRateResponse,
  CompetitiveInsight,
  CurrentlyPlaying,
  GameDetails,
  GameSession,
  GenreInsight,
  GenreSleepImpact,
  HealthSnapshot,
  HeartRateResponse,
  LateNightImpact,
  RecentlyPlayedGame,
  SleepImpactCompetitive,
  SleepResponse,
  WindDownImpact,
  PlaytimeImpact,
  ActivityInteraction,
  WeeklyPlaytimePoint,
} from './types'

const BASE_URL = 'http://localhost:8000'

// Visiting this URL starts the Google OAuth flow (redirect, not fetch).
export const GOOGLE_LOGIN_URL = `${BASE_URL}/auth/google/login`

async function get<T>(path: string): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`)
  if (!response.ok) throw new Error(`${path} failed: ${response.status}`)
  return response.json()
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!response.ok) throw new Error(`${path} failed: ${response.status}`)
  return response.json()
}

// --- Auth ---

export const getAuthStatus = () => get<AuthStatus>('/auth/status')

// --- Health ---

export const getSleep = (date?: string) =>
  get<SleepResponse>(`/health/sleep${date ? `?target_date=${date}` : ''}`)

export const getHeartRate = (date?: string) =>
  get<HeartRateResponse>(`/health/heartrate${date ? `?target_date=${date}` : ''}`)

export const getBreathingRate = (date?: string) =>
  get<BreathingRateResponse>(`/health/breathing-rate${date ? `?target_date=${date}` : ''}`)

// Returns the stored day, refetching from Google only when it's stale.
// force=true bypasses that TTL — for an explicit "refresh now" action.
export const getSnapshot = (date?: string, force = false) => {
  const params = new URLSearchParams()
  if (date) params.set('target_date', date)
  if (force) params.set('force', 'true')
  const query = params.toString()
  return get<HealthSnapshot>(`/health/snapshot${query ? `?${query}` : ''}`)
}

// Reads stored snapshots (no external calls). Oldest first — feed to trend charts.
export const getSnapshotHistory = (days = 30) =>
  get<HealthSnapshot[]>(`/health/snapshots?days=${days}`)

// --- Steam ---

export const getCurrentlyPlaying = () => get<CurrentlyPlaying>('/steam/currently-playing')

export const getRecentlyPlayed = () =>
  get<{ total_count: number; games: RecentlyPlayedGame[] }>('/steam/recently-played')

export const getGames = () => get<GameDetails[]>('/steam/games')

// Add or update a game's metadata (genre + competitive flag). The backend also
// backfills existing sessions of this game, so insights update retroactively.
export const upsertGame = (game: {
  app_id: number
  game_name: string
  genre?: string | null
  is_competitive: boolean
}) => post<GameDetails>('/steam/games', game)

// --- Sessions ---

export const getSessions = (date?: string, limit = 50) =>
  get<GameSession[]>(`/sessions/?limit=${limit}${date ? `&target_date=${date}` : ''}`)

export const getActiveSession = () => get<ActiveSession | null>('/sessions/active')

// --- Insights ---

export const getInsightsByGenre = () => get<GenreInsight[]>('/insights/by-genre')

export const getInsightsByCompetitive = () =>
  get<CompetitiveInsight[]>('/insights/by-competitive')

// Next-morning sleep score after each genre, best first.
export const getSleepImpactByGenre = () => get<GenreSleepImpact[]>('/insights/sleep-impact')

// Sleep bucketed by how long before bed the last session ended.
export const getWindDownImpact = () => get<WindDownImpact>('/insights/wind-down')

// Sleep after late-night gaming vs earlier gaming vs none.
export const getLateNightImpact = () => get<LateNightImpact>('/insights/late-night')

export const getSleepImpactCompetitive = () =>
  get<SleepImpactCompetitive>('/insights/sleep-impact-competitive')

// Recovery bucketed by how much was played that day (<1h / 1–3h / 3h+).
export const getPlaytimeImpact = () => get<PlaytimeImpact>('/insights/playtime')

// Recovery on gaming days that were also physically active vs sedentary vs none.
export const getActivityInteraction = () =>
  get<ActivityInteraction>('/insights/activity-interaction')

// Per-week total gaming minutes vs average next-morning sleep score.
export const getWeeklyPlaytime = () => get<WeeklyPlaytimePoint[]>('/insights/weekly')
