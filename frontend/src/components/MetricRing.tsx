// Apple-Watch-style progress ring. Pass value/max and it fills proportionally.
// Example: <MetricRing label="Sleep" value={84} max={100} color="#7c5cff" />

interface MetricRingProps {
  label: string
  value: number | null | undefined
  max: number
  unit?: string
  color?: string
  size?: number
}

export function MetricRing({ label, value, max, unit = '', color = '#7c5cff', size = 120 }: MetricRingProps) {
  const stroke = size * 0.09
  const radius = (size - stroke) / 2
  const circumference = 2 * Math.PI * radius
  const fraction = value == null ? 0 : Math.min(Math.max(value / max, 0), 1)

  return (
    <div className="flex flex-col items-center gap-1">
      <svg width={size} height={size}>
        {/* Track */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          opacity={0.15}
          strokeWidth={stroke}
        />
        {/* Fill — starts at 12 o'clock */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={circumference * (1 - fraction)}
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
        />
        <text
          x="50%"
          y="50%"
          textAnchor="middle"
          dominantBaseline="central"
          className="fill-zinc-900 text-[22px] font-semibold dark:fill-zinc-100"
        >
          {value == null ? '–' : `${value}${unit}`}
        </text>
      </svg>
      <span className="text-[13px] text-zinc-500 dark:text-zinc-400">{label}</span>
    </div>
  )
}
