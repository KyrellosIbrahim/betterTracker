// Side-by-side stat comparison, e.g. resting HR on competitive vs casual days.
// Rows render as label + big number; null shows as a dash.

interface ComparisonRow {
  label: string
  value: number | string | null | undefined
  unit?: string
}

interface ComparisonCardProps {
  title: string
  rows: ComparisonRow[]
}

export function ComparisonCard({ title, rows }: ComparisonCardProps) {
  return (
    <div className="rounded-lg bg-zinc-100 p-4 dark:bg-zinc-800">
      <h3 className="mb-2 text-sm font-medium text-zinc-900 dark:text-zinc-100">{title}</h3>
      <div className="flex gap-8">
        {rows.map((row) => (
          <div key={row.label} className="flex flex-col">
            <span className="text-[28px] font-semibold text-zinc-900 dark:text-zinc-100">
              {row.value == null ? '–' : row.value}
              {row.value != null && row.unit ? (
                <small className="ml-1 text-[13px] font-normal text-zinc-500 dark:text-zinc-400">{row.unit}</small>
              ) : null}
            </span>
            <span className="text-[13px] text-zinc-500 dark:text-zinc-400">{row.label}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
