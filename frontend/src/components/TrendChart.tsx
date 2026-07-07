// Minimal dependency-free SVG line chart for daily trends.
// Pass points in chronological order (getSnapshotHistory is already sorted).
// Barebones on purpose — no axes/tooltips yet. Swap in recharts/chart.js
// later if you want interactivity.

interface TrendPoint {
  label: string // e.g. the date
  value: number | null
}

interface TrendChartProps {
  title: string
  points: TrendPoint[]
  color?: string
  height?: number
}

export function TrendChart({ title, points, color = '#4fc3f7', height = 120 }: TrendChartProps) {
  const width = 400
  const pad = 8
  const values = points.map((p) => p.value).filter((v): v is number => v != null)

  let path = ''
  if (values.length >= 2) {
    const min = Math.min(...values)
    const max = Math.max(...values)
    const span = max - min || 1
    const drawable = points.filter((p) => p.value != null)
    path = drawable
      .map((p, i) => {
        const x = pad + (i / (drawable.length - 1)) * (width - pad * 2)
        const y = height - pad - ((p.value! - min) / span) * (height - pad * 2)
        return `${i === 0 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`
      })
      .join(' ')
  }

  return (
    <div>
      <h3 className="mb-2 text-sm font-medium text-zinc-900 dark:text-zinc-100">{title}</h3>
      {path ? (
        <svg
          viewBox={`0 0 ${width} ${height}`}
          preserveAspectRatio="none"
          className="h-[120px] w-full rounded-lg bg-zinc-100 dark:bg-zinc-800"
        >
          <path d={path} fill="none" stroke={color} strokeWidth={2} strokeLinejoin="round" />
        </svg>
      ) : (
        <p className="rounded-lg bg-zinc-100 px-4 py-6 text-[13px] text-zinc-500 dark:bg-zinc-800 dark:text-zinc-400">
          Not enough data yet — hit /health/snapshot on a few different days.
        </p>
      )}
    </div>
  )
}
