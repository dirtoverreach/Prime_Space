import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchDevices, createDevice, deleteDevice, syncDevice } from '../api/devices'
import type { Device, DeviceCreate } from '../types/device'
import toast from 'react-hot-toast'
import { Plus, RefreshCw, Trash2 } from 'lucide-react'

const PLATFORMS = ['junos', 'cisco_ios', 'cisco_xe']

function DeviceForm({ onClose }: { onClose: () => void }) {
  const qc = useQueryClient()
  const [form, setForm] = useState<DeviceCreate>({
    hostname: '', ip_address: '', platform: 'cisco_ios', username: '',
    password: '', snmp_community: 'public', snmp_version: 'v2c',
  })
  const mutation = useMutation({
    mutationFn: createDevice,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['devices'] }); toast.success('Device added'); onClose() },
  })
  const set = (k: keyof DeviceCreate) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm((prev) => ({ ...prev, [k]: e.target.value }))

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6 space-y-4">
        <h2 className="text-lg font-semibold">Add Device</h2>
        {(['hostname', 'ip_address', 'username', 'password', 'snmp_community'] as const).map((f) => (
          <div key={f}>
            <label className="block text-xs text-gray-500 mb-1 capitalize">{f.replace('_', ' ')}</label>
            <input
              type={f === 'password' ? 'password' : 'text'}
              value={form[f] ?? ''}
              onChange={set(f)}
              className="w-full border rounded px-3 py-1.5 text-sm"
            />
          </div>
        ))}
        <div>
          <label className="block text-xs text-gray-500 mb-1">Platform</label>
          <select value={form.platform} onChange={set('platform')} className="w-full border rounded px-3 py-1.5 text-sm">
            {PLATFORMS.map((p) => <option key={p}>{p}</option>)}
          </select>
        </div>
        <div className="flex gap-2 pt-2">
          <button onClick={onClose} className="flex-1 border rounded px-4 py-2 text-sm">Cancel</button>
          <button
            onClick={() => mutation.mutate(form)}
            disabled={mutation.isPending}
            className="flex-1 bg-blue-600 text-white rounded px-4 py-2 text-sm"
          >
            {mutation.isPending ? 'Adding…' : 'Add Device'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default function Inventory() {
  const qc = useQueryClient()
  const [showForm, setShowForm] = useState(false)
  const { data: devices = [], isLoading } = useQuery({ queryKey: ['devices'], queryFn: () => fetchDevices() })

  const deleteMut = useMutation({
    mutationFn: deleteDevice,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['devices'] }),
  })
  const syncMut = useMutation({
    mutationFn: syncDevice,
    onSuccess: () => toast.success('Sync queued'),
  })

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800">Device Inventory</h1>
        <button onClick={() => setShowForm(true)} className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm">
          <Plus size={16} /> Add Device
        </button>
      </div>

      {showForm && <DeviceForm onClose={() => setShowForm(false)} />}

      <div className="bg-white rounded-xl shadow overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-gray-600 text-xs uppercase">
            <tr>
              {['Hostname', 'IP Address', 'Platform', 'Status', 'Model', 'Last Seen', 'Actions'].map((h) => (
                <th key={h} className="px-4 py-3 text-left">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {isLoading ? (
              <tr><td colSpan={7} className="text-center py-8 text-gray-400">Loading…</td></tr>
            ) : devices.length === 0 ? (
              <tr><td colSpan={7} className="text-center py-8 text-gray-400">No devices yet. Add one above.</td></tr>
            ) : devices.map((d: Device) => (
              <tr key={d.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 font-mono font-medium">{d.hostname}</td>
                <td className="px-4 py-3 text-gray-600">{d.ip_address}</td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                    d.platform === 'junos' ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'
                  }`}>{d.platform}</span>
                </td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                    d.status === 'reachable' ? 'bg-green-100 text-green-700'
                    : d.status === 'unreachable' ? 'bg-red-100 text-red-700'
                    : 'bg-gray-100 text-gray-500'
                  }`}>{d.status}</span>
                </td>
                <td className="px-4 py-3 text-gray-500">{d.model ?? '—'}</td>
                <td className="px-4 py-3 text-gray-400 text-xs">{d.last_seen ? new Date(d.last_seen).toLocaleString() : '—'}</td>
                <td className="px-4 py-3">
                  <div className="flex gap-2">
                    <button onClick={() => syncMut.mutate(d.id)} className="text-blue-500 hover:text-blue-700" title="Sync facts">
                      <RefreshCw size={15} />
                    </button>
                    <button onClick={() => { if (confirm(`Delete ${d.hostname}?`)) deleteMut.mutate(d.id) }} className="text-red-400 hover:text-red-600" title="Delete">
                      <Trash2 size={15} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
