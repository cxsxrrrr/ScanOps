import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import api from '../lib/api'
import { formatDate, getStatusColor, getStatusLabel, getSeverityColor, getSeverityLabel } from '../lib/utils'
import {
    ScanSearch, FileText, Loader2, Filter, Clock,
    AlertTriangle, CheckCircle2, XCircle,
} from 'lucide-react'

export default function ScanHistory() {
    const [scans, setScans] = useState([])
    const [loading, setLoading] = useState(true)
    const [filter, setFilter] = useState('all')

    useEffect(() => { loadScans() }, [])

    async function loadScans() {
        try {
            const res = await api.get('/scans/list/')
            setScans(res.data.results || res.data || [])
        } catch (err) {
            console.error('Failed to load scans:', err)
        } finally {
            setLoading(false)
        }
    }

    const filtered = filter === 'all'
        ? scans
        : scans.filter(s => s.status === filter)

    const statusIcon = (status) => {
        switch (status) {
            case 'completed': return <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            case 'running': return <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />
            case 'error': return <XCircle className="w-4 h-4 text-red-400" />
            default: return <Clock className="w-4 h-4 text-yellow-400" />
        }
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between flex-wrap gap-4">
                <div>
                    <h1 className="text-2xl font-bold flex items-center gap-2">
                        <ScanSearch className="w-6 h-6 text-purple-400" />
                        Historial de Escaneos
                    </h1>
                    <p className="text-muted-foreground text-sm mt-1">
                        Revisa los resultados de tus auditorías de seguridad.
                    </p>
                </div>

                {/* Filter */}
                <div className="flex items-center gap-2 flex-wrap">
                    <Filter className="w-4 h-4 text-muted-foreground" />
                    {['all', 'completed', 'running', 'pending', 'error'].map((f) => (
                        <button
                            key={f}
                            onClick={() => setFilter(f)}
                            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200
                ${filter === f
                                    ? 'gradient-primary text-white shadow-md shadow-blue-500/20'
                                    : 'glass hover:bg-white/10'
                                }`}
                        >
                            {f === 'all' ? 'Todos' : getStatusLabel(f)}
                        </button>
                    ))}
                </div>
            </div>

            {/* Scan list */}
            <div className="glass rounded-xl overflow-hidden">
                {loading ? (
                    <div className="flex items-center justify-center py-12">
                        <Loader2 className="w-6 h-6 animate-spin text-purple-400" />
                    </div>
                ) : filtered.length === 0 ? (
                    <div className="text-center py-12 text-muted-foreground">
                        <ScanSearch className="w-12 h-12 mx-auto mb-3 opacity-30 empty-state-icon" />
                        <p className="font-medium">No hay escaneos que mostrar.</p>
                    </div>
                ) : (
                    <div className="divide-y divide-white/5">
                        {filtered.map((scan) => (
                            <Link
                                key={scan.id}
                                to={`/scans/${scan.id}/report`}
                                className="flex items-center justify-between p-4 hover:bg-white/5 transition-colors group"
                            >
                                <div className="flex items-center gap-3 min-w-0 flex-1">
                                    {statusIcon(scan.status)}
                                    <div className="min-w-0">
                                        <p className="text-sm font-medium truncate group-hover:text-blue-400 transition-colors">
                                            {scan.url}
                                        </p>
                                        <p className="text-xs text-muted-foreground mt-0.5">
                                            {formatDate(scan.started_at)}
                                            {scan.finished_at && ` — ${formatDate(scan.finished_at)}`}
                                        </p>
                                    </div>
                                </div>

                                <div className="flex items-center gap-3 ml-4">
                                    {scan.critical_count > 0 && (
                                        <span className="severity-critical px-2 py-0.5 rounded text-xs font-medium flex items-center gap-1">
                                            <AlertTriangle className="w-3 h-3" />
                                            {scan.critical_count}
                                        </span>
                                    )}
                                    {scan.high_count > 0 && (
                                        <span className="severity-high px-2 py-0.5 rounded text-xs font-medium flex items-center gap-1">
                                            <AlertTriangle className="w-3 h-3" />
                                            {scan.high_count}
                                        </span>
                                    )}
                                    {scan.medium_count > 0 && (
                                        <span className="severity-medium px-2 py-0.5 rounded text-xs font-medium">
                                            {scan.medium_count}
                                        </span>
                                    )}
                                    {scan.low_count > 0 && (
                                        <span className="severity-low px-2 py-0.5 rounded text-xs font-medium">
                                            {scan.low_count}
                                        </span>
                                    )}
                                    <span className={`text-xs font-medium ${getStatusColor(scan.status)}`}>
                                        {getStatusLabel(scan.status)}
                                    </span>
                                    <FileText className="w-4 h-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                                </div>
                            </Link>
                        ))}
                    </div>
                )}
            </div>
        </div>
    )
}
