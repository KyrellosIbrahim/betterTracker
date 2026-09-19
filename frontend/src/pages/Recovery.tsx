import { PageHeader } from '../components/ui/Section'
import { ComingSoon } from '../components/ui/ComingSoon'

export function Recovery() {
  return (
    <>
      <PageHeader title="Recovery" subtitle="Resting heart rate and breathing rate" />
      <ComingSoon title="Recovery detail" note="Resting-HR and breathing trends land in Phase 3 — the data is already collected." />
    </>
  )
}
