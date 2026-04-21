import client from './client'
import type { Alert, AlertRule } from '../types/command'

export const fetchAlerts = (params?: Record<string, string>) =>
  client.get<Alert[]>('/api/v1/alerts', { params }).then((r) => r.data)

export const acknowledgeAlert = (id: string) =>
  client.post<Alert>(`/api/v1/alerts/${id}/acknowledge`).then((r) => r.data)

export const resolveAlert = (id: string) =>
  client.post<Alert>(`/api/v1/alerts/${id}/resolve`).then((r) => r.data)

export const fetchAlertRules = () =>
  client.get<AlertRule[]>('/api/v1/alerts/rules').then((r) => r.data)

export const createAlertRule = (body: Partial<AlertRule>) =>
  client.post<AlertRule>('/api/v1/alerts/rules', body).then((r) => r.data)

export const updateAlertRule = (id: string, body: Partial<AlertRule>) =>
  client.put<AlertRule>(`/api/v1/alerts/rules/${id}`, body).then((r) => r.data)

export const deleteAlertRule = (id: string) =>
  client.delete(`/api/v1/alerts/rules/${id}`)
