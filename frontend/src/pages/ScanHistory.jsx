import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import api from '../lib/api'
import { formatDate, getStatusColor, getStatusLabel } from '../lib/utils'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Button } from '@/components/ui/button'
import {
    ScanSearch, FileText, Loader2, Filter, Clock,
    AlertTriangle, CheckCircle2, XCircle,
} from 'lucide-react'

const FILTERS = [
    { key: 'all',       label: 'Todos' },
    { key: 'completed', label: 'Completado' },
    { key: 'running',   label: 'En progreso' },
    { key: 'pending',   label: 'Pendiente' },
    { key: 'error',     label: 'Error' },
]

function StatusIcon({ status }) {
    switch (status) {
        case 'completed': return <CheckCircle2 className="w-4 h-4 text-emerald-500" />
        case 'running':   return <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />
        case 'error':     return <XCircle className="w-4 h-4 text-red-500" />
        default:          return <Clock className="w-4 h-4 text-amber-500" />
    }
}

export default function ScanHistory() {
    const [scans,   setScans]   = useState([])
    const [loading, setLoading] = useState(true)
    const [filter,  setFilter]  = useState('all')

    useEffect(() => {
        const controller = new AbortController()
        loadScans(controller.signal)
        return () => controller.abort()
    }, [])

    async function loadScans(signal) {
        try {
            const res = await api.get('/scans/list/', { signal })
            setScans(res.data.results || res.data || [])
        } catch (err) {
            if (err.code === 'ERR_CANCELED') return
            console.error('Failed to load scans:', err)
        } finally {
            setLoading(false)
        }
    }

    const filtered = filter === 'all' ? scans : scans.filter(s => s.status === filter)

    return (
        <div className="space-y-5">
            <div className="flex items-start justify-between flex-wrap gap-4">
                <div>
                    <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
                        <ScanSearch className="w-6 h-6 text-purple-500" /> Historial de Escaneos
                    </h1>
                    <p className="text-muted-foreground text-sm mt-1">
                        Revisa los resultados de tus auditorías de seguridad.
                    </p>
                </div>

                {/* Filters */}
                <div className="flex items-center gap-1.5 flex-wrap">
                    <Filter className="w-3.5 h-3.5 text-muted-foreground mr-0.5" />
                    {FILTERS.map(({ key, label }) => (
                        <Button
                            key={key}
                            variant={filter === key ? 'default' : 'outline'}
                            size="sm"
                            onClick={() => setFilter(key)}
                            className={`h-7 text-xs px-3 ${filter === key ? '' : 'text-muted-foreground'}`}
                        >
                            {label}
                        </Button>
                    ))}
                </div>
            </div>

            <Card>
                {loading ? (
                    <CardContent className="py-8 flex justify-center">
                        <Loader2 className="w-6 h-6 animate-spin text-purple-500" />
                    </CardContent>
                ) : filtered.length === 0 ? (
                    <CardContent className="py-14 text-center text-muted-foreground">
                        <ScanSearch className="w-10 h-10 mx-auto mb-3 opacity-25 empty-state-icon" />
                        <p className="text-sm font-medium">Sin escaneos que mostrar</p>
                        <p className="text-xs mt-1">Cambia el filtro o inicia un nuevo escaneo.</p>
                    </CardContent>
                ) : (
                    <CardContent className="p-0">
                        <div className="divide-y divide-border">
                            {filtered.map((scan, i) => (
                                <motion.div
                                    key={scan.id}
                                    initial={{ opacity: 0, y: 6 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ delay: i * 0.04, duration: 0.25 }}
                                >
                                    <Link
                                        to={`/scans/${scan.id}/report`}
                                        className="flex items-center justify-between p-4 hover:bg-accent/50 transition-colors group"
                                    >
                                        <div className="flex items-center gap-3 min-w-0 flex-1">
                                            <StatusIcon status={scan.status} />
                                            <div className="min-w-0">
                                                <p className="text-sm font-medium truncate group-hover:text-blue-500 transition-colors">
                                                    {scan.url}
                                                </p>
                                                <p className="text-xs text-muted-foreground mt-0.5">
                                                    {formatDate(scan.started_at)}
                                                    {scan.finished_at && ` — ${formatDate(scan.finished_at)}`}
                                                </p>
                                            </div>
                                        </div>

                                        <div className="flex items-center gap-2 ml-4 flex-shrink-0">
                                            {scan.critical_count > 0 && (
                                                <Badge className="severity-critical text-[10px] px-1.5 py-0 border">
                                                    <AlertTriangle className="w-2.5 h-2.5 mr-0.5" />{scan.critical_count}
                                                </Badge>
                                            )}
                                            {scan.high_count > 0 && (
                                                <Badge className="severity-high text-[10px] px-1.5 py-0 border">
                                                    <AlertTriangle className="w-2.5 h-2.5 mr-0.5" />{scan.high_count}
                                                </Badge>
                                            )}
                                            {scan.medium_count > 0 && (
                                                <Badge className="severity-medium text-[10px] px-1.5 py-0 border">{scan.medium_count}</Badge>
                                            )}
                                            {scan.low_count > 0 && (
                                                <Badge className="severity-low text-[10px] px-1.5 py-0 border">{scan.low_count}</Badge>
                                            )}
                                            <span className={`text-xs font-medium ${getStatusColor(scan.status)}`}>
                                                {getStatusLabel(scan.status)}
                                            </span>
                                            <FileText className="w-3.5 h-3.5 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                                        </div>
                                    </Link>
                                </motion.div>
                            ))}
                        </div>
                    </CardContent>
                )}
            </Card>
        </div>
    )
}
