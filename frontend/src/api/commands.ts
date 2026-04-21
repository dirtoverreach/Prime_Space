import client from './client'
import type { CommandJob } from '../types/command'

export const submitJob = (command: string, target_devices: string[]) =>
  client.post<CommandJob>('/api/v1/commands/jobs', { command, target_devices }).then((r) => r.data)

export const fetchJobs = () =>
  client.get<CommandJob[]>('/api/v1/commands/jobs').then((r) => r.data)

export const fetchJob = (id: string) =>
  client.get<CommandJob>(`/api/v1/commands/jobs/${id}`).then((r) => r.data)

export const cancelJob = (id: string) =>
  client.delete(`/api/v1/commands/jobs/${id}`)
