import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchAlerts, acknowledgeAlert, resolveAlert, fetchAlertRules, createAlertRule, deleteAlertRule } from '../api/alerts'
import type { Alert, AlertRule } from '../types/command'
import toast from 'react-hot-toast'
import { Plus, Check, X } from 'lucide-react'

const SEVERITY_COLORS: Record<string, string> = {
  critical: 'bg-red-100 text-red-700',
  warning: 'bg-orange-100 text-orange-700',
  info: 'bg-blue-100 text-blue-700',
}

const STATE_COLORS: Record<string, string> = {
  open: 'bg-red-50 text-red-600',
  acknowledged: 'bg-yellow-50 text-yellow-600',
  resolved: 'bg-green-50 text-green-600',
}

function RuleForm({ onClose }: { onClose: () => void }) {
  const qc = useQueryClient()
  const [form, setForm] = useState({ name: '', metric: 'cpu_percent', operator: 'gt', threshold: '80', severity: 'warning' })
  const mut = useMutation({
    mutationFn: createAlertRule,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['rules'] }); toast.success('Rule created'); onClose() },
  })
  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6 space-y-3">
        <h2 className="text-lg font-semibold">New Alert Rule</h2>
        {(['name', 'metric', 'threshold'] as const).map((f) => (
          <div key={f}>
            <label className="block text-xs text-gray-500 mb-1 capitalize">{f}</label>
            <input value={(form as any)[f]} onChange={(e) => setForm((p) => ({ ...p, [f]: e.target.value }))} className="w-full border rounded px-3 py-1.5 text-sm" />
          </div>
        ))}
        <div>
          <label className="block text-xs text-gray-500 mb-1">Operator</label>
          <select value={form.operator} onChange={(e) => setForm((p) => ({ ...p, operator: e.target.value }))} className="w-full border rounded px-3 py-1.5 text-sm">
            {['gt', 'gte', 'lt', 'lte'].map((o) => <option key={o}>{o}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">Severity</label>
          <select value={form.severity} onChange={(e) => setForm((p) => ({ ...p, severity: e.target.value }))} className="w-full border rounded px-3 py-1.5 text-sm">
            {['info', 'warning', 'critical'].map((s) => <option key={s}>{s}</option>)}
          </select>
        </div>
        <div className="flex gap-2 pt-1">
          <button onClick={onClose} className="flex-1 border rounded px-4 py-2 text-sm">Cancel</button>
          <button onClick={() => mut.mutate({ ...form, threshold: Number(form.threshold) } as any)} className="flex-1 bg-blue-600 text-white rounded px-4 py-2 text-sm">
            Create
          </button>
        </div>
      </div>
    </div>
  )
}

export default function Alerts() {
  const qc = useQueryClient()
  const [tab, setTab] = useState<'alerts' | 'rules'>('alerts')
  const [showForm, setShowForm] = useState(false)

  const { data: alerts = [] } = useQuery({ queryKey: ['alerts'], queryFn: () => fetchAlerts() })
  const { data: rules = [] } = useQuery({ queryKey: ['rules'], queryFn: fetchAlertRules })

  const ackMut = useMutation({ mutationFn: acknowledgeAlert, onSuccess: () => qc.invalidateQueries({ queryKey: ['alerts'] }) })
  const resolMut = useMutation({ mutationFn: resolveAlert, onSuccess: () => qc.invalidateQueries({ queryKey: ['alerts'] }) })
  const delRuleMut = useMutation({ mutationFn: deleteAlertRule, onSuccess: () => qc.invalidateQueries({ queryKey: ['rules'] }) })

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800">Alerts</h1>
        <button onClick={() => setShowForm(true)} className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm">
          <Plus size={15} /> New Rule
        </button>
      </div>
      {showForm && <RuleForm onClose={() => setShowForm(false)} />}

      <div className="flex gap-2">
        {(['alerts', 'rules'] as const).map((t) => (
          <button key={t} onClick={() => setTab(t)} className={`px-4 py-1.5 rounded-full text-sm capitalize ${tab === t ? 'bg-blue-600 text-white' : 'bg-white border text-gray-600 hover:bg-gray-50'}`}>{t}</button>
        ))}
      </div>

      {tab === 'alerts' && (
        <div className="bg-white rounded-xl shadow overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-gray-500 text-xs uppercase">
              <tr>{['Severity', 'Device', 'Metric', 'Value', 'State', 'Triggered', 'Actions'].map((h) => <th key={h} className="px-4 py-3 text-left">{h}</th>)}</tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {alerts.length === 0 ? (
                <tr><td colSpan={7} className="text-center py-8 text-gray-400">No alerts.</td></tr>
              ) : alerts.map((a: Alert) => (
                <tr key={a.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3"><span className={`px-2 py-0.5 rounded text-xs font-medium ${SEVERITY_COLORS[a.severity]}`}>{a.severity}</span></td>
                  <td className="px-4 py-3 font-mono text-xs">{a.device_id.slice(0, 8)}</td>
                  <td className="px-4 py-3 font-mono text-xs">{a.metric}</td>
                  <td className="px-4 py-3">{a.value.toFixed(1)}</td>
                  <td className="px-4 py-3"><span className={`px-2 py-0.5 rounded text-xs ${STATE_COLORS[a.state]}`}>{a.state}</span></td>
                  <td className="px-4 py-3 text-xs text-gray-400">{new Date(a.triggered_at + 'Z').toLocaleString()}</td>
                  <td className="px-4 py-3">
                    <div className="flex gap-1">
                      {a.state === 'open' && <button onClick={() => ackMut.mutate(a.id)} title="Acknowledge" className="text-yellow-500 hover:text-yellow-700"><Check size={15} /></button>}
                      {a.state !== 'resolved' && <button onClick={() => resolMut.mutate(a.id)} title="Resolve" className="text-green-500 hover:text-green-700"><X size={15} /></button>}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {tab === 'rules' && (
        <div className="bg-white rounded-xl shadow overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-gray-500 text-xs uppercase">
              <tr>{['Name', 'Metric', 'Condition', 'Severity', 'Enabled', 'Actions'].map((h) => <th key={h} className="px-4 py-3 text-left">{h}</th>)}</tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {rules.length === 0 ? (
                <tr><td colSpan={6} className="text-center py-8 text-gray-400">No rules. Create one above.</td></tr>
              ) : rules.map((r: AlertRule) => (
                <tr key={r.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium">{r.name}</td>
                  <td className="px-4 py-3 font-mono text-xs">{r.metric}</td>
                  <td className="px-4 py-3 font-mono text-xs">{r.operator} {r.threshold}</td>
                  <td className="px-4 py-3"><span className={`px-2 py-0.5 rounded text-xs font-medium ${SEVERITY_COLORS[r.severity]}`}>{r.severity}</span></td>
                  <td className="px-4 py-3"><span className={`w-2 h-2 rounded-full inline-block ${r.enabled ? 'bg-green-500' : 'bg-gray-300'}`} /></td>
                  <td className="px-4 py-3">
                    <button onClick={() => delRuleMut.mutate(r.id)} className="text-red-400 hover:text-red-600"><X size={15} /></button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
