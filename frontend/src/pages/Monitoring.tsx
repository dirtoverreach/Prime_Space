import { useEffect, useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import { fetchDevices } from '../api/devices'
import { fetchAllStats } from '../api/monitoring'
import type { DeviceMetric } from '../types/monitoring'

function Gauge({ label, value }: { label: string; value: number | null }) {
  const pct = value ?? 0
  const color = pct > 90 ? 'bg-red-500' : pct > 70 ? 'bg-orange-400' : 'bg-green-500'
  return (
    <div>
      <div className="flex justify-between text-xs text-gray-500 mb-1">
        <span>{label}</span>
        <span>{value !== null ? `${pct.toFixed(1)}%` : '—'}</span>
      </div>
      <div className="w-full bg-gray-100 rounded-full h-2">
        <div className={`${color} h-2 rounded-full transition-all`} style={{ width: `${Math.min(pct, 100)}%` }} />
      </div>
    </div>
  )
}

function DeviceCard({ metric, hostname }: { metric: DeviceMetric; hostname: string }) {
  return (
    <div className="bg-white rounded-xl shadow p-4 space-y-3">
      <div className="flex items-center justify-between">
        <span className="font-mono font-medium text-sm text-gray-800">{hostname}</span>
        <span className="text-xs text-gray-400">{new Date(metric.collected_at + 'Z').toLocaleTimeString()}</span>
      </div>
      <Gauge label="CPU" value={metric.cpu_percent} />
      <Gauge label="Memory" value={metric.mem_used_percent} />
      {metric.interface_stats && (
        <p className="text-xs text-gray-400">{Object.keys(metric.interface_stats).length} interfaces</p>
      )}
    </div>
  )
}

export default function Monitoring() {
  const wsRef = useRef<WebSocket | null>(null)

  const { data: devices = [] } = useQuery({ queryKey: ['devices'], queryFn: () => fetchDevices() })
  const { data: stats = [], refetch } = useQuery({ queryKey: ['stats'], queryFn: fetchAllStats, refetchInterval: 60000 })

  const deviceMap = Object.fromEntries(devices.map((d) => [d.id, d.hostname]))

  useEffect(() => {
    const wsUrl = `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/api/v1/monitoring/ws`
    wsRef.current = new WebSocket(wsUrl)
    wsRef.current.onmessage = () => {
      refetch()
    }
    return () => wsRef.current?.close()
  }, [])

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800">Monitoring</h1>
        <div className="flex items-center gap-2 text-sm text-green-600">
          <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
          Live
        </div>
      </div>

      {stats.length === 0 ? (
        <div className="bg-white rounded-xl shadow p-8 text-center text-gray-400">
          No metrics yet. Ensure SNMP is configured and polling is running.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {stats.map((m: DeviceMetric) => (
            <DeviceCard key={m.device_id} metric={m} hostname={deviceMap[m.device_id] ?? m.device_id.slice(0, 8)} />
          ))}
        </div>
      )}
    </div>
  )
}
