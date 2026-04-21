export interface CommandJobResult {
  id: string
  job_id: string
  device_id: string
  output: string | null
  exit_status: 'success' | 'error' | 'timeout'
  duration_ms: number | null
  completed_at: string
}

export interface CommandJob {
  id: string
  command: string
  target_devices: string[]
  requested_by: string
  celery_task_id: string | null
  status: 'pending' | 'running' | 'completed' | 'failed'
  created_at: string
  completed_at: string | null
  results: CommandJobResult[]
}

export interface Alert {
  id: string
  rule_id: string
  device_id: string
  metric: string
  value: number
  message: string | null
  severity: 'info' | 'warning' | 'critical'
  state: 'open' | 'acknowledged' | 'resolved'
  triggered_at: string
  resolved_at: string | null
}

export interface AlertRule {
  id: string
  name: string
  metric: string
  operator: string
  threshold: number
  severity: string
  device_id: string | null
  enabled: boolean
  created_at: string
}
