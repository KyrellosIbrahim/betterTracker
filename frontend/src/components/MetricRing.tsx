// Apple-Watch-style progress ring. Fills proportionally across [min, max].
// "Fuller = better" is the convention: for lower-is-better metrics (resting HR,
// breathing) pass `invert` so a lower value fills more.
// Example: <MetricRing label="Sleep" value={84} max={100} color="#7c5cff" />
//          <MetricRing label="Resting HR" value={64} min={50} max={90} invert />

interface MetricRingProps {
  label: string
  /** Drives how far the ring fills. Always numeric, even when `display` overrides the text. */
  value: number | null | undefined
  max: number
  /** Low end of the fill range (default 0). */
  min?: number
  /** Flip the fill so a LOWER value reads fuller — for lower-is-better metrics. */
  invert?: boolean
  unit?: string
  /** Overrides the centre text, e.g. "6:24" for a duration held as 384 minutes. */
  display?: string
  color?: string
  size?: number
}

export function MetricRing({
  label,
  value,
  max,
  min = 0,
  invert = false,
  unit = '',
  display,
  color = '#7c5cff',
  size = 120,
}: MetricRingProps) {
  const stroke = size * 0.09
  const radius = (size - stroke) / 2
  const circumference = 2 * Math.PI * radius
  // Clamp the raw ratio before inverting, so a value past either anchor
  // saturates correctly (better-than-best → full, worse-than-worst → empty).
  // A missing value is always empty — never let `invert` turn null into a full ring.
  const ratio = Math.min(Math.max(((value ?? min) - min) / (max - min || 1), 0), 1)
  const fraction = value == null ? 0 : invert ? 1 - ratio : ratio

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
          {value == null ? '–' : (display ?? `${value}${unit}`)}
        </text>
      </svg>
      <span className="text-[13px] text-zinc-500 dark:text-zinc-400">{label}</span>
    </div>
  )
}
