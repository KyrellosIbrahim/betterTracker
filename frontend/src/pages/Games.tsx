// Games tab — the project's reason to exist: Steam activity and its effect on
// recovery. Currently-playing, a sessions timeline, recently-played, and the
// gaming↔recovery correlation cards (moved here from the Dashboard).

import { useEffect, useState } from 'react'
import {
  getActiveSession,
  getInsightsByCompetitive,
  getLateNightImpact,
  getRecentlyPlayed,
  getSessions,
  getWindDownImpact,
} from '../api/client'
import type {
  ActiveSession,
  CompetitiveInsight,
  GameSession,
  LateNightImpact,
  RecentlyPlayedGame,
  SleepImpactBucket,
  WindDownImpact,
} from '../api/types'
import { ComparisonCard } from '../components/ComparisonCard'
import { Card } from '../components/ui/Card'
import { PageHeader, Section } from '../components/ui/Section'
import { clockTime, formatHm, relativeDay } from '../lib/format'

function CompetitiveBadge({ competitive }: { competitive: boolean | null }) {
  if (competitive == null) return null
  return competitive ? (
    <span className="rounded-full bg-accent/15 px-2 py-0.5 text-[11px] font-medium text-accent">Competitive</span>
  ) : (
    <span className="rounded-full bg-elevated px-2 py-0.5 text-[11px] font-medium text-muted">Casual</span>
  )
}

export function Games() {
  const [active, setActive] = useState<ActiveSession | null>(null)
  const [sessions, setSessions] = useState<GameSession[]>([])
  const [recent, setRecent] = useState<RecentlyPlayedGame[]>([])
  const [competitive, setCompetitive] = useState<CompetitiveInsight[]>([])
  const [windDown, setWindDown] = useState<WindDownImpact | null>(null)
  const [lateNight, setLateNight] = useState<LateNightImpact | null>(null)

  useEffect(() => {
    getActiveSession().then(setActive).catch(console.error)
    getSessions(undefined, 20).then(setSessions).catch(console.error)
    getRecentlyPlayed().then((r) => setRecent(r.games)).catch(console.error)
    getInsightsByCompetitive().then(setCompetitive).catch(console.error)
    getWindDownImpact().then(setWindDown).catch(console.error)
    getLateNightImpact().then(setLateNight).catch(console.error)
  }, [])

  const bucketRow = (label: string, bucket: SleepImpactBucket | undefined) => ({
    label,
    value: bucket?.avg_sleep_score,
    sampleDays: bucket?.sample_days,
    spread: [bucket?.sleep_score_min ?? null, bucket?.sleep_score_max ?? null] as [number | null, number | null],
  })

  const competitiveRow = competitive.find((c) => c.is_competitive)
  const casualRow = competitive.find((c) => !c.is_competitive)
  const maxRecent = Math.max(1, ...recent.map((g) => g.playtime_2weeks))

  return (
    <>
      <PageHeader title="Games" subtitle="Steam sessions and their effect on recovery" />

      {active && (
        <Card className="mb-6 border-accent/40">
          <div className="flex items-center gap-3">
            <span className="size-2 animate-pulse rounded-full bg-accent" />
            <div>
              <p className="text-sm font-medium text-content">
                Playing {active.game_name}
                <span className="ml-2 align-middle">
                  <CompetitiveBadge competitive={active.is_competitive} />
                </span>
              </p>
              <p className="text-[13px] text-muted">
                {formatHm(active.elapsed_minutes)} this session
                {active.genre ? ` · ${active.genre}` : ''}
              </p>
            </div>
          </div>
        </Card>
      )}

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        <Card title="Recent sessions" subtitle={sessions.length ? undefined : 'Sessions are recorded while the backend runs'}>
          {sessions.length === 0 ? (
            <p className="text-[13px] text-muted">No sessions recorded yet.</p>
          ) : (
            <ul className="flex flex-col divide-y divide-line">
              {sessions.map((s) => (
                <li key={s.id} className="flex items-center justify-between gap-3 py-2.5 first:pt-0 last:pb-0">
                  <div className="min-w-0">
                    <p className="truncate text-sm text-content">{s.game_name}</p>
                    <p className="text-[12px] text-muted">
                      {relativeDay(s.start_time.slice(0, 10))} · {clockTime(s.start_time)}
                      {s.genre ? ` · ${s.genre}` : ''}
                    </p>
                  </div>
                  <div className="flex shrink-0 items-center gap-3">
                    <CompetitiveBadge competitive={s.is_competitive} />
                    <span className="w-14 text-right text-sm tabular-nums text-content">
                      {s.duration_minutes != null ? formatHm(s.duration_minutes) : '—'}
                    </span>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </Card>

        <Card title="Recently played" subtitle="Last 2 weeks, from Steam">
          {recent.length === 0 ? (
            <p className="text-[13px] text-muted">Nothing played in the last 2 weeks.</p>
          ) : (
            <ul className="flex flex-col gap-3">
              {recent.slice(0, 8).map((g) => (
                <li key={g.app_id} className="flex flex-col gap-1">
                  <div className="flex items-center justify-between gap-3 text-sm">
                    <span className="truncate text-content">{g.name}</span>
                    <span className="shrink-0 tabular-nums text-muted">{formatHm(g.playtime_2weeks)}</span>
                  </div>
                  <div className="h-1.5 w-full overflow-hidden rounded-full bg-elevated">
                    <div
                      className="h-full rounded-full bg-accent"
                      style={{ width: `${(g.playtime_2weeks / maxRecent) * 100}%` }}
                    />
                  </div>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>

      <Section title="Gaming vs recovery">
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
        </div>
      </Section>
    </>
  )
}
