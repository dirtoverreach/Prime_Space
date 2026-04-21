import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'

export default function PageShell() {
  return (
    <div className="flex min-h-screen bg-gray-100">
      <Sidebar />
      <main className="flex-1 overflow-auto p-6">
        <Outlet />
      </main>
    </div>
  )
}
