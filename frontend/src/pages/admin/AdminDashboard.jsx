import { useState, useEffect } from 'react'
import api from '../../lib/api'
import {
    ShieldCheck, Users, ScanSearch, AlertTriangle,
    Mail, Loader2, RefreshCw, XCircle,
} from 'lucide-react'

export default function AdminDashboard() {
    const [metrics, setMetrics] = useState(null)
    const [errors, setErrors] = useState(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => { loadData() }, [])

    async function loadData() {
        setLoading(true)
        try {
            const [metricsRes, errorsRes] = await Promise.all([
                api.get('/admin/metrics/'),
                api.get('/admin/errors/'),
            ])
            setMetrics(metricsRes.data)
            setErrors(errorsRes.data)
        } catch (err) {
            console.error('Failed to load admin data:', err)
        } finally {
            setLoading(false)
        }
    }

    if (loading) {
        return (
            <div className="flex items-center justify-center py-20">
                <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
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

    const cards = [
        { label: 'Usuarios', value: metrics.users.total, sub: `${metrics.users.active_last_30d} activos (30d)`, icon: Users, color: 'from-blue-500 to-blue-600' },
        { label: 'Organizaciones', value: metrics.organizations.total, sub: '', icon: ShieldCheck, color: 'from-purple-500 to-purple-600' },
        { label: 'Escaneos Totales', value: metrics.scans.total, sub: `${metrics.scans.last_7_days} últimos 7 días`, icon: ScanSearch, color: 'from-cyan-500 to-cyan-600' },
        { label: 'Hallazgos Altos', value: metrics.findings.high, sub: `${metrics.findings.total} total`, icon: AlertTriangle, color: 'from-red-500 to-red-600' },
        { label: 'Emails Enviados', value: metrics.emails.sent_last_30d, sub: `${metrics.emails.failed_last_30d} fallidos`, icon: Mail, color: 'from-emerald-500 to-emerald-600' },
        { label: 'Errores Escaneo', value: metrics.scans.errors_last_30d, sub: 'últimos 30 días', icon: XCircle, color: 'from-amber-500 to-amber-600' },
    ]

    return (
        <div className="space-y-6 animate-fade-in">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold flex items-center gap-2">
                        <ShieldCheck className="w-6 h-6 text-blue-500" />
                        Panel de Administración
                    </h1>
                    <p className="text-muted-foreground text-sm mt-1">
                        Monitoreo y métricas del sistema.
                    </p>
                </div>
                <button
                    onClick={loadData}
                    className="p-2 rounded-lg glass hover:bg-gray-100 dark:hover:bg-white/10 transition-colors"
                >
                    <RefreshCw className="w-4 h-4" />
                </button>
            </div>

            {/* Metric cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {cards.map((card) => (
                    <div key={card.label} className="glass rounded-xl p-5 hover:scale-[1.02] transition-transform">
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

            {/* Scan status breakdown */}
            <div className="glass rounded-xl p-6">
                <h2 className="text-lg font-semibold mb-4">Estado de Escaneos</h2>
                <div className="flex gap-4">
                    {Object.entries(metrics.scans.by_status).map(([status, count]) => (
                        <div key={status} className="flex-1 text-center p-3 rounded-lg bg-gray-100 dark:bg-white/5">
                            <div className="text-xl font-bold">{count}</div>
                            <div className="text-xs text-muted-foreground capitalize">{status}</div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Recent errors */}
            {errors && (
                <div className="glass rounded-xl p-6">
                    <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                        <XCircle className="w-5 h-5 text-red-500" />
                        Errores Recientes
                    </h2>
                    {errors.scan_errors?.length === 0 && errors.email_errors?.length === 0 ? (
                        <p className="text-muted-foreground text-sm text-center py-4">
                            ✅ No hay errores recientes.
                        </p>
                    ) : (
                        <div className="space-y-2 max-h-64 overflow-y-auto custom-scrollbar">
                            {errors.scan_errors?.map((err) => (
                                <div key={`scan-${err.id}`} className="p-3 rounded-lg bg-red-500/5 border border-red-500/10 text-sm">
                                    <div className="flex items-center justify-between">
                                        <span className="font-medium">Scan #{err.id}</span>
                                        <span className="text-xs text-muted-foreground">{new Date(err.started_at).toLocaleString('es-VE')}</span>
                                    </div>
                                    <p className="text-xs text-muted-foreground mt-1">{err.url_asset__url}</p>
                                    <p className="text-xs text-red-600 dark:text-red-400 mt-1 truncate">{err.error}</p>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}
        </div>
    )
}
