import { useState } from 'react'
import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom'
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
    User,
    Sparkles,
    Crown,
    Zap,
    Shield,
    ScrollText,
} from 'lucide-react'

const navItems = [
    { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/urls', icon: Globe, label: 'URLs' },
    { to: '/scans', icon: ScanSearch, label: 'Escaneos' },
    { to: '/plans', icon: Sparkles, label: 'Planes' },
    { to: '/profile', icon: User, label: 'Perfil' },
    { to: '/settings', icon: Settings, label: 'Configuración' },
    { to: '/admin', icon: ShieldCheck, label: 'Admin', adminOnly: true },
]

const pageNames = {
    '/': 'Dashboard',
    '/urls': 'URLs Registradas',
    '/scans': 'Historial de Escaneos',
    '/plans': 'Planes',
    '/profile': 'Mi Perfil',
    '/settings': 'Configuración',
    '/admin': 'Panel de Administración',
}

const planIcons = {
    free: Shield,
    pro: Zap,
    ultimate: Crown,
}

const planBadgeClasses = {
    free: 'plan-badge-free',
    pro: 'plan-badge-pro',
    ultimate: 'plan-badge-ultimate',
}

export default function DashboardLayout() {
    useApiSetup()
    const { user } = useUser()
    const location = useLocation()
    const [collapsed, setCollapsed] = useState(false)
    const [mobileOpen, setMobileOpen] = useState(false)

    // Derive page name from current route
    const currentPageName = pageNames[location.pathname] || 'Reporte'

    // Filter admin-only items (basic check — real role check should come from backend)
    const isAdmin = user?.publicMetadata?.role === 'admin'
    const visibleNavItems = navItems.filter(item => !item.adminOnly || isAdmin)

    // Plan info from public metadata (set by backend sync)
    const currentPlan = user?.publicMetadata?.plan || 'free'
    const PlanIcon = planIcons[currentPlan] || Shield
    const planBadgeClass = planBadgeClasses[currentPlan] || 'plan-badge-free'

    return (
        <div className="flex h-screen overflow-hidden gradient-bg">
            {/* Mobile overlay */}
            {mobileOpen && (
                <div
                    className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 lg:hidden"
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
                            <div className="w-8 h-8 rounded-lg gradient-primary flex items-center justify-center shadow-lg shadow-blue-500/25">
                                <ShieldCheck className="w-5 h-5 text-white" />
                            </div>
                            <span className="font-bold text-lg bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                                ScanOps
                            </span>
                        </div>
                    )}
                    {collapsed && (
                        <div className="mx-auto">
                            <div className="w-8 h-8 rounded-lg gradient-primary flex items-center justify-center shadow-lg shadow-blue-500/25">
                                <ShieldCheck className="w-5 h-5 text-white" />
                            </div>
                        </div>
                    )}
                    <button
                        onClick={() => setCollapsed(!collapsed)}
                        className="hidden lg:flex p-1.5 rounded-lg hover:bg-white/10 transition-colors"
                        aria-label={collapsed ? 'Expandir sidebar' : 'Colapsar sidebar'}
                    >
                        <ChevronLeft className={`w-4 h-4 transition-transform duration-300 ${collapsed ? 'rotate-180' : ''}`} />
                    </button>
                    <button
                        onClick={() => setMobileOpen(false)}
                        className="lg:hidden p-1.5 rounded-lg hover:bg-white/10"
                        aria-label="Cerrar menú"
                    >
                        <X className="w-4 h-4" />
                    </button>
                </div>

                {/* Navigation */}
                <nav className="flex-1 p-3 space-y-1">
                    {visibleNavItems.map((item) => (
                        <NavLink
                            key={item.to}
                            to={item.to}
                            end={item.to === '/'}
                            onClick={() => setMobileOpen(false)}
                            className={({ isActive }) =>
                                `sidebar-item relative flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200
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
                            {collapsed && <span className="sidebar-tooltip">{item.label}</span>}
                        </NavLink>
                    ))}
                </nav>

                {/* Terms link */}
                {!collapsed && (
                    <div className="px-3 pb-2">
                        <NavLink
                            to="/terms"
                            onClick={() => setMobileOpen(false)}
                            className="flex items-center gap-2 px-3 py-2 text-xs text-muted-foreground hover:text-foreground rounded-lg hover:bg-white/5 transition-colors"
                        >
                            <ScrollText className="w-3.5 h-3.5" />
                            Términos y Condiciones
                        </NavLink>
                    </div>
                )}

                {/* User section */}
                <div className="p-3 border-t border-white/10">
                    <div className={`flex items-center gap-3 ${collapsed ? 'justify-center' : ''}`}>
                        <UserButton
                            appearance={{
                                elements: {
                                    avatarBox: 'w-9 h-9 ring-2 ring-white/10',
                                },
                            }}
                        />
                        {!collapsed && (
                            <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2">
                                    <p className="text-sm font-medium truncate">
                                        {user?.firstName || 'Usuario'}
                                    </p>
                                    {isAdmin && (
                                        <span className="role-badge-admin px-1.5 py-0.5 rounded text-[10px] font-bold leading-none">
                                            ADMIN
                                        </span>
                                    )}
                                </div>
                                <div className="flex items-center gap-1.5 mt-0.5">
                                    <span className={`${planBadgeClass} px-1.5 py-0.5 rounded text-[10px] font-bold leading-none inline-flex items-center gap-1`}>
                                        <PlanIcon className="w-2.5 h-2.5" />
                                        {currentPlan.toUpperCase()}
                                    </span>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </aside>

            {/* Main content */}
            <main className="flex-1 flex flex-col overflow-hidden">
                {/* Top bar */}
                <header className="h-16 flex items-center justify-between px-6 border-b border-white/10 glass">
                    <div className="flex items-center gap-4">
                        <button
                            onClick={() => setMobileOpen(true)}
                            className="lg:hidden p-2 rounded-lg hover:bg-white/10 transition-colors"
                            aria-label="Abrir menú"
                        >
                            <Menu className="w-5 h-5" />
                        </button>
                        <h2 className="text-lg font-semibold hidden sm:block">
                            {currentPageName}
                        </h2>
                    </div>
                    <div className="text-xs text-muted-foreground flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                        <span className="hidden sm:inline">Sistema activo</span>
                        <span className="text-white/20">•</span>
                        <span>v2.0</span>
                    </div>
                </header>

                {/* Page content */}
                <div className="flex-1 overflow-y-auto p-6 custom-scrollbar">
                    <div className="page-enter">
                        <Outlet />
                    </div>
                </div>
            </main>
        </div>
    )
}
