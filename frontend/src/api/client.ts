import axios from 'axios'
import toast from 'react-hot-toast'

const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? '',
  headers: { 'Content-Type': 'application/json' },
})

client.interceptors.response.use(
  (res) => res,
  (error) => {
    const msg = error.response?.data?.detail ?? error.message ?? 'An error occurred'
    toast.error(String(msg))
    return Promise.reject(error)
  }
)

export default client
