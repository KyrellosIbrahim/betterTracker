// Interactive line trend — the Recharts replacement for the old hand-rolled
// TrendChart. Hover shows an exact value + formatted date. Title/heading is
// owned by the surrounding Card, so this renders just the plot.

import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { ReactNode } from 'react'
import { ChartTooltip } from './ChartTooltip'
import { axisTick, chartChrome, chartMargin } from './chartTheme'
import { metricColors } from '../../lib/colors'

export interface TrendPoint {
  label: string // usually an ISO date
  value: number | null
}

interface LineTrendProps {
  points: TrendPoint[]
  color?: string
  height?: number
  unit?: string
  /** Format x tick + tooltip header (e.g. ISO date → "Fri"). */
  labelFormatter?: (label: string | number) => ReactNode
  /** Format the tooltip value. */
  valueFormatter?: (value: number) => ReactNode
  /** Allow fractional y-axis ticks. Off for e.g. hours, so 6.75 doesn't appear. */
  yAllowDecimals?: boolean
  /** Format y-axis ticks (e.g. compact "4k" for step counts). */
  yTickFormatter?: (value: number) => string
  emptyMessage?: string
}

export function LineTrend({
  points,
  color = metricColors.duration,
  height = 160,
  unit,
  labelFormatter,
  valueFormatter,
  yAllowDecimals = true,
  yTickFormatter,
  emptyMessage = 'Not enough data yet — check back after a few days of syncing.',
}: LineTrendProps) {
  const hasEnough = points.filter((p) => p.value != null).length >= 2

  if (!hasEnough) {
    return (
      <p className="rounded-lg bg-elevated/60 px-4 py-6 text-[13px] text-muted" style={{ minHeight: height }}>
        {emptyMessage}
      </p>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={points} margin={chartMargin}>
        <CartesianGrid stroke={chartChrome.grid} strokeDasharray="3 3" vertical={false} />
        <XAxis
          dataKey="label"
          tick={axisTick}
          tickFormatter={labelFormatter ? (v) => String(labelFormatter(v)) : undefined}
          axisLine={{ stroke: chartChrome.grid }}
          tickLine={false}
          minTickGap={24}
        />
        <YAxis
          tick={axisTick}
          axisLine={false}
          tickLine={false}
          width={44}
          domain={['auto', 'auto']}
          allowDecimals={yAllowDecimals}
          tickFormatter={yTickFormatter}
        />
        <Tooltip
          cursor={{ stroke: color, strokeWidth: 1, strokeDasharray: '3 3' }}
          content={<ChartTooltip unit={unit} labelFormatter={labelFormatter} valueFormatter={valueFormatter} />}
        />
        <Line
          type="monotone"
          dataKey="value"
          stroke={color}
          strokeWidth={2}
          connectNulls
          dot={false}
          activeDot={{ r: 4, fill: color, stroke: 'var(--color-bg)', strokeWidth: 2 }}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}
