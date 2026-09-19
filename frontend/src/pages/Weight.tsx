import { PageHeader } from '../components/ui/Section'
import { ComingSoon } from '../components/ui/ComingSoon'

export function Weight() {
  return (
    <>
      <PageHeader title="Weight" subtitle="Body weight over time" />
      <ComingSoon
        title="Weight"
        note="Weight tracking arrives with the Phase 4 backend expansion — this data isn’t collected yet."
      />
    </>
  )
}
