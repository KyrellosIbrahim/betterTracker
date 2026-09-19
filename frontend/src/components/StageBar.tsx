// One night's sleep-stage composition as a proportional stacked bar + legend.
//
// Honesty note: the backend stores only per-stage TOTALS (deep/light/rem/awake
// minutes), not the per-segment timeline, so this is a proportional composition
// — NOT a true time-ordered hypnogram. Showing stages in a fabricated order
// would imply a sleep architecture that didn't happen, so we don't. A real
// hypnogram needs the raw stage segments, which is future backend work.

import { stageColors, type SleepStage } from '../lib/colors'
import { formatHm } from '../lib/format'

const ORDER: SleepStage[] = ['deep', 'light', 'rem', 'awake']
const LABELS: Record<SleepStage, string> = { deep: 'Deep', light: 'Light', rem: 'REM', awake: 'Awake' }

export function StageBar({
  deep,
  light,
  rem,
  awake,
}: {
  deep: number | null
  light: number | null
  rem: number | null
  awake: number | null
}) {
  const minutes: Record<SleepStage, number> = {
    deep: deep ?? 0,
    light: light ?? 0,
    rem: rem ?? 0,
    awake: awake ?? 0,
  }
  const total = ORDER.reduce((sum, s) => sum + minutes[s], 0)

  if (total === 0) {
    return <p className="text-[13px] text-muted">No stage breakdown for this night.</p>
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="flex h-4 w-full overflow-hidden rounded-full bg-elevated">
        {ORDER.map((stage) =>
          minutes[stage] > 0 ? (
            <div
              key={stage}
              className="h-full first:rounded-l-full last:rounded-r-full"
              style={{ width: `${(minutes[stage] / total) * 100}%`, backgroundColor: stageColors[stage] }}
              title={`${LABELS[stage]}: ${formatHm(minutes[stage])}`}
            />
          ) : null,
        )}
      </div>

      <div className="grid grid-cols-2 gap-x-6 gap-y-2 sm:grid-cols-4">
        {ORDER.map((stage) => (
          <div key={stage} className="flex flex-col gap-0.5">
            <span className="flex items-center gap-1.5 text-[13px] text-muted">
              <span className="size-2 rounded-full" style={{ backgroundColor: stageColors[stage] }} />
              {LABELS[stage]}
            </span>
            <span className="text-sm font-medium text-content">
              {formatHm(minutes[stage])}
              <span className="ml-1 text-[11px] font-normal text-faint">
                {Math.round((minutes[stage] / total) * 100)}%
              </span>
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
