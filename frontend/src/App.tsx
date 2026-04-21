import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'react-hot-toast'
import PageShell from './components/layout/PageShell'
import Dashboard from './pages/Dashboard'
import Inventory from './pages/Inventory'
import Topology from './pages/Topology'
import ConfigManager from './pages/ConfigManager'
import Monitoring from './pages/Monitoring'
import Alerts from './pages/Alerts'
import CommandRunner from './pages/CommandRunner'

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 30_000, retry: 1 } },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route element={<PageShell />}>
            <Route path="/" element={<Dashboard />} />
            <Route path="/inventory" element={<Inventory />} />
            <Route path="/topology" element={<Topology />} />
            <Route path="/configs" element={<ConfigManager />} />
            <Route path="/monitoring" element={<Monitoring />} />
            <Route path="/alerts" element={<Alerts />} />
            <Route path="/commands" element={<CommandRunner />} />
          </Route>
        </Routes>
      </BrowserRouter>
      <Toaster position="bottom-right" />
    </QueryClientProvider>
  )
}
