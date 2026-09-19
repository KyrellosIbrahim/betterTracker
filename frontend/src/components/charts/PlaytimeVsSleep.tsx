// Weekly total playtime (bars, hours) against average next-morning sleep score
// (line) — does a heavier gaming week track with worse sleep? Two y-axes since
// the units differ.

import {
  Bar,
  CartesianGrid,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { WeeklyPlaytimePoint } from '../../api/types'
import { axisTick, chartChrome } from './chartTheme'
import { metricColors } from '../../lib/colors'
import { formatDuration, monthDay } from '../../lib/format'

interface WeeklyTooltipProps {
  active?: boolean
  payload?: Array<{ payload: WeeklyPlaytimePoint }>
}

function WeeklyTooltip({ active, payload }: WeeklyTooltipProps) {
  if (!active || !payload || payload.length === 0) return null
  const d = payload[0].payload
  return (
    <div className="rounded-lg border border-line bg-elevated px-3 py-2 text-xs shadow-lg">
      <div className="mb-1 text-faint">Week of {monthDay(d.week_start)}</div>
      <div className="flex items-center gap-1.5 text-content">
        <span className="size-2 rounded-full" style={{ backgroundColor: metricColors.steps }} />
        Playtime <span className="ml-auto font-medium">{formatDuration(d.total_minutes)}</span>
      </div>
      <div className="mt-0.5 flex items-center gap-1.5 text-content">
        <span className="size-2 rounded-full" style={{ backgroundColor: metricColors.sleep }} />
        Sleep score <span className="ml-auto font-medium">{d.avg_sleep_score ?? '–'}</span>
      </div>
    </div>
  )
}

export function PlaytimeVsSleep({
  data,
  height = 220,
  emptyMessage = 'Not enough weeks with gaming yet.',
}: {
  data: WeeklyPlaytimePoint[]
  height?: number
  emptyMessage?: string
}) {
  if (data.length < 2) {
    return (
      <p className="rounded-lg bg-elevated/60 px-4 py-6 text-[13px] text-muted" style={{ minHeight: height }}>
        {emptyMessage}
      </p>
    )
  }

  // Bars are drawn in hours so the axis reads sensibly.
  const rows = data.map((d) => ({ ...d, hours: d.total_minutes / 60 }))

  return (
    <ResponsiveContainer width="100%" height={height}>
      <ComposedChart data={rows} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
        <CartesianGrid stroke={chartChrome.grid} strokeDasharray="3 3" vertical={false} />
        <XAxis
          dataKey="week_start"
          tick={axisTick}
          tickFormatter={(v) => monthDay(String(v))}
          axisLine={{ stroke: chartChrome.grid }}
          tickLine={false}
          minTickGap={16}
        />
        <YAxis
          yAxisId="hours"
          tick={axisTick}
          axisLine={false}
          tickLine={false}
          width={40}
          tickFormatter={(v) => `${v}h`}
        />
        <YAxis
          yAxisId="score"
          orientation="right"
          domain={[0, 100]}
          tick={axisTick}
          axisLine={false}
          tickLine={false}
          width={32}
        />
        <Tooltip cursor={{ fill: chartChrome.cursor }} content={<WeeklyTooltip />} />
        <Bar yAxisId="hours" dataKey="hours" fill={metricColors.steps} radius={[4, 4, 0, 0]} maxBarSize={48} />
        <Line
          yAxisId="score"
          type="monotone"
          dataKey="avg_sleep_score"
          stroke={metricColors.sleep}
          strokeWidth={2}
          connectNulls
          dot={false}
        />
      </ComposedChart>
    </ResponsiveContainer>
  )
}
