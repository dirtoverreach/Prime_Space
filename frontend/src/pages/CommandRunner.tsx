import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { fetchDevices } from '../api/devices'
import { submitJob, fetchJob } from '../api/commands'
import type { CommandJob } from '../types/command'
import { Play } from 'lucide-react'

export default function CommandRunner() {
  const [selectedDevices, setSelectedDevices] = useState<Set<string>>(new Set())
  const [command, setCommand] = useState('')
  const [jobId, setJobId] = useState<string | null>(null)

  const { data: devices = [] } = useQuery({ queryKey: ['devices'], queryFn: () => fetchDevices() })
  const { data: job } = useQuery<CommandJob>({
    queryKey: ['job', jobId],
    queryFn: () => fetchJob(jobId!),
    enabled: !!jobId,
    refetchInterval: (query) => {
      const d = query.state.data
      return d?.status === 'completed' || d?.status === 'failed' ? false : 2000
    },
  })

  const submitMut = useMutation({
    mutationFn: () => submitJob(command, Array.from(selectedDevices)),
    onSuccess: (data) => setJobId(data.id),
  })

  const toggleDevice = (id: string) => {
    setSelectedDevices((prev) => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  const deviceMap = Object.fromEntries(devices.map((d) => [d.id, d.hostname]))

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-gray-800">Command Runner</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="bg-white rounded-xl shadow p-4 space-y-2">
          <h2 className="font-semibold text-sm text-gray-600">Select Devices</h2>
          {devices.length === 0 ? (
            <p className="text-sm text-gray-400">No devices available.</p>
          ) : (
            <div className="space-y-1 max-h-72 overflow-y-auto">
              {devices.map((d) => (
                <label key={d.id} className="flex items-center gap-2 text-sm cursor-pointer hover:bg-gray-50 px-2 py-1 rounded">
                  <input
                    type="checkbox"
                    checked={selectedDevices.has(d.id)}
                    onChange={() => toggleDevice(d.id)}
                    className="accent-blue-600"
                  />
                  <span className="font-mono">{d.hostname}</span>
                  <span className={`ml-auto text-xs ${d.status === 'reachable' ? 'text-green-500' : 'text-gray-400'}`}>{d.status}</span>
                </label>
              ))}
            </div>
          )}
          <p className="text-xs text-gray-400">{selectedDevices.size} selected</p>
        </div>

        <div className="lg:col-span-2 bg-white rounded-xl shadow p-4 space-y-3">
          <h2 className="font-semibold text-sm text-gray-600">Command</h2>
          <textarea
            value={command}
            onChange={(e) => setCommand(e.target.value)}
            placeholder="e.g. show version"
            rows={3}
            className="w-full border rounded px-3 py-2 text-sm font-mono resize-none"
          />
          <button
            onClick={() => submitMut.mutate()}
            disabled={!command || selectedDevices.size === 0 || submitMut.isPending}
            className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm disabled:opacity-50"
          >
            <Play size={15} />
            {submitMut.isPending ? 'Submitting…' : `Run on ${selectedDevices.size} device(s)`}
          </button>
        </div>
      </div>

      {job && (
        <div className="bg-white rounded-xl shadow p-4 space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold text-sm text-gray-600">Results</h2>
            <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
              job.status === 'completed' ? 'bg-green-100 text-green-700'
              : job.status === 'failed' ? 'bg-red-100 text-red-700'
              : 'bg-yellow-100 text-yellow-700'
            }`}>{job.status}</span>
          </div>
          {job.status !== 'completed' && job.status !== 'failed' && (
            <p className="text-sm text-gray-400 animate-pulse">Running on {job.target_devices.length} device(s)…</p>
          )}
          {job.results.map((r) => (
            <div key={r.id} className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs font-medium">{deviceMap[r.device_id] ?? r.device_id.slice(0, 8)}</span>
                <span className={`px-1.5 py-0.5 rounded text-xs ${r.exit_status === 'success' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>{r.exit_status}</span>
                {r.duration_ms && <span className="text-xs text-gray-400">{r.duration_ms}ms</span>}
              </div>
              <pre className="bg-gray-900 text-green-400 text-xs rounded p-3 overflow-x-auto max-h-60 overflow-y-auto">{r.output ?? '(no output)'}</pre>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
