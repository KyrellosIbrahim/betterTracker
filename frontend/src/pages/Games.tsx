// Games tab — the project's reason to exist: Steam activity and its effect on
// recovery. A KPI row, the sessions timeline + recently-played, a competitive
// tagging UI (writes to the DB and backfills history), and a set of
// gaming-vs-recovery comparisons that share one metric switcher.

import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  getActiveSession,
  getActivityInteraction,
  getLateNightImpact,
  getPlaytimeImpact,
  getRecentlyPlayed,
  getSessions,
  getSleepImpactCompetitive,
  getWeeklyPlaytime,
  getWindDownImpact,
  upsertGame,
} from '../api/client'
import type {
  ActiveSession,
  ActivityInteraction,
  GameSession,
  LateNightImpact,
  PlaytimeImpact,
  RecentlyPlayedGame,
  SleepImpactBucket,
  SleepImpactCompetitive,
  WeeklyPlaytimePoint,
  WindDownImpact,
} from '../api/types'
import { Card, Stat } from '../components/ui/Card'
import { PageHeader, Section } from '../components/ui/Section'
import { SegmentedControl } from '../components/ui/SegmentedControl'
import { CategoryBars, type CategoryDatum } from '../components/charts/CategoryBars'
import { PlaytimeVsSleep } from '../components/charts/PlaytimeVsSleep'
import { clockTime, formatHm, relativeDay } from '../lib/format'
import { metricColors, stageColors } from '../lib/colors'

// The metrics the comparison cards can chart — every bucket carries all of them.
type MetricKey = 'sleep_score' | 'deep' | 'rem' | 'hr' | 'breathing' | 'spo2'
const METRICS: {
  key: MetricKey
  label: string
  field: keyof SleepImpactBucket
  unit: string
  color: string
  fmt: (v: number) => string
}[] = [
  { key: 'sleep_score', label: 'Sleep score', field: 'avg_sleep_score', unit: '', color: metricColors.sleep, fmt: (v) => String(Math.round(v)) },
  { key: 'deep', label: 'Deep', field: 'avg_deep_minutes', unit: 'min', color: stageColors.deep, fmt: (v) => String(Math.round(v)) },
  { key: 'rem', label: 'REM', field: 'avg_rem_minutes', unit: 'min', color: stageColors.rem, fmt: (v) => String(Math.round(v)) },
  { key: 'hr', label: 'Resting HR', field: 'avg_resting_hr', unit: 'bpm', color: metricColors.hr, fmt: (v) => String(Math.round(v)) },
  { key: 'breathing', label: 'Breathing', field: 'avg_breathing_rate', unit: '/min', color: metricColors.breathing, fmt: (v) => v.toFixed(1) },
  { key: 'spo2', label: 'SpO₂', field: 'avg_spo2', unit: '%', color: metricColors.spo2, fmt: (v) => v.toFixed(1) },
]

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
  const [competitiveImpact, setCompetitiveImpact] = useState<SleepImpactCompetitive | null>(null)
  const [activity, setActivity] = useState<ActivityInteraction | null>(null)
  const [playtime, setPlaytime] = useState<PlaytimeImpact | null>(null)
  const [windDown, setWindDown] = useState<WindDownImpact | null>(null)
  const [lateNight, setLateNight] = useState<LateNightImpact | null>(null)
  const [weekly, setWeekly] = useState<WeeklyPlaytimePoint[]>([])
  const [metric, setMetric] = useState<MetricKey>('sleep_score')
  const [saving, setSaving] = useState<number | null>(null)

  // The insight + game data that a competitive re-tag invalidates.
  const loadInsights = useCallback(() => {
    getRecentlyPlayed().then((r) => setRecent(r.games)).catch(console.error)
    getSleepImpactCompetitive().then(setCompetitiveImpact).catch(console.error)
    getActivityInteraction().then(setActivity).catch(console.error)
    getPlaytimeImpact().then(setPlaytime).catch(console.error)
    getWindDownImpact().then(setWindDown).catch(console.error)
    getLateNightImpact().then(setLateNight).catch(console.error)
    getWeeklyPlaytime().then(setWeekly).catch(console.error)
  }, [])

  useEffect(() => {
    getActiveSession().then(setActive).catch(console.error)
    getSessions(undefined, 100).then(setSessions).catch(console.error)
    loadInsights()
  }, [loadInsights])

  const handleToggleCompetitive = useCallback(
    async (game: RecentlyPlayedGame) => {
      setSaving(game.app_id)
      try {
        await upsertGame({
          app_id: game.app_id,
          game_name: game.name,
          genre: game.genre,
          is_competitive: !game.is_competitive,
        })
        // Re-tagging rewrites past sessions, so refetch sessions + insights.
        getSessions(undefined, 100).then(setSessions).catch(console.error)
        loadInsights()
      } catch (e) {
        console.error(e)
      } finally {
        setSaving(null)
      }
    },
    [loadInsights],
  )

  // --- KPI row (all captured sessions) ---
  // Session capture is the scarce resource (it only records while the backend
  // runs and can't be backfilled), so these are all-time rather than a trailing
  // window that would usually read empty.
  const kpis = useMemo(() => {
    const durations = sessions.map((s) => s.duration_minutes).filter((d): d is number => d != null)
    const totalMin = durations.reduce((a, b) => a + b, 0)
    const competitiveCount = sessions.filter((s) => s.is_competitive).length
    return {
      count: sessions.length,
      totalMin,
      share: sessions.length ? Math.round((competitiveCount / sessions.length) * 100) : null,
      avgLen: durations.length ? totalMin / durations.length : null,
    }
  }, [sessions])

  const m = METRICS.find((x) => x.key === metric)!
  const toDatum = (label: string, bucket: SleepImpactBucket | undefined): CategoryDatum => ({
    label,
    value: (bucket?.[m.field] as number | null | undefined) ?? null,
    sampleDays: bucket?.sample_days ?? 0,
    spread: m.key === 'sleep_score' ? [bucket?.sleep_score_min ?? null, bucket?.sleep_score_max ?? null] : undefined,
  })

  const comparison = (data: CategoryDatum[], emptyMessage: string) => (
    <CategoryBars
      data={data}
      color={m.color}
      unit={m.unit}
      valueFormatter={(v) => m.fmt(v)}
      emptyMessage={emptyMessage}
    />
  )

  return (
    <>
      <PageHeader title="Games" subtitle="Steam sessions and their effect on recovery" />

      {/* KPI row */}
      <Card>
        <div className="grid grid-cols-2 gap-6 sm:grid-cols-4">
          <Stat label="Sessions" value={kpis.count} color={metricColors.sleep} />
          <Stat label="Total playtime" value={kpis.totalMin ? formatHm(kpis.totalMin) : '–'} />
          <Stat label="Competitive share" value={kpis.share ?? '–'} unit={kpis.share != null ? '%' : ''} color={metricColors.hr} />
          <Stat label="Avg session" value={kpis.avgLen != null ? formatHm(kpis.avgLen) : '–'} />
        </div>
      </Card>

      {active && (
        <Card className="mt-5 border-accent/40">
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

      <div className="mt-5 grid grid-cols-1 gap-5 lg:grid-cols-2">
        <Card title="Recent sessions" subtitle={sessions.length ? undefined : 'Sessions are recorded while the backend runs'}>
          {sessions.length === 0 ? (
            <p className="text-[13px] text-muted">No sessions recorded yet.</p>
          ) : (
            <ul className="flex max-h-80 flex-col divide-y divide-line overflow-y-auto">
              {sessions.slice(0, 20).map((s) => (
                <li key={s.id} className="flex items-center justify-between gap-3 py-2.5 first:pt-0">
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

        <Card title="Manage games" subtitle="Tag competitive play — updates past sessions & insights">
          {recent.length === 0 ? (
            <p className="text-[13px] text-muted">Nothing played in the last 2 weeks to tag.</p>
          ) : (
            <ul className="flex max-h-80 flex-col divide-y divide-line overflow-y-auto">
              {recent.map((g) => (
                <li key={g.app_id} className="flex items-center justify-between gap-3 py-2.5 first:pt-0">
                  <div className="min-w-0">
                    <p className="truncate text-sm text-content">{g.name}</p>
                    <p className="text-[12px] text-muted">
                      {formatHm(g.playtime_2weeks)} · 2 weeks
                      {g.genre ? ` · ${g.genre}` : ''}
                    </p>
                  </div>
                  <label className="flex shrink-0 cursor-pointer items-center gap-2 text-[12px] text-muted">
                    Competitive
                    <input
                      type="checkbox"
                      className="size-4 accent-[var(--color-accent)]"
                      checked={!!g.is_competitive}
                      disabled={saving === g.app_id}
                      onChange={() => handleToggleCompetitive(g)}
                    />
                  </label>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>

      <Section
        title="Gaming vs recovery"
        action={<SegmentedControl options={METRICS.map((x) => ({ key: x.key, label: x.label }))} value={metric} onChange={setMetric} />}
      >
        <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
          <Card title="Does gaming hurt recovery?" subtitle="Next morning after competitive vs casual vs no-gaming nights">
            {comparison(
              [
                toDatum('Competitive', competitiveImpact?.competitive_days),
                toDatum('Casual', competitiveImpact?.casual_only_days),
                toDatum('No gaming', competitiveImpact?.no_gaming_days),
              ],
              'No sessions recorded yet — play something to start comparing.',
            )}
          </Card>

          <Card title="Does staying active offset it?" subtitle="Gaming days that were also physically active vs sedentary">
            {comparison(
              [
                toDatum('Active', activity?.gaming_active),
                toDatum('Sedentary', activity?.gaming_sedentary),
                toDatum('No gaming', activity?.no_gaming),
              ],
              'Need gaming days with activity data to compare.',
            )}
          </Card>

          <Card title="Session length" subtitle="By total playtime that day">
            {comparison(
              [
                toDatum('<1h', playtime?.under_1h),
                toDatum('1–3h', playtime?.['1_to_3h']),
                toDatum('3h+', playtime?.over_3h),
              ],
              'No sessions recorded yet.',
            )}
          </Card>

          <Card title="Late-night gaming" subtitle="Last session past 11pm vs earlier vs none">
            {comparison(
              [
                toDatum('Late', lateNight?.late_night_gaming),
                toDatum('Earlier', lateNight?.earlier_gaming),
                toDatum('No gaming', lateNight?.no_gaming),
              ],
              'No sessions recorded yet.',
            )}
          </Card>

          <Card title="Wind-down gap" subtitle="Time between last session and bed">
            {comparison(
              [
                toDatum('<30m', windDown?.under_30min),
                toDatum('30–90m', windDown?.['30_to_90min']),
                toDatum('90m+', windDown?.over_90min),
              ],
              'No sessions with a measurable wind-down gap yet.',
            )}
          </Card>
        </div>

        <div className="mt-5">
          <Card title="Weekly playtime vs sleep" subtitle="Total gaming hours vs average next-morning sleep score">
            <PlaytimeVsSleep data={weekly} />
          </Card>
        </div>
      </Section>
    </>
  )
}
