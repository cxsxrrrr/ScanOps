import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useUser } from '@clerk/clerk-react'
import api from '../lib/api'
import { formatDate, getStatusColor, getStatusLabel } from '../lib/utils'
import {
    Globe,
    ScanSearch,
    AlertTriangle,
    Shield,
    ArrowRight,
    TrendingUp,
    Activity,
} from 'lucide-react'

export default function Dashboard() {
    const { user } = useUser()
    const [stats, setStats] = useState(null)
    const [recentScans, setRecentScans] = useState([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        loadDashboard()
    }, [])

    async function loadDashboard() {
        try {
            const [urlsRes, scansRes] = await Promise.all([
                api.get('/urls/').catch(() => ({ data: { results: [] } })),
                api.get('/scans/list/').catch(() => ({ data: { results: [] } })),
            ])

            const urls = urlsRes.data.results || urlsRes.data || []
            const scans = scansRes.data.results || scansRes.data || []

            setStats({
                totalUrls: urls.length,
                totalScans: scans.length,
                highFindings: scans.reduce((acc, s) => acc + (s.high_count || 0), 0),
                completedScans: scans.filter(s => s.status === 'completed').length,
            })
            setRecentScans(scans.slice(0, 5))
        } catch (err) {
            console.error('Failed to load dashboard:', err)
        } finally {
            setLoading(false)
        }
    }

    const statCards = [
        {
            label: 'URLs Registradas',
            value: stats?.totalUrls || 0,
            icon: Globe,
            color: 'from-blue-500 to-blue-600',
            shadow: 'shadow-blue-500/20',
        },
        {
            label: 'Escaneos Totales',
            value: stats?.totalScans || 0,
            icon: ScanSearch,
            color: 'from-purple-500 to-purple-600',
            shadow: 'shadow-purple-500/20',
        },
        {
            label: 'Hallazgos Altos',
            value: stats?.highFindings || 0,
            icon: AlertTriangle,
            color: 'from-red-500 to-red-600',
            shadow: 'shadow-red-500/20',
        },
        {
            label: 'Escaneos Exitosos',
            value: stats?.completedScans || 0,
            icon: Shield,
            color: 'from-emerald-500 to-emerald-600',
            shadow: 'shadow-emerald-500/20',
        },
    ]

    return (
        <div className="space-y-8 animate-fade-in">
            {/* Welcome */}
            <div>
                <h1 className="text-3xl font-bold">
                    Hola, <span className="bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">{user?.firstName || 'Usuario'}</span> 👋
                </h1>
                <p className="text-muted-foreground mt-1">
                    Aquí tienes un resumen de la seguridad de tus sitios web.
                </p>
            </div>

            {/* Stat cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {statCards.map((card) => (
                    <div
                        key={card.label}
                        className={`glass rounded-xl p-5 hover:scale-[1.02] transition-all duration-300 cursor-default shadow-lg ${card.shadow}`}
                    >
                        <div className="flex items-center justify-between mb-3">
                            <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${card.color} flex items-center justify-center shadow-lg`}>
                                <card.icon className="w-5 h-5 text-white" />
                            </div>
                            <TrendingUp className="w-4 h-4 text-muted-foreground" />
                        </div>
                        <div className="text-3xl font-bold">{card.value}</div>
                        <div className="text-sm text-muted-foreground mt-1">{card.label}</div>
                    </div>
                ))}
            </div>

            {/* Quick actions + Recent scans */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Quick actions */}
                <div className="glass rounded-xl p-6">
                    <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                        <Activity className="w-5 h-5 text-blue-400" />
                        Acciones Rápidas
                    </h2>
                    <div className="space-y-3">
                        <Link
                            to="/urls"
                            className="flex items-center justify-between p-3 rounded-lg hover:bg-white/5 transition-colors group"
                        >
                            <div className="flex items-center gap-3">
                                <Globe className="w-5 h-5 text-blue-400" />
                                <span className="text-sm">Registrar nueva URL</span>
                            </div>
                            <ArrowRight className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity" />
                        </Link>
                        <Link
                            to="/scans"
                            className="flex items-center justify-between p-3 rounded-lg hover:bg-white/5 transition-colors group"
                        >
                            <div className="flex items-center gap-3">
                                <ScanSearch className="w-5 h-5 text-purple-400" />
                                <span className="text-sm">Ver escaneos</span>
                            </div>
                            <ArrowRight className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity" />
                        </Link>
                        <Link
                            to="/settings"
                            className="flex items-center justify-between p-3 rounded-lg hover:bg-white/5 transition-colors group"
                        >
                            <div className="flex items-center gap-3">
                                <Shield className="w-5 h-5 text-emerald-400" />
                                <span className="text-sm">Configurar notificaciones</span>
                            </div>
                            <ArrowRight className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity" />
                        </Link>
                    </div>
                </div>

                {/* Recent scans */}
                <div className="lg:col-span-2 glass rounded-xl p-6">
                    <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                        <ScanSearch className="w-5 h-5 text-purple-400" />
                        Escaneos Recientes
                    </h2>
                    {recentScans.length === 0 ? (
                        <div className="text-center py-8 text-muted-foreground">
                            <ScanSearch className="w-12 h-12 mx-auto mb-3 opacity-30" />
                            <p>No hay escaneos aún.</p>
                            <p className="text-sm mt-1">Registra una URL para comenzar.</p>
                        </div>
                    ) : (
                        <div className="space-y-2">
                            {recentScans.map((scan) => (
                                <Link
                                    key={scan.id}
                                    to={`/scans/${scan.id}/report`}
                                    className="flex items-center justify-between p-3 rounded-lg hover:bg-white/5 transition-colors"
                                >
                                    <div className="flex items-center gap-3 min-w-0">
                                        <div className={`w-2 h-2 rounded-full ${getStatusColor(scan.status)} bg-current`} />
                                        <span className="text-sm truncate">{scan.url}</span>
                                    </div>
                                    <div className="flex items-center gap-4 text-sm text-muted-foreground">
                                        <span className={getStatusColor(scan.status)}>
                                            {getStatusLabel(scan.status)}
                                        </span>
                                        <span className="hidden sm:inline">{formatDate(scan.started_at)}</span>
                                        {scan.high_count > 0 && (
                                            <span className="severity-high px-2 py-0.5 rounded text-xs font-medium">
                                                {scan.high_count} Alto
                                            </span>
                                        )}
                                    </div>
                                </Link>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}
