export interface ConfigBackup {
  id: string
  device_id: string
  checksum: string
  source: 'scheduled' | 'manual' | 'pre_change'
  label: string | null
  created_by: string
  created_at: string
}

export interface ConfigBackupDetail extends ConfigBackup {
  content: string
}

export interface DiffResult {
  unified_diff: string
  lines_added: number
  lines_removed: number
}

export interface ConfigTemplate {
  id: string
  name: string
  platform: string
  body: string
  variables: Record<string, unknown>
  created_at: string
  updated_at: string
}
