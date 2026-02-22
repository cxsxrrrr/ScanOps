import { useState } from 'react'
import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { UserButton, useUser } from '@clerk/clerk-react'
import { useApiSetup } from '../hooks/useApi'
import {
    LayoutDashboard,
    Globe,
    ScanSearch,
    Settings,
    ShieldCheck,
    Menu,
    X,
    ChevronLeft,
} from 'lucide-react'

const navItems = [
    { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/urls', icon: Globe, label: 'URLs' },
    { to: '/scans', icon: ScanSearch, label: 'Escaneos' },
    { to: '/settings', icon: Settings, label: 'Configuración' },
    { to: '/admin', icon: ShieldCheck, label: 'Admin', adminOnly: true },
]

export default function DashboardLayout() {
    useApiSetup()
    const { user } = useUser()
    const [collapsed, setCollapsed] = useState(false)
    const [mobileOpen, setMobileOpen] = useState(false)

    return (
        <div className="flex h-screen overflow-hidden gradient-bg">
            {/* Mobile overlay */}
            {mobileOpen && (
                <div
                    className="fixed inset-0 bg-black/60 z-40 lg:hidden"
                    onClick={() => setMobileOpen(false)}
                />
            )}

            {/* Sidebar */}
            <aside
                className={`
          fixed lg:relative z-50 h-full
          ${collapsed ? 'w-[72px]' : 'w-64'}
          ${mobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
          transition-all duration-300 ease-in-out
          glass border-r border-white/10
          flex flex-col
          custom-scrollbar
        `}
            >
                {/* Logo */}
                <div className="flex items-center justify-between p-4 border-b border-white/10">
                    {!collapsed && (
                        <div className="flex items-center gap-2">
                            <div className="w-8 h-8 rounded-lg gradient-primary flex items-center justify-center">
                                <ShieldCheck className="w-5 h-5 text-white" />
                            </div>
                            <span className="font-bold text-lg bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                                AuditWeb
                            </span>
                        </div>
                    )}
                    <button
                        onClick={() => setCollapsed(!collapsed)}
                        className="hidden lg:flex p-1.5 rounded-lg hover:bg-white/10 transition-colors"
                    >
                        <ChevronLeft className={`w-4 h-4 transition-transform ${collapsed ? 'rotate-180' : ''}`} />
                    </button>
                    <button
                        onClick={() => setMobileOpen(false)}
                        className="lg:hidden p-1.5 rounded-lg hover:bg-white/10"
                    >
                        <X className="w-4 h-4" />
                    </button>
                </div>

                {/* Navigation */}
                <nav className="flex-1 p-3 space-y-1">
                    {navItems.map((item) => (
                        <NavLink
                            key={item.to}
                            to={item.to}
                            end={item.to === '/'}
                            onClick={() => setMobileOpen(false)}
                            className={({ isActive }) =>
                                `flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200
                ${isActive
                                    ? 'gradient-primary text-white shadow-lg shadow-blue-500/20'
                                    : 'text-muted-foreground hover:text-foreground hover:bg-white/5'
                                }
                ${collapsed ? 'justify-center' : ''}
                `
                            }
                        >
                            <item.icon className="w-5 h-5 flex-shrink-0" />
                            {!collapsed && <span className="text-sm font-medium">{item.label}</span>}
                        </NavLink>
                    ))}
                </nav>

                {/* User section */}
                <div className="p-3 border-t border-white/10">
                    <div className={`flex items-center gap-3 ${collapsed ? 'justify-center' : ''}`}>
                        <UserButton
                            appearance={{
                                elements: {
                                    avatarBox: 'w-9 h-9',
                                },
                            }}
                        />
                        {!collapsed && (
                            <div className="flex-1 min-w-0">
                                <p className="text-sm font-medium truncate">
                                    {user?.firstName || 'Usuario'}
                                </p>
                                <p className="text-xs text-muted-foreground truncate">
                                    {user?.primaryEmailAddress?.emailAddress}
                                </p>
                            </div>
                        )}
                    </div>
                </div>
            </aside>

            {/* Main content */}
            <main className="flex-1 flex flex-col overflow-hidden">
                {/* Top bar */}
                <header className="h-16 flex items-center justify-between px-6 border-b border-white/10 glass">
                    <button
                        onClick={() => setMobileOpen(true)}
                        className="lg:hidden p-2 rounded-lg hover:bg-white/10"
                    >
                        <Menu className="w-5 h-5" />
                    </button>
                    <div className="flex-1" />
                    <div className="text-xs text-muted-foreground">
                        Auditoría Web para PYMES v1.0
                    </div>
                </header>

                {/* Page content */}
                <div className="flex-1 overflow-y-auto p-6 custom-scrollbar">
                    <Outlet />
                </div>
            </main>
        </div>
    )
}
