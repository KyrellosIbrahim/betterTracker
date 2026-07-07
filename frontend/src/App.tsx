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
  getInsightsByCompetitive,
  getSnapshot,
  getSnapshotHistory,
} from './api/client'
import type { ActiveSession, CompetitiveInsight, HealthSnapshot } from './api/types'
import { MetricRing } from './components/MetricRing'
import { TrendChart } from './components/TrendChart'
import { ComparisonCard } from './components/ComparisonCard'

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
  const [today, setToday] = useState<HealthSnapshot | null>(null)
  const [history, setHistory] = useState<HealthSnapshot[]>([])
  const [competitive, setCompetitive] = useState<CompetitiveInsight[]>([])
  const [nowPlaying, setNowPlaying] = useState<ActiveSession | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // getSnapshot also persists today's data, feeding the history/insights
    getSnapshot().then(setToday).catch((e) => setError(String(e)))
    getSnapshotHistory(30).then(setHistory).catch(console.error)
    getInsightsByCompetitive().then(setCompetitive).catch(console.error)
    getActiveSession().then(setNowPlaying).catch(console.error)
  }, [])

  const competitiveRow = competitive.find((c) => c.is_competitive)
  const casualRow = competitive.find((c) => !c.is_competitive)

  return (
    <main className="mx-auto max-w-4xl px-5 pt-6 pb-16">
      <header className="flex items-baseline justify-between">
        <h1 className="text-3xl font-semibold text-zinc-900 dark:text-zinc-100">BetterTracker</h1>
        <div className="flex items-center gap-4">
          {nowPlaying && (
            <span className="text-sm text-violet-600 dark:text-violet-400">▶ {nowPlaying.game_name}</span>
          )}
          <a href={GOOGLE_LOGIN_URL} className="text-sm text-violet-600 underline dark:text-violet-400">
            Connect Google Health
          </a>
        </div>
      </header>

      {error && <p className="mt-2 text-sm text-rose-500">Backend unreachable or not authed: {error}</p>}

      {/* --- Today's rings --- */}
      <Section title="Today">
        <div className="flex flex-wrap gap-8">
          <MetricRing label="Sleep score" value={today?.sleep_score} max={100} color="#7c5cff" />
          <MetricRing
            label="Sleep duration"
            value={today?.sleep_duration_minutes != null ? Math.round(today.sleep_duration_minutes / 6) / 10 : null}
            max={8}
            unit="h"
            color="#4fc3f7"
          />
          {/* TODO: more rings — resting HR (inverted: lower is better?), deep sleep vs 90min goal, ... */}
          <MetricRing label="Resting HR" value={today?.resting_heart_rate} max={100} unit=" bpm" color="#ff6b81" />
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
            rows={[
              { label: 'Competitive', value: competitiveRow?.avg_resting_hr, unit: 'bpm' },
              { label: 'Casual', value: casualRow?.avg_resting_hr, unit: 'bpm' },
            ]}
          />
          {/* TODO: sleep impact card (getSleepImpactCompetitive), genre breakdown table, ... */}
        </div>
      </Section>
    </main>
  )
}

export default App
