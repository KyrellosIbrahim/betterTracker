import { PageHeader } from '../components/ui/Section'
import { ComingSoon } from '../components/ui/ComingSoon'

export function Sleep() {
  return (
    <>
      <PageHeader title="Sleep" subtitle="Stages, duration, and score over time" />
      <ComingSoon title="Sleep detail" note="The hypnogram and sleep trends land in Phase 3 — the data is already collected." />
    </>
  )
}
