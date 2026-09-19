// Route table. The shell (sidebar + header) lives in AppLayout; each tab is a
// page under it. Tabs without backend data yet render a "coming soon" stub
// (see the individual page files).

import { Routes, Route } from 'react-router-dom'
import { AppLayout } from './components/layout/AppLayout'
import { Dashboard } from './pages/Dashboard'
import { Activity } from './pages/Activity'
import { Sleep } from './pages/Sleep'
import { Recovery } from './pages/Recovery'
import { Health } from './pages/Health'
import { Weight } from './pages/Weight'
import { Games } from './pages/Games'

function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<Dashboard />} />
        <Route path="activity" element={<Activity />} />
        <Route path="sleep" element={<Sleep />} />
        <Route path="recovery" element={<Recovery />} />
        <Route path="health" element={<Health />} />
        <Route path="weight" element={<Weight />} />
        <Route path="games" element={<Games />} />
      </Route>
    </Routes>
  )
}

export default App
