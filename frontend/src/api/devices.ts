import client from './client'
import type { Device, DeviceCreate, Topology } from '../types/device'

export const fetchDevices = (params?: Record<string, string>) =>
  client.get<Device[]>('/api/v1/devices', { params }).then((r) => r.data)

export const fetchDevice = (id: string) =>
  client.get<Device>(`/api/v1/devices/${id}`).then((r) => r.data)

export const createDevice = (body: DeviceCreate) =>
  client.post<Device>('/api/v1/devices', body).then((r) => r.data)

export const updateDevice = (id: string, body: Partial<DeviceCreate>) =>
  client.put<Device>(`/api/v1/devices/${id}`, body).then((r) => r.data)

export const deleteDevice = (id: string) =>
  client.delete(`/api/v1/devices/${id}`)

export const syncDevice = (id: string) =>
  client.post<{ task_id: string }>(`/api/v1/devices/${id}/sync`).then((r) => r.data)

export const discoverDevices = (body: object) =>
  client.post<{ task_id: string }>('/api/v1/devices/discover', body).then((r) => r.data)

export const fetchTopology = () =>
  client.get<Topology>('/api/v1/topology').then((r) => r.data)

export const discoverTopology = () =>
  client.post<{ task_id: string }>('/api/v1/topology/discover').then((r) => r.data)
