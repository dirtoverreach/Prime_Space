import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchDevices } from '../api/devices'
import { fetchBackups, triggerBackup, diffBackups, diffLive } from '../api/configs'
import DiffViewer from '../components/config/DiffViewer'
import toast from 'react-hot-toast'
import { Download, GitCompare, Trash2 } from 'lucide-react'

export default function ConfigManager() {
  const qc = useQueryClient()
  const [selectedDevice, setSelectedDevice] = useState<string>('')
  const [selectedA, setSelectedA] = useState<string>('')
  const [selectedB, setSelectedB] = useState<string>('')
  const [diffResult, setDiffResult] = useState<{ unified_diff: string } | null>(null)

  const { data: devices = [] } = useQuery({ queryKey: ['devices'], queryFn: () => fetchDevices() })
  const { data: backups = [] } = useQuery({
    queryKey: ['backups', selectedDevice],
    queryFn: () => fetchBackups(selectedDevice || undefined),
    enabled: true,
  })

  const backupMut = useMutation({
    mutationFn: ({ device_id }: { device_id: string }) => triggerBackup(device_id),
    onSuccess: () => { toast.success('Backup queued'); qc.invalidateQueries({ queryKey: ['backups'] }) },
  })

  const diffMut = useMutation({
    mutationFn: ({ a, b }: { a: string; b: string }) => diffBackups(a, b),
    onSuccess: (data) => setDiffResult(data),
  })

  const liveDiffMut = useMutation({
    mutationFn: (device_id: string) => diffLive(device_id),
    onSuccess: (data) => setDiffResult(data),
  })

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-gray-800">Configuration Manager</h1>

      <div className="bg-white rounded-xl shadow p-4 flex flex-wrap gap-3 items-end">
        <div>
          <label className="block text-xs text-gray-500 mb-1">Filter by Device</label>
          <select
            value={selectedDevice}
            onChange={(e) => setSelectedDevice(e.target.value)}
            className="border rounded px-3 py-1.5 text-sm"
          >
            <option value="">All Devices</option>
            {devices.map((d) => <option key={d.id} value={d.id}>{d.hostname}</option>)}
          </select>
        </div>
        {selectedDevice && (
          <>
            <button
              onClick={() => backupMut.mutate({ device_id: selectedDevice })}
              className="flex items-center gap-2 bg-blue-600 text-white px-3 py-1.5 rounded text-sm"
            >
              <Download size={14} /> Pull Backup
            </button>
            <button
              onClick={() => liveDiffMut.mutate(selectedDevice)}
              className="flex items-center gap-2 border px-3 py-1.5 rounded text-sm hover:bg-gray-50"
            >
              <GitCompare size={14} /> Diff vs Live
            </button>
          </>
        )}
      </div>

      <div className="bg-white rounded-xl shadow overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-gray-500 text-xs uppercase">
            <tr>
              {['Device', 'Source', 'Checksum', 'Label', 'Date', 'Compare'].map((h) => (
                <th key={h} className="px-4 py-3 text-left">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {backups.length === 0 ? (
              <tr><td colSpan={6} className="text-center py-8 text-gray-400">No backups yet.</td></tr>
            ) : backups.map((b) => {
              const device = devices.find((d) => d.id === b.device_id)
              return (
                <tr key={b.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-mono text-xs">{device?.hostname ?? b.device_id.slice(0, 8)}</td>
                  <td className="px-4 py-3"><span className="bg-gray-100 px-2 py-0.5 rounded text-xs">{b.source}</span></td>
                  <td className="px-4 py-3 font-mono text-xs text-gray-400">{b.checksum.slice(0, 12)}…</td>
                  <td className="px-4 py-3 text-xs text-gray-500">{b.label ?? '—'}</td>
                  <td className="px-4 py-3 text-xs text-gray-400">{new Date(b.created_at).toLocaleString()}</td>
                  <td className="px-4 py-3">
                    <div className="flex gap-1">
                      <button
                        className={`px-2 py-0.5 text-xs rounded border ${selectedA === b.id ? 'bg-blue-100 border-blue-400' : 'hover:bg-gray-100'}`}
                        onClick={() => setSelectedA(b.id)}
                      >A</button>
                      <button
                        className={`px-2 py-0.5 text-xs rounded border ${selectedB === b.id ? 'bg-green-100 border-green-400' : 'hover:bg-gray-100'}`}
                        onClick={() => setSelectedB(b.id)}
                      >B</button>
                    </div>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {selectedA && selectedB && selectedA !== selectedB && (
        <button
          onClick={() => diffMut.mutate({ a: selectedA, b: selectedB })}
          className="flex items-center gap-2 bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm"
        >
          <GitCompare size={15} /> Compare Selected (A vs B)
        </button>
      )}

      {diffResult && <DiffViewer diff={diffResult.unified_diff} />}
    </div>
  )
}
