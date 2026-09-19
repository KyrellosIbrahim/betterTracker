// Health tab — the catch-all: every metric Google Health reports in one place,
// plus the connection/source status. A superset overview; the focused tabs
// (Sleep, Recovery) go deeper on each.

import { useEffect, useState } from 'react'
import { getAuthStatus, getSnapshotHistory } from '../api/client'
import type { AuthStatus, HealthSnapshot } from '../api/types'
import { LineTrend } from '../components/charts/LineTrend'
import { Card, Stat } from '../components/ui/Card'
import { PageHeader, Section } from '../components/ui/Section'
import { ComingSoon } from '../components/ui/ComingSoon'
import { formatDuration, monthDay, relativeDay, relativeTime } from '../lib/format'
import { latestOf } from '../lib/stats'
import { metricColors } from '../lib/colors'

export function Health() {
  const [history, setHistory] = useState<HealthSnapshot[]>([])
  const [auth, setAuth] = useState<AuthStatus | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getSnapshotHistory(30)
      .then(setHistory)
      .catch(console.error)
      .finally(() => setLoading(false))
    getAuthStatus().then(setAuth).catch(console.error)
  }, [])

  const latest = history.at(-1) ?? null
  const sleepScore = latestOf(history, (s) => s.sleep_score)
  const sleepMinutes = latestOf(history, (s) => s.sleep_duration_minutes)
  const restingHr = latestOf(history, (s) => s.resting_heart_rate)
  const breathing = latestOf(history, (s) => s.breathing_rate)

  return (
    <>
      <PageHeader
        title="Health"
        subtitle={latest ? `Latest data from ${relativeDay(latest.date)}` : 'Everything Google Health reports'}
      />

      {loading ? (
        <p className="text-sm text-muted">Loading…</p>
      ) : history.length === 0 ? (
        <ComingSoon title="No health data yet" note="Connect Google Health and let a day sync to populate this tab." />
      ) : (
        <>
          <Card>
            <div className="grid grid-cols-2 gap-6 sm:grid-cols-4">
              <Stat label="Sleep score" value={sleepScore ?? '–'} color={metricColors.sleep} />
              <Stat
                label="Time asleep"
                value={sleepMinutes != null ? formatDuration(sleepMinutes) : '–'}
                color={metricColors.duration}
              />
              <Stat label="Resting HR" value={restingHr ?? '–'} unit="bpm" color={metricColors.hr} />
              <Stat
                label="Breathing"
                value={breathing != null ? breathing.toFixed(1) : '–'}
                unit="/min"
                color={metricColors.breathing}
              />
            </div>
          </Card>

          <Section title="All trends (30d)">
            <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
              <Card title="Sleep score">
                <LineTrend
                  color={metricColors.sleep}
                  points={history.map((s) => ({ label: s.date, value: s.sleep_score }))}
                  labelFormatter={(v) => monthDay(String(v))}
                  valueFormatter={(v) => Math.round(v)}
                />
              </Card>
              <Card title="Time asleep">
                <LineTrend
                  color={metricColors.duration}
                  yAllowDecimals={false}
                  points={history.map((s) => ({
                    label: s.date,
                    value: s.sleep_duration_minutes != null ? s.sleep_duration_minutes / 60 : null,
                  }))}
                  labelFormatter={(v) => monthDay(String(v))}
                  valueFormatter={(h) => formatDuration(h * 60)}
                />
              </Card>
              <Card title="Resting heart rate">
                <LineTrend
                  color={metricColors.hr}
                  unit="bpm"
                  points={history.map((s) => ({ label: s.date, value: s.resting_heart_rate }))}
                  labelFormatter={(v) => monthDay(String(v))}
                  valueFormatter={(v) => Math.round(v)}
                />
              </Card>
              <Card title="Breathing rate">
                <LineTrend
                  color={metricColors.breathing}
                  unit="/min"
                  points={history.map((s) => ({ label: s.date, value: s.breathing_rate }))}
                  labelFormatter={(v) => monthDay(String(v))}
                  valueFormatter={(v) => v.toFixed(1)}
                />
              </Card>
            </div>
          </Section>

          <Section title="Source">
            <Card>
              <div className="flex flex-wrap items-center justify-between gap-3 text-sm">
                <span className="flex items-center gap-2">
                  <span className={`size-2 rounded-full ${auth?.connected ? 'bg-good' : 'bg-faint'}`} />
                  <span className="text-content">Google Health</span>
                  <span className="text-muted">{auth?.connected ? 'connected' : 'not connected'}</span>
                </span>
                {auth?.last_success_at && (
                  <span className="text-[13px] text-muted" title={new Date(auth.last_success_at).toLocaleString()}>
                    Last sync {relativeTime(auth.last_success_at)}
                  </span>
                )}
              </div>
              {auth?.last_error && <p className="mt-2 text-[13px] text-warn">Last error: {auth.last_error}</p>}
            </Card>
          </Section>
        </>
      )}
    </>
  )
}
