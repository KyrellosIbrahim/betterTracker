// TypeScript mirrors of the backend Pydantic schemas.
// Keep in sync with backend/schemas/*.py.

// --- Health (backend/schemas/fitbit.py) ---

export interface SleepScoreComponents {
  duration: number
  quality: number
  restoration: number
}

export interface SleepResponse {
  date: string
  duration_minutes: number | null
  deep_minutes: number | null
  light_minutes: number | null
  rem_minutes: number | null
  awake_minutes: number | null
  sleep_score: number | null
  rating: string | null
  components: SleepScoreComponents | null
}

export interface HeartRateResponse {
  date: string
  resting_heart_rate: number | null
}

export interface BreathingRateResponse {
  date: string
  breathing_rate: number | null
}

export interface HealthSnapshot {
  date: string
  resting_heart_rate: number | null
  sleep_score: number | null
  sleep_duration_minutes: number | null
  deep_minutes: number | null
  light_minutes: number | null
  rem_minutes: number | null
  awake_minutes: number | null
  breathing_rate: number | null
}

// --- Steam (backend/schemas/steam.py) ---

export interface CurrentlyPlaying {
  is_playing: boolean
  game_id: number | null
  game_name: string | null
  genre: string | null
  is_competitive: boolean | null
}

export interface RecentlyPlayedGame {
  app_id: number
  name: string
  playtime_2weeks: number
  playtime_forever: number
  genre: string | null
  is_competitive: boolean | null
}

export interface GameDetails {
  app_id: number
  name: string
  genre: string | null
  is_competitive: boolean
}

// --- Sessions (backend/schemas/session.py) ---

export interface GameSession {
  id: number
  game_id: number
  game_name: string
  genre: string | null
  start_time: string
  end_time: string | null
  duration_minutes: number | null
}

export interface ActiveSession {
  game_id: number
  game_name: string
  genre: string | null
  start_time: string
  elapsed_minutes: number
}

// --- Insights (backend/services/insights_service.py) ---

export interface GenreInsight {
  genre: string
  session_count: number
  avg_session_minutes: number | null
  avg_resting_hr: number | null
  avg_sleep_score: number | null
  avg_breathing_rate: number | null
}

export interface CompetitiveInsight {
  is_competitive: boolean
  session_count: number
  avg_session_minutes: number | null
  avg_resting_hr: number | null
  avg_sleep_score: number | null
  avg_breathing_rate: number | null
}

export interface SleepImpactBucket {
  avg_sleep_score: number | null
  sample_days: number
}

export interface SleepImpactCompetitive {
  competitive_days: SleepImpactBucket
  casual_only_days: SleepImpactBucket
  no_gaming_days: SleepImpactBucket
}
