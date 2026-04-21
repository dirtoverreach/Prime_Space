export interface DeviceMetric {
  id: string
  device_id: string
  cpu_percent: number | null
  mem_used_percent: number | null
  uptime_seconds: number | null
  interface_stats: Record<string, InterfaceStat> | null
  collected_at: string
}

export interface InterfaceStat {
  index: string
  name: string
  in_octets: string
  out_octets: string
  in_errors: string
  out_errors: string
  oper_status: 'up' | 'down'
}

export interface MetricHistory {
  collected_at: string
  cpu_percent: number | null
  mem_used_percent: number | null
  uptime_seconds: number | null
}
