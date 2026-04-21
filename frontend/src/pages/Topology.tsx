import { useEffect, useRef, useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { fetchTopology, discoverTopology } from '../api/devices'
import type { TopologyNode } from '../types/device'
import cytoscape from 'cytoscape'
import dagre from 'cytoscape-dagre'
import toast from 'react-hot-toast'
import { RefreshCw } from 'lucide-react'

cytoscape.use(dagre)

const PLATFORM_COLORS: Record<string, string> = {
  junos: '#22c55e',
  cisco_ios: '#3b82f6',
  cisco_xe: '#6366f1',
}

export default function Topology() {
  const containerRef = useRef<HTMLDivElement>(null)
  const cyRef = useRef<cytoscape.Core | null>(null)
  const [selected, setSelected] = useState<TopologyNode | null>(null)

  const { data, isLoading, refetch } = useQuery({ queryKey: ['topology'], queryFn: fetchTopology })
  const discoverMut = useMutation({ mutationFn: discoverTopology, onSuccess: () => { toast.success('Discovery queued'); setTimeout(() => refetch(), 5000) } })

  useEffect(() => {
    if (!data || !containerRef.current) return
    cyRef.current?.destroy()

    const elements = [
      ...data.nodes.map((n) => ({
        data: {
          id: n.id,
          label: n.hostname,
          platform: n.platform,
          status: n.status,
          ip_address: n.ip_address,
          model: n.model,
          site: n.site,
          hostname: n.hostname,
        },
      })),
      ...data.edges.map((e, i) => ({
        data: {
          id: `e${i}`,
          source: e.source,
          target: e.target,
          source_interface: e.source_interface,
          target_interface: e.target_interface,
        },
      })),
    ]

    const cy = cytoscape({
      container: containerRef.current,
      elements,
      style: [
        {
          selector: 'node',
          style: {
            label: 'data(label)',
            'background-color': (ele: any) => PLATFORM_COLORS[ele.data('platform')] ?? '#94a3b8',
            'border-color': (ele: any) => ele.data('status') === 'unreachable' ? '#ef4444' : '#fff',
            'border-width': 3,
            color: '#fff',
            'text-valign': 'bottom',
            'text-margin-y': 6,
            'font-size': 11,
            width: 40,
            height: 40,
          },
        },
        {
          selector: 'edge',
          style: {
            width: 2,
            'line-color': '#94a3b8',
            'target-arrow-color': '#94a3b8',
            'curve-style': 'bezier',
          },
        },
        {
          selector: 'node:selected',
          style: { 'border-color': '#f59e0b', 'border-width': 4 },
        },
      ],
      layout: { name: 'dagre', rankDir: 'TB' } as any,
    })

    cy.on('tap', 'node', (evt) => setSelected(evt.target.data()))
    cy.on('tap', (evt) => { if (evt.target === cy) setSelected(null) })
    cyRef.current = cy
    return () => cy.destroy()
  }, [data])

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800">Network Topology</h1>
        <div className="flex gap-2">
          <button onClick={() => discoverMut.mutate()} className="flex items-center gap-2 border px-4 py-2 rounded-lg text-sm hover:bg-gray-50">
            <RefreshCw size={15} /> Discover Neighbors
          </button>
        </div>
      </div>

      <div className="flex gap-3 text-xs">
        {Object.entries(PLATFORM_COLORS).map(([p, c]) => (
          <span key={p} className="flex items-center gap-1">
            <span className="w-3 h-3 rounded-full inline-block" style={{ backgroundColor: c }} />
            {p}
          </span>
        ))}
      </div>

      <div className="relative bg-white rounded-xl shadow overflow-hidden" style={{ height: 540 }}>
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center text-gray-400">Loading topology…</div>
        )}
        {!isLoading && data?.nodes.length === 0 && (
          <div className="absolute inset-0 flex items-center justify-center text-gray-400">No devices. Add devices in Inventory first.</div>
        )}
        <div ref={containerRef} className="w-full h-full" />
      </div>

      {selected && (
        <div className="bg-white rounded-xl shadow p-4 text-sm grid grid-cols-3 gap-2">
          <div><span className="text-gray-500">Hostname</span><p className="font-mono font-medium">{selected.hostname}</p></div>
          <div><span className="text-gray-500">IP</span><p>{selected.ip_address}</p></div>
          <div><span className="text-gray-500">Platform</span><p>{selected.platform}</p></div>
          <div><span className="text-gray-500">Status</span><p>{selected.status}</p></div>
          <div><span className="text-gray-500">Model</span><p>{selected.model ?? '—'}</p></div>
          <div><span className="text-gray-500">Site</span><p>{selected.site ?? '—'}</p></div>
        </div>
      )}
    </div>
  )
}
