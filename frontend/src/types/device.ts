export interface Interface {
  id: string
  device_id: string
  name: string
  description: string | null
  admin_status: 'up' | 'down'
  oper_status: 'up' | 'down'
  speed_mbps: number | null
  mtu: number | null
  mac_address: string | null
  neighbor_device_id: string | null
  neighbor_interface: string | null
}

export interface Device {
  id: string
  hostname: string
  ip_address: string
  platform: 'junos' | 'cisco_ios' | 'cisco_xe'
  username: string
  device_type: string | null
  snmp_version: string
  status: 'reachable' | 'unreachable' | 'unknown'
  last_seen: string | null
  last_backup: string | null
  serial_number: string | null
  model: string | null
  os_version: string | null
  site: string | null
  tags: string[]
  created_at: string
  updated_at: string
  interfaces: Interface[]
}

export interface DeviceCreate {
  hostname: string
  ip_address: string
  platform: string
  username: string
  password?: string
  enable_secret?: string
  snmp_community?: string
  snmp_version?: string
  site?: string
  tags?: string[]
}

export interface TopologyNode {
  id: string
  hostname: string
  ip_address: string
  platform: string
  status: string
  model: string | null
  site: string | null
}

export interface TopologyEdge {
  source: string
  target: string
  source_interface: string
  target_interface: string
}

export interface Topology {
  nodes: TopologyNode[]
  edges: TopologyEdge[]
}
