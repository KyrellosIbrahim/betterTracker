import { PageHeader } from '../components/ui/Section'
import { ComingSoon } from '../components/ui/ComingSoon'

export function Activity() {
  return (
    <>
      <PageHeader title="Activity" subtitle="Steps, active minutes, and workouts" />
      <ComingSoon
        title="Activity"
        note="Steps and active-minutes tracking arrives with the Phase 4 backend expansion — this data isn’t collected yet."
      />
    </>
  )
}
