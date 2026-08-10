// TypeScript mirrors of the backend Pydantic schemas.
// Keep in sync with backend/schemas/*.py.

// --- Auth ---
export interface AuthStatus {
  connected: boolean
  has_refresh_token: boolean
  updated_at: string | null
  needs_reauth: boolean
  last_error: string | null
  last_success_at: string | null
}

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

// NOTE: every insight below joins a gaming session to the FOLLOWING morning's
// health snapshot, and treats a gaming day as 4am–4am. So `avg_sleep_score`
// means "sleep the morning after playing", and `recovery_days` counts distinct
// mornings (not sessions) behind the averages.

interface InsightMetrics {
  session_count: number
  recovery_days: number
  avg_session_minutes: number | null
  avg_resting_hr: number | null
  // Min/max alongside the mean — overlapping ranges reveal a "difference"
  // between two averages as noise.
  resting_hr_min: number | null
  resting_hr_max: number | null
  avg_sleep_score: number | null
  sleep_score_min: number | null
  sleep_score_max: number | null
  avg_sleep_duration_minutes: number | null
  avg_breathing_rate: number | null
}

export interface GenreInsight extends InsightMetrics {
  genre: string
}

export interface CompetitiveInsight extends InsightMetrics {
  is_competitive: boolean
}

export interface GenreSleepImpact {
  genre: string
  avg_sleep_score: number | null
  sample_days: number
}

// Shared shape for every bucket-of-recovery-mornings insight.
export interface SleepImpactBucket {
  avg_sleep_score: number | null
  sleep_score_min: number | null
  sleep_score_max: number | null
  avg_sleep_duration_minutes: number | null
  avg_resting_hr: number | null
  sample_days: number
}

export interface SleepImpactCompetitive {
  competitive_days: SleepImpactBucket
  casual_only_days: SleepImpactBucket
  no_gaming_days: SleepImpactBucket
}

// How long before bed the last session ended.
export interface WindDownBucket extends SleepImpactBucket {
  avg_gap_minutes: number | null
}

export interface WindDownImpact {
  under_30min: WindDownBucket
  '30_to_90min': WindDownBucket
  over_90min: WindDownBucket
}

// Gaming past LATE_NIGHT_HOUR (measured on the gaming day, so a 1am finish
// counts as late) vs earlier gaming vs none.
export interface LateNightImpact {
  late_night_gaming: SleepImpactBucket
  earlier_gaming: SleepImpactBucket
  no_gaming: SleepImpactBucket
}
