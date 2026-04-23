import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard, Server, Network, FileCode,
  Activity, Bell, Terminal,
} from 'lucide-react'

const links = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/inventory', icon: Server, label: 'Inventory' },
  { to: '/topology', icon: Network, label: 'Topology' },
  { to: '/configs', icon: FileCode, label: 'Configs' },
  { to: '/monitoring', icon: Activity, label: 'Monitoring' },
  { to: '/alerts', icon: Bell, label: 'Alerts' },
  { to: '/commands', icon: Terminal, label: 'Commands' },
]

export default function Sidebar() {
  return (
    <aside className="w-48 bg-gray-900 text-gray-200 flex flex-col min-h-screen">
      <div className="px-4 py-5 border-b border-gray-700">
        <span className="text-lg font-semibold text-white">Prime Space</span>
        <p className="text-xs text-gray-500 mt-0.5">Network Management</p>
      </div>
      <nav className="flex-1 px-2 py-4 space-y-1">
        {links.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors ${
                isActive
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-400 hover:bg-gray-800 hover:text-white'
              }`
            }
          >
            <Icon size={16} />
            {label}
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}
