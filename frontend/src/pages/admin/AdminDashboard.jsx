import { useState, useEffect } from 'react'
import api from '../../lib/api'
import {
    ShieldCheck, Users, ScanSearch, AlertTriangle,
    Mail, Loader2, RefreshCw, XCircle, Building,
    Crown, Zap, Shield, ChevronDown, Check,
} from 'lucide-react'

const planConfig = {
    free: { icon: Shield, label: 'Free', gradient: 'from-gray-500 to-gray-600', badge: 'plan-badge-free' },
    pro: { icon: Zap, label: 'Pro', gradient: 'from-purple-500 to-purple-600', badge: 'plan-badge-pro' },
    ultimate: { icon: Crown, label: 'Ultimate', gradient: 'from-amber-500 to-orange-500', badge: 'plan-badge-ultimate' },
}

export default function AdminDashboard() {
    const [metrics, setMetrics] = useState(null)
    const [errors, setErrors] = useState(null)
    const [users, setUsers] = useState([])
    const [orgs, setOrgs] = useState([])
    const [loading, setLoading] = useState(true)
    const [activeTab, setActiveTab] = useState('overview')
    const [updatingPlan, setUpdatingPlan] = useState(null)
    const [updatingRole, setUpdatingRole] = useState(null)

    useEffect(() => { loadData() }, [])

    async function loadData() {
        setLoading(true)
        try {
            const [metricsRes, errorsRes, usersRes, orgsRes] = await Promise.all([
                api.get('/admin/metrics/'),
                api.get('/admin/errors/'),
                api.get('/admin/users/').catch(() => ({ data: [] })),
                api.get('/admin/organizations/').catch(() => ({ data: [] })),
            ])
            setMetrics(metricsRes.data)
            setErrors(errorsRes.data)
            setUsers(usersRes.data)
            setOrgs(orgsRes.data)
        } catch (err) {
            console.error('Failed to load admin data:', err)
        } finally {
            setLoading(false)
        }
    }

    async function handleChangePlan(orgId, newPlan) {
        setUpdatingPlan(orgId)
        try {
            await api.patch(`/admin/organizations/${orgId}/plan/`, { plan: newPlan })
            loadData()
        } catch (err) {
            console.error('Failed to update plan:', err)
        } finally {
            setUpdatingPlan(null)
        }
    }

    async function handleChangeRole(userId, newRole) {
        setUpdatingRole(userId)
        try {
            await api.patch(`/admin/users/${userId}/role/`, { role: newRole })
            loadData()
        } catch (err) {
            console.error('Failed to update role:', err)
        } finally {
            setUpdatingRole(null)
        }
    }

    if (loading) {
        return (
            <div className="flex items-center justify-center py-20">
                <Loader2 className="w-8 h-8 animate-spin text-blue-400" />
            </div>
        )
    }

    if (!metrics) {
        return (
            <div className="text-center py-20 text-muted-foreground">
                <ShieldCheck className="w-12 h-12 mx-auto mb-3 opacity-30" />
                <p>No tienes permisos de administrador.</p>
            </div>
        )
    }

    const overviewCards = [
        { label: 'Usuarios', value: metrics.users.total, sub: `${metrics.users.active_last_30d} activos (30d)`, icon: Users, color: 'from-blue-500 to-blue-600' },
        { label: 'Admins', value: metrics.users.admins, sub: '', icon: ShieldCheck, color: 'from-red-500 to-red-600' },
        { label: 'Organizaciones', value: metrics.organizations.total, sub: '', icon: Building, color: 'from-purple-500 to-purple-600' },
        { label: 'Escaneos Totales', value: metrics.scans.total, sub: `${metrics.scans.last_7_days} últimos 7 días`, icon: ScanSearch, color: 'from-cyan-500 to-cyan-600' },
        { label: 'Hallazgos Altos', value: metrics.findings.high, sub: `${metrics.findings.total} total`, icon: AlertTriangle, color: 'from-red-500 to-red-600' },
        { label: 'Emails Enviados', value: metrics.emails.sent_last_30d, sub: `${metrics.emails.failed_last_30d} fallidos`, icon: Mail, color: 'from-emerald-500 to-emerald-600' },
    ]

    return (
        <div className="space-y-6 animate-fade-in">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold flex items-center gap-2">
                        <ShieldCheck className="w-6 h-6 text-blue-400" />
                        Panel de Administración
                    </h1>
                    <p className="text-muted-foreground text-sm mt-1">
                        Monitoreo, métricas y gestión del sistema.
                    </p>
                </div>
                <button
                    onClick={loadData}
                    className="p-2 rounded-lg glass hover:bg-white/10 transition-colors"
                >
                    <RefreshCw className="w-4 h-4" />
                </button>
            </div>

            {/* Tabs */}
            <div className="flex gap-1 glass-card rounded-xl p-1">
                {[
                    { key: 'overview', label: '📊 General' },
                    { key: 'orgs', label: '🏢 Organizaciones' },
                    { key: 'users', label: '👥 Usuarios' },
                    { key: 'errors', label: '⚠️ Errores' },
                ].map(tab => (
                    <button
                        key={tab.key}
                        onClick={() => setActiveTab(tab.key)}
                        className={`flex-1 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors
                            ${activeTab === tab.key ? 'gradient-primary text-white' : 'hover:bg-white/5'}`}
                    >
                        {tab.label}
                    </button>
                ))}
            </div>

            {/* Tab Content */}
            {activeTab === 'overview' && (
                <div className="space-y-6">
                    {/* Metric cards */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                        {overviewCards.map((card) => (
                            <div key={card.label} className="glass-card rounded-xl p-5 hover:scale-[1.02] transition-transform">
                                <div className="flex items-center gap-3 mb-3">
                                    <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${card.color} flex items-center justify-center`}>
                                        <card.icon className="w-5 h-5 text-white" />
                                    </div>
                                    <span className="text-sm text-muted-foreground">{card.label}</span>
                                </div>
                                <div className="text-3xl font-bold">{card.value}</div>
                                {card.sub && <div className="text-xs text-muted-foreground mt-1">{card.sub}</div>}
                            </div>
                        ))}
                    </div>

                    {/* Plan distribution */}
                    <div className="glass-card rounded-xl p-6">
                        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                            <Crown className="w-5 h-5 text-amber-400" />
                            Distribución de Planes
                        </h2>
                        <div className="grid grid-cols-3 gap-4">
                            {Object.entries(metrics.organizations.by_plan || {}).map(([plan, count]) => {
                                const config = planConfig[plan] || planConfig.free
                                const PlanIcon = config.icon
                                return (
                                    <div key={plan} className="text-center p-4 rounded-xl bg-white/5 hover:bg-white/10 transition-colors">
                                        <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${config.gradient} flex items-center justify-center mx-auto mb-2`}>
                                            <PlanIcon className="w-5 h-5 text-white" />
                                        </div>
                                        <div className="text-2xl font-bold">{count}</div>
                                        <div className="text-xs text-muted-foreground capitalize">{config.label}</div>
                                    </div>
                                )
                            })}
                        </div>
                    </div>

                    {/* Scan status breakdown */}
                    <div className="glass-card rounded-xl p-6">
                        <h2 className="text-lg font-semibold mb-4">Estado de Escaneos</h2>
                        <div className="flex gap-4">
                            {Object.entries(metrics.scans.by_status).map(([status, count]) => (
                                <div key={status} className="flex-1 text-center p-3 rounded-lg bg-white/5">
                                    <div className="text-xl font-bold">{count}</div>
                                    <div className="text-xs text-muted-foreground capitalize">{status}</div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}

            {activeTab === 'orgs' && (
                <div className="glass-card rounded-xl overflow-hidden">
                    <div className="p-4 border-b border-white/10">
                        <h2 className="font-semibold flex items-center gap-2">
                            <Building className="w-5 h-5 text-purple-400" />
                            Organizaciones ({orgs.length})
                        </h2>
                    </div>
                    <div className="divide-y divide-white/5">
                        {orgs.length === 0 ? (
                            <div className="p-8 text-center text-muted-foreground">
                                No hay organizaciones registradas.
                            </div>
                        ) : (
                            orgs.map((org) => {
                                const config = planConfig[org.plan] || planConfig.free
                                const PlanIcon = config.icon
                                return (
                                    <div key={org.id} className="flex items-center justify-between p-4 hover:bg-white/5 transition-colors">
                                        <div className="flex items-center gap-3">
                                            <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${config.gradient} flex items-center justify-center`}>
                                                <PlanIcon className="w-5 h-5 text-white" />
                                            </div>
                                            <div>
                                                <p className="font-medium">{org.name}</p>
                                                <div className="flex items-center gap-2 mt-0.5">
                                                    <span className={`${config.badge} px-2 py-0.5 rounded text-xs font-bold`}>
                                                        {config.label.toUpperCase()}
                                                    </span>
                                                    <span className="text-xs text-muted-foreground">
                                                        {org.urls_used}/{org.url_limit} URLs • {org.user_count} usuarios
                                                    </span>
                                                </div>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            <select
                                                value={org.plan}
                                                onChange={(e) => handleChangePlan(org.id, e.target.value)}
                                                disabled={updatingPlan === org.id}
                                                className="px-3 py-1.5 rounded-lg bg-white/5 border border-white/10 text-sm outline-none cursor-pointer"
                                            >
                                                <option value="free">Free</option>
                                                <option value="pro">Pro</option>
                                                <option value="ultimate">Ultimate</option>
                                            </select>
                                            {updatingPlan === org.id && (
                                                <Loader2 className="w-4 h-4 animate-spin text-blue-400" />
                                            )}
                                        </div>
                                    </div>
                                )
                            })
                        )}
                    </div>
                </div>
            )}

            {activeTab === 'users' && (
                <div className="glass-card rounded-xl overflow-hidden">
                    <div className="p-4 border-b border-white/10">
                        <h2 className="font-semibold flex items-center gap-2">
                            <Users className="w-5 h-5 text-blue-400" />
                            Usuarios ({users.length})
                        </h2>
                    </div>
                    <div className="divide-y divide-white/5">
                        {users.length === 0 ? (
                            <div className="p-8 text-center text-muted-foreground">
                                No hay usuarios registrados.
                            </div>
                        ) : (
                            users.map((u) => (
                                <div key={u.id} className="flex items-center justify-between p-4 hover:bg-white/5 transition-colors">
                                    <div>
                                        <p className="font-medium">{u.email}</p>
                                        <div className="flex items-center gap-2 mt-0.5">
                                            <span className={`${u.role === 'admin' ? 'role-badge-admin' : 'role-badge-user'} px-2 py-0.5 rounded text-xs font-bold`}>
                                                {u.role?.toUpperCase()}
                                            </span>
                                            {u.organization__name && (
                                                <span className="text-xs text-muted-foreground">
                                                    {u.organization__name}
                                                </span>
                                            )}
                                            {u.organization__plan && (
                                                <span className={`${planConfig[u.organization__plan]?.badge || 'plan-badge-free'} px-1.5 py-0.5 rounded text-[10px] font-bold`}>
                                                    {u.organization__plan?.toUpperCase()}
                                                </span>
                                            )}
                                            {u.accepted_terms_at && (
                                                <span className="text-xs text-emerald-400 flex items-center gap-0.5">
                                                    <Check className="w-3 h-3" /> T&C
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <select
                                            value={u.role}
                                            onChange={(e) => handleChangeRole(u.id, e.target.value)}
                                            disabled={updatingRole === u.id}
                                            className="px-3 py-1.5 rounded-lg bg-white/5 border border-white/10 text-sm outline-none cursor-pointer"
                                        >
                                            <option value="user">User</option>
                                            <option value="admin">Admin</option>
                                        </select>
                                        {updatingRole === u.id && (
                                            <Loader2 className="w-4 h-4 animate-spin text-blue-400" />
                                        )}
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                </div>
            )}

            {activeTab === 'errors' && errors && (
                <div className="glass-card rounded-xl p-6">
                    <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                        <XCircle className="w-5 h-5 text-red-400" />
                        Errores Recientes
                    </h2>
                    {errors.scan_errors?.length === 0 && errors.email_errors?.length === 0 ? (
                        <p className="text-muted-foreground text-sm text-center py-4">
                            ✅ No hay errores recientes.
                        </p>
                    ) : (
                        <div className="space-y-2 max-h-96 overflow-y-auto custom-scrollbar">
                            {errors.scan_errors?.map((err) => (
                                <div key={`scan-${err.id}`} className="p-3 rounded-lg bg-red-500/5 border border-red-500/10 text-sm">
                                    <div className="flex items-center justify-between">
                                        <span className="font-medium">Scan #{err.id}</span>
                                        <span className="text-xs text-muted-foreground">{new Date(err.started_at).toLocaleString('es-VE')}</span>
                                    </div>
                                    <p className="text-xs text-muted-foreground mt-1">{err.url_asset__url}</p>
                                    <p className="text-xs text-red-400 mt-1 truncate">{err.error}</p>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}
        </div>
    )
}
