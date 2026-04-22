import { useEffect, useRef, useState, useCallback } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { fetchTopology, discoverTopology } from '../api/devices'
import type { TopologyNode } from '../types/device'
import cytoscape from 'cytoscape'
import dagre from 'cytoscape-dagre'
import toast from 'react-hot-toast'
import { RefreshCw, ZoomIn, ZoomOut, Maximize2, Loader2 } from 'lucide-react'

cytoscape.use(dagre)

const PLATFORM_COLORS: Record<string, string> = {
  junos:      '#16a34a',
  cisco_ios:  '#2563eb',
  cisco_xe:   '#7c3aed',
  openwrt:    '#ea580c',
}

const PLATFORM_LABELS: Record<string, string> = {
  junos:      'Juniper',
  cisco_ios:  'Cisco IOS',
  cisco_xe:   'Cisco IOS-XE',
  openwrt:    'OpenWrt',
}

const STATUS_BORDER: Record<string, string> = {
  reachable:   '#22c55e',
  unreachable: '#ef4444',
  unknown:     '#94a3b8',
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function buildStyle(): any[] {
  return [
    {
      selector: 'node',
      style: {
        shape: 'round-rectangle',
        label: 'data(label)',
        'background-color': 'data(color)',
        'border-color': 'data(borderColor)',
        'border-width': 3,
        color: '#fff',
        'text-valign': 'bottom',
        'text-halign': 'center',
        'text-margin-y': 8,
        'font-size': 11,
        'font-weight': 'bold',
        'text-background-color': '#1e293b',
        'text-background-opacity': 0.75,
        'text-background-padding': '3px',
        'text-background-shape': 'roundrectangle',
        width: 52,
        height: 52,
      } as any,
    },
    {
      selector: 'edge',
      style: {
        width: 2,
        'line-color': '#64748b',
        'target-arrow-shape': 'none',
        'curve-style': 'bezier',
        label: 'data(label)',
        'font-size': 9,
        color: '#64748b',
        'text-rotation': 'autorotate',
        'text-background-color': '#f8fafc',
        'text-background-opacity': 1,
        'text-background-padding': '2px',
      } as any,
    },
    {
      selector: 'node:selected',
      style: {
        'border-color': '#f59e0b',
        'border-width': 5,
        'box-shadow-blur': 12,
        'box-shadow-color': '#f59e0b',
        'box-shadow-opacity': 0.6,
        'box-shadow-offset-x': 0,
        'box-shadow-offset-y': 0,
      } as any,
    },
    {
      selector: 'edge:selected',
      style: { 'line-color': '#f59e0b', width: 3 } as any,
    },
    {
      selector: 'node.faded',
      style: { opacity: 0.25 } as any,
    },
    {
      selector: 'edge.faded',
      style: { opacity: 0.1 } as any,
    },
  ]
}

export default function Topology() {
  const containerRef = useRef<HTMLDivElement>(null)
  const cyRef = useRef<cytoscape.Core | null>(null)
  const [selected, setSelected] = useState<TopologyNode | null>(null)
  const [discovering, setDiscovering] = useState(false)

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['topology'],
    queryFn: fetchTopology,
    refetchInterval: discovering ? 3000 : false,
  })

  const discoverMut = useMutation({
    mutationFn: discoverTopology,
    onSuccess: () => {
      toast.success('Neighbor discovery running…')
      setDiscovering(true)
      setTimeout(() => { setDiscovering(false); refetch() }, 15000)
    },
  })

  const fitGraph = useCallback(() => cyRef.current?.fit(undefined, 40), [])
  const zoomIn  = useCallback(() => { const cy = cyRef.current; if (cy) cy.zoom(cy.zoom() * 1.3) }, [])
  const zoomOut = useCallback(() => { const cy = cyRef.current; if (cy) cy.zoom(cy.zoom() * 0.77) }, [])

  useEffect(() => {
    if (!data || !containerRef.current) return
    cyRef.current?.destroy()

    const elements: cytoscape.ElementDefinition[] = [
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
          color: PLATFORM_COLORS[n.platform] ?? '#64748b',
          borderColor: STATUS_BORDER[n.status] ?? '#94a3b8',
        },
      })),
      ...data.edges.map((e, i) => ({
        data: {
          id: `e${i}`,
          source: e.source,
          target: e.target,
          source_interface: e.source_interface,
          target_interface: e.target_interface,
          label: e.source_interface && e.target_interface
            ? `${e.source_interface} ↔ ${e.target_interface}`
            : '',
        },
      })),
    ]

    const cy = cytoscape({
      container: containerRef.current,
      elements,
      style: buildStyle(),
      layout: {
        name: 'dagre',
        rankDir: 'TB',
        nodeSep: 80,
        rankSep: 120,
        padding: 40,
      } as any,
      minZoom: 0.2,
      maxZoom: 4,
    })

    cy.on('tap', 'node', (evt) => {
      const node = evt.target
      setSelected(node.data())
      cy.elements().addClass('faded')
      node.removeClass('faded')
      node.connectedEdges().removeClass('faded').connectedNodes().removeClass('faded')
    })

    cy.on('tap', (evt) => {
      if (evt.target === cy) {
        setSelected(null)
        cy.elements().removeClass('faded')
      }
    })

    cyRef.current = cy
    return () => cy.destroy()
  }, [data])

  const nodeCount = data?.nodes.length ?? 0
  const edgeCount = data?.edges.length ?? 0

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Network Topology</h1>
          {nodeCount > 0 && (
            <p className="text-xs text-gray-400 mt-0.5">{nodeCount} devices · {edgeCount} links</p>
          )}
        </div>
        <button
          onClick={() => discoverMut.mutate()}
          disabled={discoverMut.isPending || discovering}
          className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm disabled:opacity-60"
        >
          {discovering
            ? <><Loader2 size={15} className="animate-spin" /> Discovering…</>
            : <><RefreshCw size={15} /> Discover Neighbors</>
          }
        </button>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-4 text-xs">
        {Object.entries(PLATFORM_LABELS).map(([p, label]) => (
          <span key={p} className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded inline-block" style={{ backgroundColor: PLATFORM_COLORS[p] }} />
            {label}
          </span>
        ))}
        <span className="ml-4 flex items-center gap-1.5 text-gray-400">
          <span className="w-3 h-3 rounded-full border-2 border-green-500 inline-block" />reachable
        </span>
        <span className="flex items-center gap-1.5 text-gray-400">
          <span className="w-3 h-3 rounded-full border-2 border-red-500 inline-block" />unreachable
        </span>
      </div>

      {/* Graph canvas */}
      <div className="relative bg-gray-950 rounded-xl shadow overflow-hidden" style={{ height: 580 }}>
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center text-gray-400">
            <Loader2 className="animate-spin mr-2" size={18} /> Loading topology…
          </div>
        )}
        {!isLoading && nodeCount === 0 && (
          <div className="absolute inset-0 flex flex-col items-center justify-center text-gray-500 gap-2">
            <p>No devices yet.</p>
            <p className="text-xs">Add devices in Inventory, then click Discover Neighbors.</p>
          </div>
        )}
        {!isLoading && nodeCount > 0 && edgeCount === 0 && (
          <div className="absolute top-3 left-1/2 -translate-x-1/2 bg-yellow-900/80 text-yellow-300 text-xs px-3 py-1.5 rounded-full">
            No links found — click Discover Neighbors to run LLDP/CDP discovery
          </div>
        )}

        {/* Zoom controls */}
        <div className="absolute top-3 right-3 flex flex-col gap-1 z-10">
          {[
            { icon: ZoomIn,    action: zoomIn,  title: 'Zoom in' },
            { icon: ZoomOut,   action: zoomOut, title: 'Zoom out' },
            { icon: Maximize2, action: fitGraph, title: 'Fit graph' },
          ].map(({ icon: Icon, action, title }) => (
            <button
              key={title}
              onClick={action}
              title={title}
              className="w-8 h-8 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded flex items-center justify-center"
            >
              <Icon size={14} />
            </button>
          ))}
        </div>

        <div ref={containerRef} className="w-full h-full" />
      </div>

      {/* Selected device panel */}
      {selected && (
        <div className="bg-white rounded-xl shadow p-4 border-l-4" style={{ borderColor: PLATFORM_COLORS[selected.platform] ?? '#64748b' }}>
          <div className="flex items-center gap-3 mb-3">
            <span className="w-3 h-3 rounded-full" style={{ backgroundColor: PLATFORM_COLORS[selected.platform] ?? '#64748b' }} />
            <span className="font-mono font-bold text-gray-800">{selected.hostname}</span>
            <span className="text-xs text-gray-400">{PLATFORM_LABELS[selected.platform] ?? selected.platform}</span>
            <span className={`ml-auto px-2 py-0.5 rounded-full text-xs font-medium ${
              selected.status === 'reachable' ? 'bg-green-100 text-green-700'
              : selected.status === 'unreachable' ? 'bg-red-100 text-red-700'
              : 'bg-gray-100 text-gray-500'
            }`}>{selected.status}</span>
          </div>
          <div className="grid grid-cols-3 gap-3 text-sm">
            <div><span className="text-gray-400 text-xs block">IP Address</span>{selected.ip_address}</div>
            <div><span className="text-gray-400 text-xs block">Model</span>{selected.model ?? '—'}</div>
            <div><span className="text-gray-400 text-xs block">Site</span>{selected.site ?? '—'}</div>
          </div>
        </div>
      )}
    </div>
  )
}
