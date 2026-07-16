import { useState, useEffect } from 'react'
import { Outlet, NavLink, useLocation, Navigate } from 'react-router-dom'
import { UserButton, useUser } from '@clerk/clerk-react'
import { motion, AnimatePresence } from 'framer-motion'
import api from '../lib/api'
import { useTheme } from '../hooks/useTheme'
import {
    LayoutDashboard, Globe, ScanSearch, Settings,
    ShieldCheck, Menu, X, ChevronLeft, User, Sparkles,
    Crown, Zap, Shield, ScrollText, Sun, Moon, LifeBuoy,
} from 'lucide-react'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import PageTransition from '../components/PageTransition'

// Each nav item carries its own accent color palette
const NAV_ITEMS = [
    {
        to: '/', icon: LayoutDashboard, label: 'Dashboard', end: true,
        iconColor: '#60a5fa', hoverBg: 'rgba(59,130,246,0.12)',
        activeBg: 'linear-gradient(135deg,#2563eb,#3b82f6)', glow: '0 4px 20px rgba(59,130,246,0.45)',
    },
    {
        to: '/urls', icon: Globe, label: 'URLs',
        iconColor: '#22d3ee', hoverBg: 'rgba(6,182,212,0.12)',
        activeBg: 'linear-gradient(135deg,#0891b2,#06b6d4)', glow: '0 4px 20px rgba(6,182,212,0.45)',
    },
    {
        to: '/scans', icon: ScanSearch, label: 'Escaneos',
        iconColor: '#c084fc', hoverBg: 'rgba(168,85,247,0.12)',
        activeBg: 'linear-gradient(135deg,#9333ea,#a855f7)', glow: '0 4px 20px rgba(168,85,247,0.45)',
    },
    {
        to: '/plans', icon: Sparkles, label: 'Planes',
        iconColor: '#fbbf24', hoverBg: 'rgba(245,158,11,0.12)',
        activeBg: 'linear-gradient(135deg,#d97706,#f59e0b)', glow: '0 4px 20px rgba(245,158,11,0.45)',
    },
    {
        to: '/profile', icon: User, label: 'Perfil',
        iconColor: '#fb7185', hoverBg: 'rgba(244,63,94,0.12)',
        activeBg: 'linear-gradient(135deg,#e11d48,#f43f5e)', glow: '0 4px 20px rgba(244,63,94,0.45)',
    },
    {
        to: '/settings', icon: Settings, label: 'Configuración',
        iconColor: '#94a3b8', hoverBg: 'rgba(100,116,139,0.12)',
        activeBg: 'linear-gradient(135deg,#475569,#64748b)', glow: '0 4px 20px rgba(100,116,139,0.35)',
    },
    {
        to: '/support', icon: LifeBuoy, label: 'Soporte',
        iconColor: '#34d399', hoverBg: 'rgba(16,185,129,0.12)',
        activeBg: 'linear-gradient(135deg,#059669,#10b981)', glow: '0 4px 20px rgba(16,185,129,0.45)',
    },
    {
        to: '/admin', icon: ShieldCheck, label: 'Admin', adminOnly: true,
        iconColor: '#f87171', hoverBg: 'rgba(239,68,68,0.12)',
        activeBg: 'linear-gradient(135deg,#dc2626,#ef4444)', glow: '0 4px 20px rgba(239,68,68,0.45)',
    },
]

const pageNames = {
    '/':         'Dashboard',
    '/urls':     'URLs Registradas',
    '/scans':    'Historial de Escaneos',
    '/plans':    'Planes',
    '/profile':  'Mi Perfil',
    '/settings': 'Configuración',
    '/support':  'Soporte',
    '/admin':    'Panel de Administración',
}

const planIcons  = { free: Shield, pro: Zap, ultimate: Crown }
const planBadges = { free: 'plan-badge-free', pro: 'plan-badge-pro', ultimate: 'plan-badge-ultimate' }

function NavItem({ item, collapsed, onClick, isDark }) {
    const inactiveText = isDark ? 'rgba(148,163,184,0.9)' : 'rgba(15,23,42,0.88)'

    return collapsed ? (
        <Tooltip>
            <TooltipTrigger asChild>
                <NavLink to={item.to} end={item.end} onClick={onClick} className="block">
                    {({ isActive }) => (
                        <span
                            className="flex items-center justify-center w-10 h-10 mx-auto rounded-xl transition-all duration-200 cursor-pointer"
                            style={isActive ? { background: item.activeBg, boxShadow: item.glow } : undefined}
                            onMouseEnter={e => { if (!isActive) e.currentTarget.style.background = item.hoverBg }}
                            onMouseLeave={e => { if (!isActive) e.currentTarget.style.background = '' }}
                        >
                            <item.icon
                                className="w-5 h-5 flex-shrink-0 transition-colors duration-200"
                                style={{ color: isActive ? '#fff' : item.iconColor }}
                            />
                        </span>
                    )}
                </NavLink>
            </TooltipTrigger>
            <TooltipContent side="right" className="font-medium ml-1">
                {item.label}
            </TooltipContent>
        </Tooltip>
    ) : (
        <NavLink to={item.to} end={item.end} onClick={onClick} className="block">
            {({ isActive }) => (
                <span
                    className="relative flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 cursor-pointer group"
                    style={isActive ? { background: item.activeBg, boxShadow: item.glow } : undefined}
                    onMouseEnter={e => { if (!isActive) e.currentTarget.style.background = item.hoverBg }}
                    onMouseLeave={e => { if (!isActive) e.currentTarget.style.background = '' }}
                >
                    {!isActive && (
                        <span
                            className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-4 rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-200"
                            style={{ background: item.iconColor }}
                        />
                    )}
                    <item.icon
                        className="w-5 h-5 flex-shrink-0 transition-all duration-200"
                        style={{ color: isActive ? '#fff' : item.iconColor }}
                    />
                    <span
                        className="text-sm font-medium whitespace-nowrap transition-colors duration-200"
                        style={{ color: isActive ? '#fff' : inactiveText }}
                    >
                        {item.label}
                    </span>
                </span>
            )}
        </NavLink>
    )
}

export default function DashboardLayout() {
    const { user }   = useUser()
    const location                = useLocation()
    const { isDark, toggleTheme } = useTheme()
    const [collapsed,  setCollapsed]  = useState(false)
    const [mobileOpen, setMobileOpen] = useState(false)
    const [profile,    setProfile]    = useState(null)
    const [profileLoading, setProfileLoading] = useState(true)

    useEffect(() => {
        let cancelled = false
        let retries = 0
        const maxRetries = 4

        async function loadProfile() {
            while (retries < maxRetries && !cancelled) {
                try {
                    const res = await api.get('/auth/profile/', { signal: null })
                    if (!cancelled) {
                        setProfile(res.data)
                        setProfileLoading(false)
                    }
                    return
                } catch (err) {
                    if (err.code === 'ERR_CANCELED') return
                    retries++
                    if (retries >= maxRetries) {
                        if (!cancelled) {
                            console.error('Profile load failed after retries:', err)
                            setProfileLoading(false)
                        }
                        return
                    }
                    // Exponential backoff: 400ms, 800ms, 1600ms
                    await new Promise(r => setTimeout(r, 400 * Math.pow(2, retries - 1)))
                }
            }
        }
        loadProfile()
        return () => { cancelled = true }
    }, [])

    // Redirect synchronously (before Outlet mounts) rather than from an
    // effect — an effect-based navigate() still lets the index route's
    // child (Dashboard) mount and fire its own data-loading effect first,
    // which calls GET /auth/organization/ and silently auto-creates an org
    // for the brand-new user. That org then blocks the invite they were
    // trying to accept ("ya perteneces a otra organizacion").
    const pendingInvite = sessionStorage.getItem('pendingInvite')
    if (pendingInvite && location.pathname !== `/invite/${pendingInvite}`) {
        sessionStorage.removeItem('pendingInvite')
        return <Navigate to={`/invite/${pendingInvite}`} replace />
    }

    const currentPageName  = pageNames[location.pathname] || 'Reporte'
    const isAdmin          = profile?.role === 'admin'
    // Show admin while profile loads (profile === null), hide only when confirmed non-admin
    const visibleItems     = NAV_ITEMS.filter(i => !i.adminOnly || profile === null || isAdmin)
    const currentPlan     = profile?.organization?.plan || 'free'
    const PlanIcon        = planIcons[currentPlan] || Shield
    const planBadgeClass  = planBadges[currentPlan] || 'plan-badge-free'
    const sidebarW        = collapsed ? 72 : 256

    return (
        <TooltipProvider delayDuration={0}>
            <div className="flex h-screen overflow-hidden gradient-bg">

                {/* Mobile overlay */}
                <AnimatePresence>
                    {mobileOpen && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            transition={{ duration: 0.2 }}
                            className="fixed inset-0 bg-black/70 backdrop-blur-sm z-40 lg:hidden"
                            onClick={() => setMobileOpen(false)}
                        />
                    )}
                </AnimatePresence>

                {/* ── Sidebar ── */}
                <motion.aside
                    animate={{ width: sidebarW }}
                    transition={{ type: 'spring', stiffness: 300, damping: 30 }}
                    className={`
                        fixed lg:relative z-50 h-full overflow-hidden flex flex-col shadow-xl lg:shadow-none
                        ${mobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
                        transition-transform duration-300 lg:transition-none
                    `}
                    style={{
                        width: sidebarW,
                        minWidth: sidebarW,
                        background: isDark
                            ? 'linear-gradient(180deg, #07101f 0%, #0b1526 50%, #07101f 100%)'
                            : 'linear-gradient(180deg, #ffffff 0%, #f8fafc 50%, #ffffff 100%)',
                        borderRight: isDark
                            ? '1px solid rgba(255,255,255,0.06)'
                            : '1px solid hsl(220 13% 88%)',
                    }}
                >
                    {/* Ambient orbs — dark only */}
                    {isDark && (
                        <div className="pointer-events-none absolute inset-0 overflow-hidden">
                            <div className="absolute -top-10 -right-10 w-40 h-40 rounded-full blur-3xl bg-blue-600/10" />
                            <div className="absolute bottom-20 -left-10 w-32 h-32 rounded-full blur-3xl bg-purple-600/10" />
                        </div>
                    )}

                    {/* ── Logo ── */}
                    <div className={`relative flex items-center ${collapsed ? 'flex-col justify-center gap-2 py-3' : 'justify-between px-4 h-16'}`}
                        style={{ borderBottom: isDark ? '1px solid rgba(255,255,255,0.06)' : '1px solid hsl(220 13% 88%)' }}
                    >
                        <AnimatePresence mode="wait">
                            {!collapsed && (
                                <motion.div
                                    key="logo-full"
                                    initial={{ opacity: 0, x: -12 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    exit={{ opacity: 0, x: -12 }}
                                    transition={{ duration: 0.15 }}
                                    className="flex items-center gap-2.5"
                                >
                                    <div className="relative flex-shrink-0">
                                        <div className="w-9 h-9 rounded-xl flex items-center justify-center"
                                            style={{ background: 'linear-gradient(135deg,#2563eb,#7c3aed)', boxShadow: '0 4px 16px rgba(37,99,235,0.5)' }}
                                        >
                                            <ShieldCheck className="w-5 h-5 text-white" />
                                        </div>
                                        <span className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 bg-emerald-400 rounded-full border-2 animate-pulse" style={{ borderColor: isDark ? '#07101f' : '#f8fafc' }} />
                                    </div>
                                    <span className="font-extrabold text-lg tracking-tight whitespace-nowrap"
                                        style={{ background: 'linear-gradient(90deg,#60a5fa,#c084fc)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}
                                    >
                                        Vigia
                                    </span>
                                </motion.div>
                            )}
                        </AnimatePresence>
                        {collapsed && (
                            <div className="relative">
                                <div className="w-9 h-9 rounded-xl flex items-center justify-center"
                                    style={{ background: 'linear-gradient(135deg,#2563eb,#7c3aed)', boxShadow: '0 4px 16px rgba(37,99,235,0.5)' }}
                                >
                                    <ShieldCheck className="w-5 h-5 text-white" />
                                </div>
                                <span className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 bg-emerald-400 rounded-full border-2 animate-pulse" style={{ borderColor: isDark ? '#07101f' : '#f8fafc' }} />
                            </div>
                        )}
                        <div className={`flex items-center ${collapsed ? '' : 'gap-1'}`}>
                            <button
                                onClick={() => { setCollapsed(!collapsed); setMobileOpen(false) }}
                                className="hidden lg:flex p-1.5 rounded-lg transition-colors flex-shrink-0"
                                style={{ color: isDark ? 'rgba(148,163,184,0.6)' : 'rgba(71,85,105,0.6)' }}
                                onMouseEnter={e => e.currentTarget.style.background = isDark ? 'rgba(255,255,255,0.07)' : 'rgba(0,0,0,0.05)'}
                                onMouseLeave={e => e.currentTarget.style.background = ''}
                                aria-label={collapsed ? 'Expandir' : 'Colapsar'}
                            >
                                <motion.div animate={{ rotate: collapsed ? 180 : 0 }} transition={{ duration: 0.25 }}>
                                    <ChevronLeft className="w-4 h-4" />
                                </motion.div>
                            </button>
                            {!collapsed && (
                                <button
                                    onClick={() => setMobileOpen(false)}
                                    className="lg:hidden p-1.5 rounded-lg flex-shrink-0"
                                    style={{ color: isDark ? 'rgba(148,163,184,0.7)' : 'rgba(71,85,105,0.7)' }}
                                >
                                    <X className="w-4 h-4" />
                                </button>
                            )}
                        </div>
                    </div>

                    {/* ── Nav label ── */}
                    {!collapsed && (
                        <div className="px-4 pt-5 pb-1">
                            <span className="text-[10px] font-bold tracking-widest uppercase"
                                style={{ color: isDark ? 'rgba(100,116,139,0.7)' : 'rgba(51,65,85,1)' }}
                            >
                                Navegación
                            </span>
                        </div>
                    )}

                    {/* ── Navigation ── */}
                    <nav className={`flex-1 overflow-y-auto custom-scrollbar ${collapsed ? 'px-2 pt-3' : 'px-3'} space-y-1`}>
                        {visibleItems.map((item) => (
                            <div key={item.to}>
                                <NavItem
                                    item={item}
                                    collapsed={collapsed}
                                    onClick={() => setMobileOpen(false)}
                                    isDark={isDark}
                                />
                            </div>
                        ))}
                    </nav>

                    {/* ── Terms ── */}
                    {!collapsed && (
                        <div className="px-3 pb-3">
                            <NavLink
                                to="/terms"
                                onClick={() => setMobileOpen(false)}
                                className="flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-xs font-medium transition-all duration-200 group"
                                style={{
                                    color: isDark ? 'rgba(148,163,184,0.85)' : 'rgba(30,41,59,0.8)',
                                    background: isDark ? 'rgba(255,255,255,0.04)' : 'hsl(220 13% 94%)',
                                    border: isDark ? '1px solid rgba(255,255,255,0.07)' : '1px solid hsl(220 13% 88%)',
                                }}
                                onMouseEnter={e => {
                                    e.currentTarget.style.color = isDark ? '#fff' : 'rgba(15,23,42,1)'
                                    e.currentTarget.style.background = isDark ? 'rgba(255,255,255,0.09)' : 'rgba(59,130,246,0.08)'
                                    e.currentTarget.style.borderColor = isDark ? 'rgba(255,255,255,0.15)' : 'rgba(59,130,246,0.3)'
                                }}
                                onMouseLeave={e => {
                                    e.currentTarget.style.color = isDark ? 'rgba(148,163,184,0.85)' : 'rgba(30,41,59,0.8)'
                                    e.currentTarget.style.background = isDark ? 'rgba(255,255,255,0.04)' : 'hsl(220 13% 94%)'
                                    e.currentTarget.style.borderColor = isDark ? 'rgba(255,255,255,0.07)' : 'hsl(220 13% 88%)'
                                }}
                            >
                                <ScrollText className="w-4 h-4 flex-shrink-0 text-blue-400" />
                                <span className="whitespace-nowrap">Términos y Condiciones</span>
                            </NavLink>
                        </div>
                    )}

                    {/* ── Divider ── */}
                    <div className="mx-3 h-px" style={{ background: isDark ? 'rgba(255,255,255,0.06)' : 'hsl(220 13% 88%)' }} />

                    {/* ── User section ── */}
                    <div className="p-3 flex justify-center">
                        <div
                            className={`flex items-center transition-all duration-300 ${
                                collapsed ? 'justify-center p-0 bg-transparent border-none' : 'gap-3 rounded-xl p-2.5'
                            }`}
                            style={collapsed ? undefined : {
                                background: isDark ? 'rgba(255,255,255,0.04)' : 'hsl(220 13% 94%)',
                                border: isDark ? '1px solid rgba(255,255,255,0.07)' : '1px solid hsl(220 13% 88%)',
                            }}
                        >
                            <UserButton
                                appearance={{
                                    elements: {
                                        avatarBox: 'w-8 h-8 ring-2 ring-blue-500/40',
                                        userButtonPopoverCard: isDark
                                            ? '!bg-[#050c1a] !border !border-white/10 !shadow-2xl !rounded-xl'
                                            : '!bg-white !border !border-slate-200 !shadow-2xl !rounded-xl',
                                        userButtonPopoverActions: isDark ? '!bg-[#050c1a]' : '!bg-white',
                                        userButtonPopoverUserPreview: isDark ? '!bg-[#050c1a]' : '!bg-white',
                                        userPreview: isDark ? '!bg-[#050c1a]' : '!bg-white',
                                        userPreviewAvatarContainer: isDark ? '!bg-[#050c1a]' : '!bg-white',
                                        userButtonPopoverHeader: isDark ? '!bg-[#050c1a]' : '!bg-white',
                                        userButtonPopoverActionButton: isDark
                                            ? '!text-slate-200 hover:!bg-white/5 !rounded-lg'
                                            : '!text-slate-800 hover:!bg-slate-100 !rounded-lg',
                                        userButtonPopoverActionButtonText: isDark ? '!text-slate-200' : '!text-slate-800',
                                        userButtonPopoverActionButtonIcon: isDark ? '!text-slate-400' : '!text-slate-500',
                                        userPreviewMainIdentifier: isDark ? '!text-white !font-medium' : '!text-slate-900 !font-medium',
                                        userPreviewSecondaryIdentifier: isDark ? '!text-slate-400 !text-sm' : '!text-slate-500 !text-sm',
                                        userButtonPopoverFooter: '!hidden',
                                    },
                                }}
                            />
                            <AnimatePresence mode="wait">
                                {!collapsed && (
                                    <motion.div
                                        key="user-info"
                                        initial={{ opacity: 0, x: -8 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        exit={{ opacity: 0, x: -8 }}
                                        transition={{ duration: 0.15 }}
                                        className="flex-1 min-w-0"
                                    >
                                        <div className="flex items-center gap-2">
                                            <p className={`text-sm font-semibold truncate ${isDark ? 'text-slate-200' : 'text-slate-800'}`}>
                                                {user?.firstName || 'Usuario'}
                                            </p>
                                            {isAdmin && (
                                                <span className="role-badge-admin px-1.5 py-0.5 rounded text-[9px] font-extrabold tracking-wider leading-none shrink-0 bg-red-500/20 text-red-400 border border-red-500/30">
                                                    ADMIN
                                                </span>
                                            )}
                                        </div>
                                        <div className="flex items-center gap-1.5 mt-1">
                                            {profileLoading ? (
                                                <span className="px-2 py-1 rounded text-[9px] font-bold tracking-wide leading-none bg-accent animate-pulse text-muted-foreground">
                                                    Cargando...
                                                </span>
                                            ) : (
                                                <span className={`${planBadgeClass} px-2 py-0.5 rounded inline-flex items-center gap-1 text-[9px] font-bold tracking-wide leading-none`}>
                                                    <PlanIcon className="w-2.5 h-2.5" />
                                                    {currentPlan.toUpperCase()}
                                                </span>
                                            )}
                                        </div>
                                    </motion.div>
                                 )}
                             </AnimatePresence>
                        </div>
                    </div>
                </motion.aside>

                {/* ── Main content ── */}
                <main className="flex-1 flex flex-col overflow-hidden min-w-0">
                    <header className="h-16 flex items-center justify-between px-5 border-b border-border bg-card/80 backdrop-blur-xl flex-shrink-0">
                        <div className="flex items-center gap-4">
                            <button
                                onClick={() => setMobileOpen(true)}
                                className="lg:hidden p-2 rounded-lg hover:bg-accent transition-colors"
                                aria-label="Abrir menú"
                            >
                                <Menu className="w-5 h-5" />
                            </button>
                            <h2 className="text-base font-semibold hidden sm:block text-foreground">
                                {currentPageName}
                            </h2>
                        </div>
                        <div className="flex items-center gap-2">
                            <button
                                onClick={toggleTheme}
                                className="p-2 rounded-lg hover:bg-accent transition-colors"
                                aria-label={isDark ? 'Modo claro' : 'Modo oscuro'}
                            >
                                <AnimatePresence mode="wait">
                                    {isDark ? (
                                        <motion.div key="sun" initial={{ rotate: -90, opacity: 0 }} animate={{ rotate: 0, opacity: 1 }} exit={{ rotate: 90, opacity: 0 }} transition={{ duration: 0.2 }}>
                                            <Sun className="w-4 h-4 text-amber-400" />
                                        </motion.div>
                                    ) : (
                                        <motion.div key="moon" initial={{ rotate: 90, opacity: 0 }} animate={{ rotate: 0, opacity: 1 }} exit={{ rotate: -90, opacity: 0 }} transition={{ duration: 0.2 }}>
                                            <Moon className="w-4 h-4 text-slate-600" />
                                        </motion.div>
                                    )}
                                </AnimatePresence>
                            </button>
                            <div className="hidden sm:flex items-center gap-2 text-xs text-muted-foreground px-3 py-1.5 rounded-full bg-accent">
                                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                                Sistema activo
                                <span className="opacity-30">·</span>
                                v2.0
                            </div>
                        </div>
                    </header>

                    <div className="flex-1 overflow-y-auto p-5 sm:p-6 custom-scrollbar">
                        <AnimatePresence mode="wait">
                            <PageTransition key={location.pathname}>
                                <Outlet />
                            </PageTransition>
                        </AnimatePresence>
                    </div>
                </main>
            </div>
        </TooltipProvider>
    )
}
