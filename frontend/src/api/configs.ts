import client from './client'
import type { ConfigBackup, ConfigBackupDetail, DiffResult, ConfigTemplate } from '../types/config'

export const fetchBackups = (device_id?: string) =>
  client.get<ConfigBackup[]>('/api/v1/configs/backups', { params: device_id ? { device_id } : {} }).then((r) => r.data)

export const fetchBackup = (id: string) =>
  client.get<ConfigBackupDetail>(`/api/v1/configs/backups/${id}`).then((r) => r.data)

export const triggerBackup = (device_id: string, label?: string) =>
  client.post<{ task_id: string }>('/api/v1/configs/backups', { device_id, label }).then((r) => r.data)

export const deleteBackup = (id: string) =>
  client.delete(`/api/v1/configs/backups/${id}`)

export const diffBackups = (a: string, b: string) =>
  client.get<DiffResult>('/api/v1/configs/diff', { params: { a, b } }).then((r) => r.data)

export const diffLive = (device_id: string) =>
  client.get<DiffResult>(`/api/v1/configs/diff/live/${device_id}`).then((r) => r.data)

export const pushConfig = (device_ids: string[], config_snippet: string) =>
  client.post<{ task_id: string }>('/api/v1/configs/push', { device_ids, config_snippet }).then((r) => r.data)

export const fetchTemplates = () =>
  client.get<ConfigTemplate[]>('/api/v1/configs/templates').then((r) => r.data)

export const createTemplate = (body: Partial<ConfigTemplate>) =>
  client.post<ConfigTemplate>('/api/v1/configs/templates', body).then((r) => r.data)

export const updateTemplate = (id: string, body: Partial<ConfigTemplate>) =>
  client.put<ConfigTemplate>(`/api/v1/configs/templates/${id}`, body).then((r) => r.data)

export const deleteTemplate = (id: string) =>
  client.delete(`/api/v1/configs/templates/${id}`)

export const renderTemplate = (id: string, variables: Record<string, unknown>) =>
  client.post<{ rendered: string }>(`/api/v1/configs/templates/${id}/render`, { variables }).then((r) => r.data)

export const deployTemplate = (id: string, device_ids: string[], variables: Record<string, unknown>) =>
  client.post<{ task_id: string }>(`/api/v1/configs/templates/${id}/deploy`, { device_ids, variables }).then((r) => r.data)
