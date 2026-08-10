// Side-by-side stat comparison, e.g. resting HR on competitive vs casual days.
// Rows render as label + big number; null shows as a dash.
//
// Guardrails: a mean over 2 days is noise, so the whole card dims when EITHER
// side is thin — a comparison is only as trustworthy as its weakest side — and
// each row shows its own day count and range so you can see which side is thin
// and whether the two ranges overlap.
const MIN_SAMPLE_DAYS = 5

interface ComparisonRow {
  label: string
  value: number | string | null | undefined
  unit?: string
  sampleDays?: number
  /** [min, max] of the underlying values, shown next to the day count. */
  spread?: [number | null, number | null]
}

interface ComparisonCardProps {
  title: string
  rows: ComparisonRow[]
  /** Shown instead of a row of dashes when no row has any data yet. */
  emptyMessage?: string
}

export function ComparisonCard({ title, rows, emptyMessage = 'No data yet' }: ComparisonCardProps) {
  const thin = rows.some((row) => row.sampleDays != null && row.sampleDays < MIN_SAMPLE_DAYS)
  const valueColor = thin ? 'text-zinc-400 dark:text-zinc-500' : 'text-zinc-900 dark:text-zinc-100'
  // "No data at all" and "thin data" mean different things — don't render both as dashes.
  const empty = rows.every((row) => row.value == null)

  return (
    <div className="rounded-lg bg-zinc-100 p-4 dark:bg-zinc-800">
      <h3 className="mb-2 text-sm font-medium text-zinc-900 dark:text-zinc-100">{title}</h3>

      {empty ? (
        <p className="py-2 text-[13px] text-zinc-500 dark:text-zinc-400">{emptyMessage}</p>
      ) : (
        <div className="flex gap-8">
          {rows.map((row) => {
            const days = row.sampleDays
            const rowThin = days != null && days < MIN_SAMPLE_DAYS
            const [min, max] = row.spread ?? [null, null]
            const meta = [
              days != null ? `${days} day${days === 1 ? '' : 's'}` : null,
              min != null && max != null ? `${min}–${max}` : null,
            ]
              .filter(Boolean)
              .join(' · ')

            return (
              <div key={row.label} className="flex flex-col">
                <span
                  className={`text-[28px] font-semibold ${valueColor}`}
                  title={rowThin ? `Only ${days} day${days === 1 ? '' : 's'} of data — not enough to compare` : undefined}
                >
                  {row.value == null ? '–' : row.value}
                  {row.value != null && row.unit ? (
                    <small className="ml-1 text-[13px] font-normal text-zinc-500 dark:text-zinc-400">{row.unit}</small>
                  ) : null}
                </span>
                <span className="text-[13px] text-zinc-500 dark:text-zinc-400">{row.label}</span>
                {meta && <span className="text-[11px] text-zinc-400 dark:text-zinc-500">{meta}</span>}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
