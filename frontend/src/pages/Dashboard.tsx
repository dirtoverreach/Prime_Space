import { useQuery } from '@tanstack/react-query'
import { fetchDevices } from '../api/devices'
import { fetchAlerts } from '../api/alerts'
import { fetchJobs } from '../api/commands'
import { Server, AlertTriangle, Terminal, CheckCircle } from 'lucide-react'

function StatCard({ icon: Icon, label, value, color }: { icon: any; label: string; value: number; color: string }) {
  return (
    <div className="bg-white rounded-xl shadow p-5 flex items-center gap-4">
      <div className={`p-3 rounded-lg ${color}`}>
        <Icon size={22} className="text-white" />
      </div>
      <div>
        <p className="text-2xl font-bold text-gray-900">{value}</p>
        <p className="text-sm text-gray-500">{label}</p>
      </div>
    </div>
  )
}

export default function Dashboard() {
  const { data: devices = [] } = useQuery({ queryKey: ['devices'], queryFn: () => fetchDevices() })
  const { data: alerts = [] } = useQuery({ queryKey: ['alerts'], queryFn: () => fetchAlerts({ state: 'open' }) })
  const { data: jobs = [] } = useQuery({ queryKey: ['jobs'], queryFn: fetchJobs })

  const reachable = devices.filter((d) => d.status === 'reachable').length
  const openAlerts = alerts.filter((a) => a.state === 'open').length

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-800">Dashboard</h1>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={Server} label="Total Devices" value={devices.length} color="bg-blue-500" />
        <StatCard icon={CheckCircle} label="Reachable" value={reachable} color="bg-green-500" />
        <StatCard icon={AlertTriangle} label="Open Alerts" value={openAlerts} color="bg-orange-500" />
        <StatCard icon={Terminal} label="Recent Jobs" value={jobs.length} color="bg-purple-500" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-white rounded-xl shadow p-5">
          <h2 className="font-semibold text-gray-700 mb-3">Recent Alerts</h2>
          {alerts.length === 0 ? (
            <p className="text-sm text-gray-400">No open alerts</p>
          ) : (
            <ul className="space-y-2">
              {alerts.slice(0, 5).map((a) => (
                <li key={a.id} className="flex items-center gap-2 text-sm">
                  <span className={`w-2 h-2 rounded-full ${a.severity === 'critical' ? 'bg-red-500' : a.severity === 'warning' ? 'bg-orange-400' : 'bg-blue-400'}`} />
                  <span className="text-gray-700 truncate">{a.message ?? `${a.metric} = ${a.value}`}</span>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="bg-white rounded-xl shadow p-5">
          <h2 className="font-semibold text-gray-700 mb-3">Device Status</h2>
          <ul className="space-y-2">
            {devices.slice(0, 8).map((d) => (
              <li key={d.id} className="flex items-center justify-between text-sm">
                <span className="font-mono text-gray-700">{d.hostname}</span>
                <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                  d.status === 'reachable' ? 'bg-green-100 text-green-700'
                  : d.status === 'unreachable' ? 'bg-red-100 text-red-700'
                  : 'bg-gray-100 text-gray-600'
                }`}>
                  {d.status}
                </span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  )
}
