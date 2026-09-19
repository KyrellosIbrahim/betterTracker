// Small pill segmented control — used to switch which metric the gaming-vs-
// recovery comparison cards chart.

export interface SegmentOption<T extends string> {
  key: T
  label: string
}

export function SegmentedControl<T extends string>({
  options,
  value,
  onChange,
}: {
  options: SegmentOption<T>[]
  value: T
  onChange: (key: T) => void
}) {
  return (
    <div className="inline-flex flex-wrap gap-0.5 rounded-lg border border-line bg-surface p-0.5">
      {options.map((o) => (
        <button
          key={o.key}
          type="button"
          onClick={() => onChange(o.key)}
          className={`rounded-md px-2.5 py-1 text-[12px] font-medium transition-colors ${
            value === o.key ? 'bg-elevated text-content' : 'text-muted hover:text-content'
          }`}
        >
          {o.label}
        </button>
      ))}
    </div>
  )
}
