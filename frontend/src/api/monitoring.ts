import client from './client'
import type { DeviceMetric, MetricHistory } from '../types/monitoring'

export const fetchAllStats = () =>
  client.get<DeviceMetric[]>('/api/v1/monitoring/stats').then((r) => r.data)

export const fetchDeviceStats = (device_id: string) =>
  client.get<DeviceMetric>(`/api/v1/monitoring/stats/${device_id}`).then((r) => r.data)

export const fetchMetricHistory = (device_id: string, metric = 'cpu_percent') =>
  client.get<MetricHistory[]>(`/api/v1/monitoring/stats/${device_id}/history`, { params: { metric } }).then((r) => r.data)

export const fetchInterfaceStats = (device_id: string) =>
  client.get<object[]>(`/api/v1/monitoring/interfaces/${device_id}`).then((r) => r.data)

export const pollDevice = (device_id: string) =>
  client.post<{ task_id: string }>(`/api/v1/monitoring/poll/${device_id}`).then((r) => r.data)
