import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchDevices, createDevice, updateDevice, deleteDevice, syncDevice, discoverDevices } from '../api/devices'
import type { Device, DeviceCreate } from '../types/device'
import toast from 'react-hot-toast'
import { Plus, RefreshCw, Trash2, Radar, Loader2, Pencil } from 'lucide-react'

const PLATFORMS = ['junos', 'cisco_ios', 'cisco_xe', 'openwrt']

const PLATFORM_COLORS: Record<string, string> = {
  junos:      'bg-green-100 text-green-700',
  cisco_ios:  'bg-blue-100 text-blue-700',
  cisco_xe:   'bg-violet-100 text-violet-700',
  openwrt:    'bg-orange-100 text-orange-700',
}

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

const PREFIX_OPTIONS = [
  { prefix: 24, hosts: 254,   label: '/24 — 254 hosts' },
  { prefix: 25, hosts: 126,   label: '/25 — 126 hosts' },
  { prefix: 26, hosts: 62,    label: '/26 — 62 hosts' },
  { prefix: 27, hosts: 30,    label: '/27 — 30 hosts' },
  { prefix: 28, hosts: 14,    label: '/28 — 14 hosts' },
  { prefix: 23, hosts: 510,   label: '/23 — 510 hosts' },
  { prefix: 22, hosts: 1022,  label: '/22 — 1022 hosts' },
  { prefix: 21, hosts: 2046,  label: '/21 — 2046 hosts' },
  { prefix: 20, hosts: 4094,  label: '/20 — 4094 hosts' },
  { prefix: 16, hosts: 65534, label: '/16 — 65534 hosts' },
]

function buildCidr(network: string, prefix: number): string {
  // Zero out host bits for the given prefix length
  const parts = network.split('.').map(Number)
  if (parts.length !== 4 || parts.some(isNaN)) return `${network}/${prefix}`
  const addr = (parts[0] << 24) | (parts[1] << 16) | (parts[2] << 8) | parts[3]
  const mask = prefix === 0 ? 0 : (~0 << (32 - prefix)) >>> 0
  const net = (addr & mask) >>> 0
  return `${(net >>> 24) & 0xff}.${(net >>> 16) & 0xff}.${(net >>> 8) & 0xff}.${net & 0xff}/${prefix}`
}

function DiscoverForm({ onClose, onStarted }: { onClose: () => void; onStarted: () => void }) {
  const [network, setNetwork] = useState('192.168.0.0')
  const [prefix, setPrefix] = useState(24)
  const [creds, setCreds] = useState({
    username: '', password: '', enable_secret: '',
    snmp_community: 'public', snmp_version: 'v2c',
  })

  const cidr = buildCidr(network, prefix)
  const hostCount = PREFIX_OPTIONS.find(o => o.prefix === prefix)?.hosts ?? 0
  const isLarge = hostCount > 1000

  const setCred = (k: keyof typeof creds) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setCreds(prev => ({ ...prev, [k]: e.target.value }))

  const mutation = useMutation({
    mutationFn: discoverDevices,
    onSuccess: () => { toast.success('Network scan started — devices will appear as found'); onStarted(); onClose() },
    onError: () => toast.error('Failed to start scan'),
  })

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6 space-y-4">
        <div>
          <h2 className="text-lg font-semibold">Network Discovery</h2>
          <p className="text-xs text-gray-400 mt-0.5">Scan a subnet and auto-add reachable devices via SSH</p>
        </div>

        {/* CIDR builder */}
        <div>
          <label className="block text-xs text-gray-500 mb-1">Subnet</label>
          <div className="flex gap-2 items-center">
            <input
              value={network}
              onChange={e => setNetwork(e.target.value)}
              placeholder="192.168.254.0"
              className="flex-1 border rounded px-3 py-1.5 text-sm font-mono"
            />
            <select
              value={prefix}
              onChange={e => setPrefix(Number(e.target.value))}
              className="border rounded px-2 py-1.5 text-sm font-mono"
            >
              {PREFIX_OPTIONS.map(o => (
                <option key={o.prefix} value={o.prefix}>{o.label}</option>
              ))}
            </select>
          </div>
          <div className="flex items-center justify-between mt-1.5">
            <span className="font-mono text-xs text-indigo-600">{cidr}</span>
            {isLarge && (
              <span className="text-xs text-amber-600 font-medium">⚠ Large scan — may take a while</span>
            )}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          {([['username', 'Username'], ['password', 'Password'], ['enable_secret', 'Enable Secret (opt.)'], ['snmp_community', 'SNMP Community']] as const).map(([k, label]) => (
            <div key={k}>
              <label className="block text-xs text-gray-500 mb-1">{label}</label>
              <input type={k === 'password' || k === 'enable_secret' ? 'password' : 'text'}
                value={creds[k]} onChange={setCred(k)}
                className="w-full border rounded px-3 py-1.5 text-sm" />
            </div>
          ))}
          <div>
            <label className="block text-xs text-gray-500 mb-1">SNMP Version</label>
            <select value={creds.snmp_version} onChange={setCred('snmp_version')} className="w-full border rounded px-3 py-1.5 text-sm">
              <option value="v2c">v2c</option>
              <option value="v3">v3</option>
            </select>
          </div>
        </div>

        <div className="flex gap-2 pt-1">
          <button onClick={onClose} className="flex-1 border rounded px-4 py-2 text-sm">Cancel</button>
          <button
            onClick={() => mutation.mutate({ ...creds, cidr })}
            disabled={mutation.isPending || !network || !creds.username}
            className="flex-1 bg-indigo-600 text-white rounded px-4 py-2 text-sm disabled:opacity-60 flex items-center justify-center gap-2"
          >
            {mutation.isPending ? <><Loader2 size={14} className="animate-spin" /> Starting…</> : <><Radar size={14} /> Start Scan</>}
          </button>
        </div>
      </div>
    </div>
  )
}

function EditDeviceForm({ device, onClose }: { device: Device; onClose: () => void }) {
  const qc = useQueryClient()
  const [form, setForm] = useState({
    hostname: device.hostname,
    ip_address: device.ip_address,
    username: device.username,
    password: '',
    enable_secret: '',
    snmp_community: '',
    platform: device.platform,
    site: device.site ?? '',
  })
  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm(prev => ({ ...prev, [k]: e.target.value }))

  const mutation = useMutation({
    mutationFn: (data: typeof form) => {
      const body: Record<string, string> = {}
      if (data.hostname !== device.hostname) body.hostname = data.hostname
      if (data.ip_address !== device.ip_address) body.ip_address = data.ip_address
      if (data.username !== device.username) body.username = data.username
      if (data.password) body.password = data.password
      if (data.enable_secret) body.enable_secret = data.enable_secret
      if (data.snmp_community) body.snmp_community = data.snmp_community
      if (data.platform !== device.platform) body.platform = data.platform
      if (data.site !== (device.site ?? '')) body.site = data.site
      return updateDevice(device.id, body)
    },
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['devices'] }); toast.success('Device updated'); onClose() },
    onError: () => toast.error('Update failed'),
  })

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6 space-y-4">
        <h2 className="text-lg font-semibold">Edit Device — {device.hostname}</h2>

        <div className="grid grid-cols-2 gap-3">
          {([['hostname', 'Hostname'], ['ip_address', 'IP Address'], ['username', 'Username'], ['site', 'Site (opt.)']] as const).map(([k, label]) => (
            <div key={k}>
              <label className="block text-xs text-gray-500 mb-1">{label}</label>
              <input value={form[k]} onChange={set(k)} className="w-full border rounded px-3 py-1.5 text-sm" />
            </div>
          ))}
        </div>

        <div className="border-t pt-3">
          <p className="text-xs text-gray-400 mb-2">Leave blank to keep existing credentials</p>
          <div className="grid grid-cols-2 gap-3">
            {([['password', 'Password'], ['enable_secret', 'Enable Secret'], ['snmp_community', 'SNMP Community']] as const).map(([k, label]) => (
              <div key={k}>
                <label className="block text-xs text-gray-500 mb-1">{label}</label>
                <input type="password" placeholder="(unchanged)" value={form[k]} onChange={set(k)}
                  className="w-full border rounded px-3 py-1.5 text-sm" />
              </div>
            ))}
            <div>
              <label className="block text-xs text-gray-500 mb-1">Platform</label>
              <select value={form.platform} onChange={set('platform')} className="w-full border rounded px-3 py-1.5 text-sm">
                {PLATFORMS.map(p => <option key={p}>{p}</option>)}
              </select>
            </div>
          </div>
        </div>

        <div className="flex gap-2 pt-1">
          <button onClick={onClose} className="flex-1 border rounded px-4 py-2 text-sm">Cancel</button>
          <button
            onClick={() => mutation.mutate(form)}
            disabled={mutation.isPending}
            className="flex-1 bg-blue-600 text-white rounded px-4 py-2 text-sm disabled:opacity-60 flex items-center justify-center gap-2"
          >
            {mutation.isPending ? <><Loader2 size={14} className="animate-spin" /> Saving…</> : 'Save Changes'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default function Inventory() {
  const qc = useQueryClient()
  const [showForm, setShowForm] = useState(false)
  const [showDiscover, setShowDiscover] = useState(false)
  const [scanning, setScanning] = useState(false)
  const [editDevice, setEditDevice] = useState<Device | null>(null)
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
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Device Inventory</h1>
          {scanning && <p className="text-xs text-indigo-500 mt-0.5 animate-pulse">Scanning network…</p>}
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setShowDiscover(true)}
            className="flex items-center gap-2 bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm"
          >
            <Radar size={16} /> Discover Network
          </button>
          <button onClick={() => setShowForm(true)} className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm">
            <Plus size={16} /> Add Device
          </button>
        </div>
      </div>

      {showForm && <DeviceForm onClose={() => setShowForm(false)} />}
      {showDiscover && (
        <DiscoverForm
          onClose={() => setShowDiscover(false)}
          onStarted={() => {
            setScanning(true)
            const poll = setInterval(() => qc.invalidateQueries({ queryKey: ['devices'] }), 4000)
            setTimeout(() => { clearInterval(poll); setScanning(false); qc.invalidateQueries({ queryKey: ['devices'] }) }, 120000)
          }}
        />
      )}
      {editDevice && <EditDeviceForm device={editDevice} onClose={() => setEditDevice(null)} />}

      <div className="bg-white rounded-xl shadow overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-gray-600 text-xs uppercase">
            <tr>
              {['Hostname', 'IP Address', 'Platform', 'Status', 'Model', 'Last Seen', 'Actions'].map((h) => (
                <th key={h} className="px-3 py-3 text-left">{h}</th>
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
                <td className="px-3 py-3 font-mono font-medium">{d.hostname}</td>
                <td className="px-3 py-3 text-gray-600">{d.ip_address}</td>
                <td className="px-3 py-3">
                  <span className={`px-2 py-0.5 rounded text-xs font-medium ${PLATFORM_COLORS[d.platform] ?? 'bg-gray-100 text-gray-600'}`}>
                    {d.platform}
                  </span>
                </td>
                <td className="px-3 py-3">
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                    d.status === 'reachable' ? 'bg-green-100 text-green-700'
                    : d.status === 'unreachable' ? 'bg-red-100 text-red-700'
                    : 'bg-gray-100 text-gray-500'
                  }`}>{d.status}</span>
                </td>
                <td className="px-3 py-3 text-gray-500">{d.model ?? '—'}</td>
                <td className="px-3 py-3 text-gray-400 text-xs">{d.last_seen ? new Date(d.last_seen).toLocaleString() : '—'}</td>
                <td className="px-3 py-3">
                  <div className="flex gap-2">
                    <button onClick={() => syncMut.mutate(d.id)} className="text-blue-500 hover:text-blue-700" title="Sync facts">
                      <RefreshCw size={15} />
                    </button>
                    <button onClick={() => setEditDevice(d)} className="text-gray-400 hover:text-gray-600" title="Edit device">
                      <Pencil size={15} />
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
