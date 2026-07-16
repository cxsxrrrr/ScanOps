import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { toast } from 'sonner'
import api from '../../lib/api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
    Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import {
    ShieldCheck, Users, ScanSearch, AlertTriangle,
    Mail, Loader2, RefreshCw, XCircle, Building,
    Crown, Zap, Shield, Check, BarChart3, CheckCircle2,
    Clock, Activity, Search, ChevronLeft, ChevronRight,
} from 'lucide-react'

import { EditOrgModal } from './EditOrgModal'
import { EditUserModal } from './EditUserModal'
import { OrgAnalyticsModal } from './OrgAnalyticsModal'

const planConfig = {
    free:     { icon: Shield,  label: 'Free',     gradient: 'from-gray-500 to-gray-600',    badge: 'plan-badge-free' },
    pro:      { icon: Zap,     label: 'Pro',      gradient: 'from-purple-500 to-purple-600', badge: 'plan-badge-pro' },
    ultimate: { icon: Crown,   label: 'Ultimate', gradient: 'from-amber-500 to-orange-500',  badge: 'plan-badge-ultimate' },
}

export default function AdminDashboard() {
    const [metrics,       setMetrics]       = useState(null)
    const [errors,        setErrors]        = useState(null)
    const [users,         setUsers]         = useState([])
    const [orgs,          setOrgs]          = useState([])
    const [analytics,     setAnalytics]     = useState([])
    const [loading,       setLoading]       = useState(true)
    const [editingOrg,    setEditingOrg]    = useState(null)
    const [editingUser,   setEditingUser]   = useState(null)
    const [viewingAnalytics, setViewingAnalytics] = useState(null)

    const [searchAnalytics, setSearchAnalytics] = useState('')
    const [pageAnalytics, setPageAnalytics] = useState(1)
    
    const [searchOrgs, setSearchOrgs] = useState('')
    const [pageOrgs, setPageOrgs] = useState(1)

    const [searchUsers, setSearchUsers] = useState('')
    const [pageUsers, setPageUsers] = useState(1)

    const ITEMS_PER_PAGE = 10

    useEffect(() => {
        const controller = new AbortController()
        loadData(controller.signal)
        return () => controller.abort()
    }, [])

    async function loadData(signal = undefined) {
        setLoading(true)
        const config = signal ? { signal } : {}
        try {
            const [metricsRes, errorsRes, usersRes, orgsRes, analyticsRes] = await Promise.all([
                api.get('/admin/metrics/', config),
                api.get('/admin/errors/', config),
                api.get('/admin/users/', config).catch(() => ({ data: [] })),
                api.get('/admin/organizations/', config).catch(() => ({ data: [] })),
                api.get('/admin/analytics/organizations/', config).catch(() => ({ data: [] })),
            ])
            setMetrics(metricsRes.data)
            setErrors(errorsRes.data)
            setUsers(usersRes.data)
            setOrgs(orgsRes.data)
            setAnalytics(analyticsRes.data)
        } catch (err) {
            if (err.code === 'ERR_CANCELED') return
            console.error('Failed to load admin data:', err)
        } finally {
            setLoading(false)
        }
    }



    if (loading) return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <Skeleton className="h-8 w-56" />
                <Skeleton className="h-9 w-9 rounded-lg" />
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {[1,2,3,4,5,6].map(i => (
                    <Card key={i}><CardContent className="p-5"><Skeleton className="h-20 w-full rounded-lg" /></CardContent></Card>
                ))}
            </div>
        </div>
    )

    if (!metrics) return (
        <div className="text-center py-20 text-muted-foreground">
            <ShieldCheck className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p>No tienes permisos de administrador.</p>
        </div>
    )

    const overviewCards = [
        { label: 'Usuarios',          value: metrics.users.total,              sub: `${metrics.users.active_last_30d} activos (30d)`, icon: Users,        color: 'from-blue-500 to-blue-600' },
        { label: 'Admins',            value: metrics.users.admins,             sub: '',                                                icon: ShieldCheck,  color: 'from-red-500 to-red-600' },
        { label: 'Organizaciones',    value: metrics.organizations.total,      sub: '',                                                icon: Building,     color: 'from-purple-500 to-purple-600' },
        { label: 'Escaneos Totales',  value: metrics.scans.total,              sub: `${metrics.scans.last_7_days} últimos 7 días`,     icon: ScanSearch,   color: 'from-cyan-500 to-cyan-600' },
        { label: 'Hallazgos Altos',   value: metrics.findings.high,            sub: `${metrics.findings.total} total`,                 icon: AlertTriangle, color: 'from-red-500 to-red-600' },
        { label: 'Emails Enviados',   value: metrics.emails.sent_last_30d,     sub: `${metrics.emails.failed_last_30d} fallidos`,      icon: Mail,         color: 'from-emerald-500 to-emerald-600' },
    ]

    const filteredAnalytics = analytics.filter(org => org.name.toLowerCase().includes(searchAnalytics.toLowerCase()))
    const paginatedAnalytics = filteredAnalytics.slice((pageAnalytics - 1) * ITEMS_PER_PAGE, pageAnalytics * ITEMS_PER_PAGE)
    const totalPagesAnalytics = Math.ceil(filteredAnalytics.length / ITEMS_PER_PAGE) || 1

    const filteredOrgs = orgs.filter(org => org.name.toLowerCase().includes(searchOrgs.toLowerCase()))
    const paginatedOrgs = filteredOrgs.slice((pageOrgs - 1) * ITEMS_PER_PAGE, pageOrgs * ITEMS_PER_PAGE)
    const totalPagesOrgs = Math.ceil(filteredOrgs.length / ITEMS_PER_PAGE) || 1

    const filteredUsers = users.filter(user => user.email.toLowerCase().includes(searchUsers.toLowerCase()))
    const paginatedUsers = filteredUsers.slice((pageUsers - 1) * ITEMS_PER_PAGE, pageUsers * ITEMS_PER_PAGE)
    const totalPagesUsers = Math.ceil(filteredUsers.length / ITEMS_PER_PAGE) || 1

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold flex items-center gap-2">
                        <ShieldCheck className="w-6 h-6 text-blue-500" /> Panel de Administración
                    </h1>
                    <p className="text-muted-foreground text-sm mt-1">Monitoreo, métricas y gestión del sistema.</p>
                </div>
                <Button variant="outline" size="icon" onClick={() => loadData()} disabled={loading}>
                    <RefreshCw className="w-4 h-4" />
                </Button>
            </div>

            <Tabs defaultValue="overview">
                <TabsList className="w-full">
                    <TabsTrigger value="overview"  className="flex-1 flex items-center justify-center gap-2 transition-all duration-300 hover:scale-[1.03] hover:bg-accent hover:text-accent-foreground data-[state=active]:shadow-md">
                        <BarChart3 className="w-4 h-4" /> General
                    </TabsTrigger>
                    <TabsTrigger value="intelligence" className="flex-1 flex items-center justify-center gap-2 transition-all duration-300 hover:scale-[1.03] hover:bg-accent hover:text-accent-foreground data-[state=active]:shadow-md">
                        <Activity className="w-4 h-4" /> Inteligencia
                    </TabsTrigger>
                    <TabsTrigger value="orgs"      className="flex-1 flex items-center justify-center gap-2 transition-all duration-300 hover:scale-[1.03] hover:bg-accent hover:text-accent-foreground data-[state=active]:shadow-md">
                        <Building className="w-4 h-4" /> Organizaciones
                    </TabsTrigger>
                    <TabsTrigger value="users"     className="flex-1 flex items-center justify-center gap-2 transition-all duration-300 hover:scale-[1.03] hover:bg-accent hover:text-accent-foreground data-[state=active]:shadow-md">
                        <Users className="w-4 h-4" /> Usuarios
                    </TabsTrigger>
                    <TabsTrigger value="errors"    className="flex-1 flex items-center justify-center gap-2 transition-all duration-300 hover:scale-[1.03] hover:bg-accent hover:text-accent-foreground data-[state=active]:shadow-md">
                        <AlertTriangle className="w-4 h-4" /> Errores
                    </TabsTrigger>
                </TabsList>

                {/* Overview */}
                <TabsContent value="overview" className="mt-4 space-y-4">
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                        {overviewCards.map((card, i) => (
                            <motion.div
                                key={card.label}
                                initial={{ opacity: 0, y: 12 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: i * 0.06 }}
                            >
                                <Card className="hover:shadow-lg hover:scale-[1.02] hover:border-primary/30 transition-all duration-300 cursor-pointer">
                                    <CardContent className="p-5">
                                        <div className="flex items-center gap-3 mb-3">
                                            <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${card.color} flex items-center justify-center`}>
                                                <card.icon className="w-5 h-5 text-white" />
                                            </div>
                                            <span className="text-sm text-muted-foreground">{card.label}</span>
                                        </div>
                                        <div className="text-3xl font-bold tabular-nums">{card.value}</div>
                                        {card.sub && <p className="text-xs text-muted-foreground mt-1">{card.sub}</p>}
                                    </CardContent>
                                </Card>
                            </motion.div>
                        ))}
                    </div>

                    {/* Plan distribution */}
                    <Card>
                        <CardHeader className="pb-3">
                            <CardTitle className="text-base flex items-center gap-2">
                                <Crown className="w-4 h-4 text-amber-500" /> Distribución de Planes
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="grid grid-cols-3 gap-4">
                                {Object.entries(metrics.organizations.by_plan || {}).map(([plan, count]) => {
                                    const cfg = planConfig[plan] || planConfig.free
                                    return (
                                        <div key={plan} className="text-center p-4 rounded-xl bg-muted/50 hover:bg-muted transition-colors">
                                            <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${cfg.gradient} flex items-center justify-center mx-auto mb-2`}>
                                                <cfg.icon className="w-5 h-5 text-white" />
                                            </div>
                                            <div className="text-2xl font-bold tabular-nums">{count}</div>
                                            <div className="text-xs text-muted-foreground capitalize">{cfg.label}</div>
                                        </div>
                                    )
                                })}
                            </div>
                        </CardContent>
                    </Card>

                    {/* Scan status */}
                    <Card>
                        <CardHeader className="pb-3">
                            <CardTitle className="text-base">Estado de Escaneos</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="flex gap-3">
                                {Object.entries(metrics.scans.by_status).map(([status, count]) => (
                                    <div key={status} className="flex-1 text-center p-3 rounded-lg bg-muted/50">
                                        <div className="text-xl font-bold tabular-nums">{count}</div>
                                        <div className="text-xs text-muted-foreground capitalize mt-0.5">{status}</div>
                                    </div>
                                ))}
                            </div>
                        </CardContent>
                    </Card>
                </TabsContent>

                {/* Intelligence / Analytics */}
                <TabsContent value="intelligence" className="mt-4">
                    <Card>
                        <CardHeader className="pb-3 flex flex-row items-center justify-between space-y-0">
                            <CardTitle className="text-base flex items-center gap-2">
                                <Activity className="w-4 h-4 text-purple-500" /> Inteligencia de Empresas
                            </CardTitle>
                            <div className="relative w-64">
                                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                                <Input
                                    placeholder="Buscar empresa..."
                                    className="pl-8"
                                    value={searchAnalytics}
                                    onChange={(e) => { setSearchAnalytics(e.target.value); setPageAnalytics(1); }}
                                />
                            </div>
                        </CardHeader>
                        <CardContent className="p-0">
                            <div className="divide-y divide-border">
                                {paginatedAnalytics.length === 0 ? (
                                    <p className="p-8 text-center text-muted-foreground text-sm">No se encontraron resultados.</p>
                                ) : (
                                    paginatedAnalytics.map((org) => (
                                        <div key={org.id} className="flex items-center justify-between p-4 hover:bg-accent/50 transition-colors">
                                            <div className="flex flex-col">
                                                <div className="flex items-center gap-2">
                                                    <span className="font-medium text-sm">{org.name}</span>
                                                    <Badge variant={org.status === 'Crítico' ? 'destructive' : org.status === 'Advertencia' ? 'warning' : 'default'} className={org.status === 'Advertencia' ? 'bg-orange-500' : ''}>
                                                        {org.status}
                                                    </Badge>
                                                </div>
                                                <div className="flex gap-3 text-xs text-muted-foreground mt-1">
                                                    <span className="flex items-center gap-1 text-destructive font-semibold"><AlertTriangle className="w-3 h-3"/> C: {org.critical_findings}</span>
                                                    <span className="flex items-center gap-1 text-orange-500 font-semibold"><AlertTriangle className="w-3 h-3"/> A: {org.high_findings}</span>
                                                    <span className="flex items-center gap-1 text-blue-500">URLs: {org.total_urls}</span>
                                                </div>
                                            </div>
                                            <Button variant="secondary" size="sm" onClick={() => setViewingAnalytics(org.id)}>
                                                Ver Análisis
                                            </Button>
                                        </div>
                                    ))
                                )}
                            </div>
                            
                            {totalPagesAnalytics > 1 && (
                                <div className="flex items-center justify-between px-4 py-3 border-t">
                                    <span className="text-sm text-muted-foreground">Página {pageAnalytics} de {totalPagesAnalytics}</span>
                                    <div className="flex gap-2">
                                        <Button variant="outline" size="sm" onClick={() => setPageAnalytics(p => Math.max(1, p - 1))} disabled={pageAnalytics === 1}>
                                            <ChevronLeft className="w-4 h-4" />
                                        </Button>
                                        <Button variant="outline" size="sm" onClick={() => setPageAnalytics(p => Math.min(totalPagesAnalytics, p + 1))} disabled={pageAnalytics === totalPagesAnalytics}>
                                            <ChevronRight className="w-4 h-4" />
                                        </Button>
                                    </div>
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </TabsContent>

                {/* Organizations */}
                <TabsContent value="orgs" className="mt-4">
                    <Card>
                        <CardHeader className="pb-3 flex flex-row items-center justify-between space-y-0">
                            <CardTitle className="text-base flex items-center gap-2">
                                <Building className="w-4 h-4 text-purple-500" /> Organizaciones ({orgs.length})
                            </CardTitle>
                            <div className="relative w-64">
                                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                                <Input
                                    placeholder="Buscar organización..."
                                    className="pl-8"
                                    value={searchOrgs}
                                    onChange={(e) => { setSearchOrgs(e.target.value); setPageOrgs(1); }}
                                />
                            </div>
                        </CardHeader>
                        <CardContent className="p-0">
                            <div className="divide-y divide-border">
                                {paginatedOrgs.length === 0 ? (
                                    <p className="p-8 text-center text-muted-foreground text-sm">No se encontraron resultados.</p>
                                ) : (
                                    paginatedOrgs.map((org) => {
                                        const cfg = planConfig[org.plan] || planConfig.free
                                        return (
                                            <div key={org.id} className="flex items-center justify-between p-4 hover:bg-accent/50 transition-colors">
                                                <div className="flex items-center gap-3">
                                                    <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${cfg.gradient} flex items-center justify-center flex-shrink-0`}>
                                                        <cfg.icon className="w-5 h-5 text-white" />
                                                    </div>
                                                    <div>
                                                        <p className="font-medium text-sm">{org.name}</p>
                                                        <div className="flex items-center gap-2 mt-0.5">
                                                            <span className={`${cfg.badge} px-2 py-0.5 rounded text-[10px] font-bold`}>
                                                                {cfg.label.toUpperCase()}
                                                            </span>
                                                            <span className="text-xs text-muted-foreground">
                                                                {org.urls_used}/{org.url_limit} URLs · {org.user_count} usuarios
                                                            </span>
                                                        </div>
                                                    </div>
                                                </div>
                                                <div className="flex items-center gap-2">
                                                    <Button variant="secondary" size="sm" onClick={() => setViewingAnalytics(org.id)}>
                                                        Ver miembros
                                                    </Button>
                                                    <Button variant="outline" size="sm" onClick={() => setEditingOrg(org)}>
                                                        Editar
                                                    </Button>
                                                </div>
                                            </div>
                                        )
                                    })
                                )}
                            </div>

                            {totalPagesOrgs > 1 && (
                                <div className="flex items-center justify-between px-4 py-3 border-t">
                                    <span className="text-sm text-muted-foreground">Página {pageOrgs} de {totalPagesOrgs}</span>
                                    <div className="flex gap-2">
                                        <Button variant="outline" size="sm" onClick={() => setPageOrgs(p => Math.max(1, p - 1))} disabled={pageOrgs === 1}>
                                            <ChevronLeft className="w-4 h-4" />
                                        </Button>
                                        <Button variant="outline" size="sm" onClick={() => setPageOrgs(p => Math.min(totalPagesOrgs, p + 1))} disabled={pageOrgs === totalPagesOrgs}>
                                            <ChevronRight className="w-4 h-4" />
                                        </Button>
                                    </div>
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </TabsContent>

                {/* Users */}
                <TabsContent value="users" className="mt-4">
                    <Card>
                        <CardHeader className="pb-3 flex flex-row items-center justify-between space-y-0">
                            <CardTitle className="text-base flex items-center gap-2">
                                <Users className="w-4 h-4 text-blue-500" /> Usuarios ({users.length})
                            </CardTitle>
                            <div className="relative w-64">
                                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                                <Input
                                    placeholder="Buscar usuario..."
                                    className="pl-8"
                                    value={searchUsers}
                                    onChange={(e) => { setSearchUsers(e.target.value); setPageUsers(1); }}
                                />
                            </div>
                        </CardHeader>
                        <CardContent className="p-0">
                            <div className="divide-y divide-border">
                                {paginatedUsers.length === 0 ? (
                                    <p className="p-8 text-center text-muted-foreground text-sm">No se encontraron resultados.</p>
                                ) : (
                                    paginatedUsers.map((u) => (
                                        <div key={u.id} className={`flex items-center justify-between p-4 hover:bg-accent/50 transition-colors ${u.is_active === false ? 'opacity-60' : ''}`}>
                                            <div>
                                                <p className="font-medium text-sm">{u.email}</p>
                                                <div className="flex items-center gap-2 mt-0.5 flex-wrap">
                                                    {u.is_active === false && (
                                                        <Badge variant="destructive" className="text-[10px]">BLOQUEADO</Badge>
                                                    )}
                                                    <span className={`role-badge-${u.role || 'user'} px-2 py-0.5 rounded text-[10px] font-bold`}>
                                                        {u.role?.toUpperCase()}
                                                    </span>
                                                    {u.organization__name && (
                                                        <span className="text-xs text-muted-foreground">{u.organization__name}</span>
                                                    )}
                                                    {u.organization__plan && (
                                                        <span className={`${planConfig[u.organization__plan]?.badge || 'plan-badge-free'} px-1.5 py-0.5 rounded text-[10px] font-bold`}>
                                                            {u.organization__plan?.toUpperCase()}
                                                        </span>
                                                    )}
                                                    {u.accepted_terms_at && (
                                                        <span className="text-[10px] text-emerald-500 flex items-center gap-0.5">
                                                            <Check className="w-3 h-3" /> T&C
                                                        </span>
                                                    )}
                                                </div>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <Button variant="outline" size="sm" onClick={() => setEditingUser(u)}>
                                                    Editar
                                                </Button>
                                            </div>
                                        </div>
                                    ))
                                )}
                            </div>
                            
                            {totalPagesUsers > 1 && (
                                <div className="flex items-center justify-between px-4 py-3 border-t">
                                    <span className="text-sm text-muted-foreground">Página {pageUsers} de {totalPagesUsers}</span>
                                    <div className="flex gap-2">
                                        <Button variant="outline" size="sm" onClick={() => setPageUsers(p => Math.max(1, p - 1))} disabled={pageUsers === 1}>
                                            <ChevronLeft className="w-4 h-4" />
                                        </Button>
                                        <Button variant="outline" size="sm" onClick={() => setPageUsers(p => Math.min(totalPagesUsers, p + 1))} disabled={pageUsers === totalPagesUsers}>
                                            <ChevronRight className="w-4 h-4" />
                                        </Button>
                                    </div>
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </TabsContent>

                {/* Errors */}
                <TabsContent value="errors" className="mt-4">
                    <Card>
                        <CardHeader className="pb-3">
                            <CardTitle className="text-base flex items-center gap-2">
                                <XCircle className="w-4 h-4 text-destructive" /> Errores Recientes
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            {errors && errors.scan_errors?.length === 0 && errors.email_errors?.length === 0 ? (
                                <p className="text-muted-foreground text-sm text-center py-4">
                                    ✅ No hay errores recientes.
                                </p>
                            ) : (
                                <div className="space-y-2 max-h-96 overflow-y-auto">
                                    {errors?.scan_errors?.map((err) => (
                                        <div key={`scan-${err.id}`} className="p-3 rounded-lg bg-destructive/5 border border-destructive/10 text-sm">
                                            <div className="flex items-center justify-between">
                                                <span className="font-medium">Scan #{err.id}</span>
                                                <span className="text-xs text-muted-foreground">
                                                    {new Date(err.started_at).toLocaleString('es-VE')}
                                                </span>
                                            </div>
                                            <p className="text-xs text-muted-foreground mt-1">{err.url_asset__url}</p>
                                            <p className="text-xs text-destructive mt-1 truncate">{err.error}</p>
                                        </div>
                                    ))}
                                    {errors?.email_errors?.map((err) => (
                                        <div key={`email-${err.id}`} className="p-3 rounded-lg bg-destructive/5 border border-destructive/10 text-sm">
                                            <div className="flex items-center justify-between">
                                                <span className="font-medium">Email {err.email_type} — {err.organization__name || 'Sin organización'}</span>
                                                <span className="text-xs text-muted-foreground">
                                                    {new Date(err.sent_at).toLocaleString('es-VE')}
                                                </span>
                                            </div>
                                            <p className="text-xs text-destructive mt-1 truncate">{err.error}</p>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </TabsContent>
            </Tabs>
            
            <EditOrgModal 
                org={editingOrg} 
                open={!!editingOrg} 
                onOpenChange={(v) => !v && setEditingOrg(null)} 
                onSuccess={() => loadData()} 
            />
            
            <EditUserModal 
                user={editingUser} 
                orgs={orgs}
                open={!!editingUser} 
                onOpenChange={(v) => !v && setEditingUser(null)} 
                onSuccess={() => loadData()} 
            />

            <OrgAnalyticsModal
                orgId={viewingAnalytics}
                open={!!viewingAnalytics}
                onOpenChange={(v) => !v && setViewingAnalytics(null)}
            />
        </div>
    )
}
