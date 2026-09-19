// Interactive weekly bar chart — the "steps/sleep/HR this week" cards from the
// reference dashboard. Hover a bar for its exact value + day. Heading is owned
// by the surrounding Card.

import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { ReactNode } from 'react'
import { ChartTooltip } from './ChartTooltip'
import { axisTick, chartChrome, chartMargin } from './chartTheme'
import { metricColors } from '../../lib/colors'
import type { TrendPoint } from './LineTrend'

interface BarWeekProps {
  points: TrendPoint[]
  color?: string
  height?: number
  unit?: string
  labelFormatter?: (label: string | number) => ReactNode
  valueFormatter?: (value: number) => ReactNode
  emptyMessage?: string
}

export function BarWeek({
  points,
  color = metricColors.steps,
  height = 160,
  unit,
  labelFormatter,
  valueFormatter,
  emptyMessage = 'No data for this week yet.',
}: BarWeekProps) {
  const hasAny = points.some((p) => p.value != null)

  if (!hasAny) {
    return (
      <p className="rounded-lg bg-elevated/60 px-4 py-6 text-[13px] text-muted" style={{ minHeight: height }}>
        {emptyMessage}
      </p>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={points} margin={chartMargin}>
        <CartesianGrid stroke={chartChrome.grid} strokeDasharray="3 3" vertical={false} />
        <XAxis
          dataKey="label"
          tick={axisTick}
          tickFormatter={labelFormatter ? (v) => String(labelFormatter(v)) : undefined}
          axisLine={{ stroke: chartChrome.grid }}
          tickLine={false}
        />
        <YAxis tick={axisTick} axisLine={false} tickLine={false} width={36} />
        <Tooltip
          cursor={{ fill: chartChrome.cursor }}
          content={<ChartTooltip unit={unit} labelFormatter={labelFormatter} valueFormatter={valueFormatter} />}
        />
        <Bar dataKey="value" fill={color} radius={[4, 4, 0, 0]} maxBarSize={40} />
      </BarChart>
    </ResponsiveContainer>
  )
}
