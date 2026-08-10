// BetterTracker dashboard shell.
// Each section has one wired-up example; the TODOs are yours to fill in.
//
// Insight ideas to build out:
//   - Avg resting HR on competitive vs casual days (wired below as the example)
//   - Sleep score: competitive days vs casual-only vs no-gaming (getSleepImpactCompetitive)
//   - Sleep stage composition (deep/REM %) after gaming days vs rest days
//   - Late-night sessions (started after 11pm) vs next-day sleep score
//   - Session length vs next-day sleep score (scatter)
//   - Breathing rate by genre (getInsightsByGenre)
//   - Weekly total playtime vs weekly avg sleep score
//   - "Best/worst sleep this month" cards with what you played that day

import { useEffect, useState } from 'react'
import {
  GOOGLE_LOGIN_URL,
  getActiveSession,
  getAuthStatus,
  getInsightsByCompetitive,
  getLateNightImpact,
  getSnapshotHistory,
  getWindDownImpact,
} from './api/client'
import type {
  ActiveSession,
  AuthStatus,
  CompetitiveInsight,
  HealthSnapshot,
  LateNightImpact,
  SleepImpactBucket,
  WindDownImpact,
} from './api/types'
import { MetricRing } from './components/MetricRing'
import { TrendChart } from './components/TrendChart'
import { ComparisonCard } from './components/ComparisonCard'

// Derive the UI state once, so the booleans don't get scattered through JSX.
// 'unknown' covers the in-flight fetch — rendering nothing beats flashing the
// wrong state on every page load.
type AuthState = 'unknown' | 'connected' | 'reconnect' | 'disconnected'

function authState(status: AuthStatus | null): AuthState {
  if (!status) return 'unknown'
  if (status.connected) return 'connected'
  // needs_reauth means the grant died — looks like "not connected" to the user,
  // but it means data silently stopped updating, so it gets different wording.
  return status.needs_reauth ? 'reconnect' : 'disconnected'
}

function AuthIndicator({ status }: { status: AuthStatus | null }) {
  const state = authState(status)
  if (state === 'unknown') return null

  if (state === 'connected') {
    const synced = status?.last_success_at
    return (
      <span className="text-sm text-emerald-600 dark:text-emerald-400">
        Connected ✓
        {synced && (
          <span className="ml-2 text-zinc-500 dark:text-zinc-400">
            synced {new Date(synced).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })}
          </span>
        )}
        {/* Non-fatal failure (e.g. invalid_client) — reconnecting wouldn't fix it,
            so warn rather than prompting. */}
        {status?.last_error && (
          <span className="ml-2 text-amber-600 dark:text-amber-400" title={status.last_error}>
            ⚠
          </span>
        )}
      </span>
    )
  }

  return (
    <a href={GOOGLE_LOGIN_URL} className="text-sm text-violet-600 underline dark:text-violet-400">
      {state === 'reconnect' ? 'Reconnect Google Health' : 'Connect Google Health'}
    </a>
  )
}

// Minutes as clock time: 384 -> "6:24". Rounding to whole minutes before
// splitting avoids a "6:60" from something like 383.7.
function formatDuration(minutes: number): string {
  const total = Math.round(minutes)
  return `${Math.floor(total / 60)}:${String(total % 60).padStart(2, '0')}`
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="mt-8">
      <h2 className="mb-4 border-b border-zinc-200 pb-2 text-lg font-medium text-zinc-900 dark:border-zinc-700 dark:text-zinc-100">
        {title}
      </h2>
      {children}
    </section>
  )
}

function App() {
  const [history, setHistory] = useState<HealthSnapshot[]>([])
  const [competitive, setCompetitive] = useState<CompetitiveInsight[]>([])
  const [nowPlaying, setNowPlaying] = useState<ActiveSession | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [authStatus, setAuthStatus] = useState<AuthStatus | null>(null)
  const [windDown, setWindDown] = useState<WindDownImpact | null>(null)
  const [lateNight, setLateNight] = useState<LateNightImpact | null>(null)

  useEffect(() => {
    getSnapshotHistory(30).then(setHistory).catch(console.error)
    getInsightsByCompetitive().then(setCompetitive).catch(console.error)
    getActiveSession().then(setNowPlaying).catch(console.error)
    getWindDownImpact().then(setWindDown).catch(console.error)
    getLateNightImpact().then(setLateNight).catch(console.error)
    // have set error for this one, since this one affects the rendering of the auth indicator.
    getAuthStatus().then(setAuthStatus).catch((e) => setError(String(e)))
  }, [])

  // Every bucket insight has the same shape, so build its card row the same way.
  const bucketRow = (label: string, bucket: SleepImpactBucket | undefined) => ({
    label,
    value: bucket?.avg_sleep_score,
    sampleDays: bucket?.sample_days,
    spread: [bucket?.sleep_score_min ?? null, bucket?.sleep_score_max ?? null] as [number | null, number | null],
  })

  const competitiveRow = competitive.find((c) => c.is_competitive)
  const casualRow = competitive.find((c) => !c.is_competitive)
  const latest = history.at(-1) ?? null

  // Kept in minutes so the ring fills exactly; formatted for display only.
  const sleepMinutes = latest?.sleep_duration_minutes ?? null

  return (
    <main className="mx-auto max-w-4xl px-5 pt-6 pb-16">
      <header className="flex items-baseline justify-between">
        <h1 className="text-3xl font-semibold text-zinc-900 dark:text-zinc-100">BetterTracker</h1>
        <div className="flex items-center gap-4">
          {nowPlaying && (
            <span className="text-sm text-violet-600 dark:text-violet-400">▶ {nowPlaying.game_name}</span>
          )}
          <AuthIndicator status={authStatus} />
        </div>
      </header>

      {/* Only the auth-status fetch sets this, so name that specifically — the
          old "unreachable or not authed" wording claimed the backend was down
          whenever any single call failed. */}
      {error && (
        <p className="mt-2 text-sm text-rose-500">Couldn't reach the backend to check the Google Health connection: {error}</p>
      )}

      {/* --- Today's rings --- */}
      <Section title={`${latest?.date ?? 'Latest'}`}>
        <div className="flex flex-wrap gap-8">
          <MetricRing label="Sleep score" value={latest?.sleep_score} max={100} color="#7c5cff" />
          <MetricRing
            label="Sleep duration"
            value={sleepMinutes}
            max={480} /* 8h goal, in minutes */
            display={sleepMinutes != null ? formatDuration(sleepMinutes) : undefined}
            color="#4fc3f7"
          />
          {/* TODO: more rings — resting HR (inverted: lower is better?), deep sleep vs 90min goal, ... */}
          <MetricRing label="Resting HR" value={latest?.resting_heart_rate} max={100} unit=" bpm" color="#ff6b81" />
        </div>
      </Section>

      {/* --- Trends --- */}
      <Section title="Trends">
        <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
          <TrendChart
            title="Sleep score (30d)"
            points={history.map((s) => ({ label: s.date, value: s.sleep_score }))}
          />
          {/* TODO: resting HR trend, deep sleep trend, playtime-per-day bars overlaid on sleep... */}
        </div>
      </Section>

      {/* --- Insights --- */}
      <Section title="Insights">
        <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
          <ComparisonCard
            title="Avg resting HR: competitive vs casual days"
            emptyMessage="No sessions recorded yet — play something to start comparing."
            rows={[
              {
                label: 'Competitive',
                value: competitiveRow?.avg_resting_hr,
                unit: 'bpm',
                sampleDays: competitiveRow?.recovery_days,
                spread: [competitiveRow?.resting_hr_min ?? null, competitiveRow?.resting_hr_max ?? null],
              },
              {
                label: 'Casual',
                value: casualRow?.avg_resting_hr,
                unit: 'bpm',
                sampleDays: casualRow?.recovery_days,
                spread: [casualRow?.resting_hr_min ?? null, casualRow?.resting_hr_max ?? null],
              },
            ]}
          />
          <ComparisonCard
            title="Sleep score by wind-down gap (last session → bed)"
            emptyMessage="No sessions with a measurable wind-down gap yet."
            rows={[
              bucketRow('<30 min', windDown?.under_30min),
              bucketRow('30–90 min', windDown?.['30_to_90min']),
              bucketRow('90+ min', windDown?.over_90min),
            ]}
          />

          <ComparisonCard
            title="Sleep score: late-night gaming vs earlier"
            emptyMessage="No sessions recorded yet."
            rows={[
              bucketRow('Late night', lateNight?.late_night_gaming),
              bucketRow('Earlier', lateNight?.earlier_gaming),
              bucketRow('No gaming', lateNight?.no_gaming),
            ]}
          />

          {/* TODO: sleep impact card (getSleepImpactCompetitive), genre breakdown table, ... */}
        </div>
      </Section>
    </main>
  )
}

export default App
