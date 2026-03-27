import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import api from '../lib/api'
import { formatDate, getStatusColor, getStatusLabel } from '../lib/utils'
import {
    Globe, Plus, Trash2, ScanSearch, Loader2,
    ExternalLink, AlertCircle, CheckCircle2, X,
    Sparkles, AlertTriangle, Lock,
} from 'lucide-react'

export default function URLs() {
    const [urls, setUrls] = useState([])
    const [loading, setLoading] = useState(true)
    const [newUrl, setNewUrl] = useState('')
    const [submitting, setSubmitting] = useState(false)
    const [error, setError] = useState('')
    const [scanningId, setScanningId] = useState(null)
    const [deleteConfirmId, setDeleteConfirmId] = useState(null)
    const [toast, setToast] = useState(null)
    const [orgData, setOrgData] = useState(null)

    useEffect(() => { loadData() }, [])

    // Auto-dismiss toast
    useEffect(() => {
        if (toast) {
            const timer = setTimeout(() => setToast(null), 4000)
            return () => clearTimeout(timer)
        }
    }, [toast])

    async function loadData() {
        try {
            const [urlsRes, orgRes] = await Promise.all([
                api.get('/urls/'),
                api.get('/auth/organization/').catch(() => ({ data: null })),
            ])
            setUrls(urlsRes.data.results || urlsRes.data || [])
            setOrgData(orgRes.data)
        } catch (err) {
            console.error('Failed to load data:', err)
        } finally {
            setLoading(false)
        }
    }

    const urlLimit = orgData?.url_limit || 1
    const urlsUsed = urls.length
    const usagePercent = Math.min((urlsUsed / urlLimit) * 100, 100)
    const isAtLimit = urlsUsed >= urlLimit
    const currentPlan = orgData?.plan || 'free'

    async function handleAddUrl(e) {
        e.preventDefault()
        setError('')
        setSubmitting(true)
        try {
            await api.post('/urls/', { url: newUrl })
            setNewUrl('')
            setToast({ type: 'success', message: 'URL registrada exitosamente.' })
            loadData()
        } catch (err) {
            const msg = err.response?.data
            if (typeof msg === 'object') {
                const errorMsg = msg.non_field_errors
                    ? msg.non_field_errors.flat().join(' ')
                    : Object.values(msg).flat().join(' ')
                setError(errorMsg)
            } else {
                setError('Error al registrar la URL.')
            }
        } finally {
            setSubmitting(false)
        }
    }

    async function handleDelete(id) {
        try {
            await api.delete(`/urls/${id}/`)
            setDeleteConfirmId(null)
            setToast({ type: 'success', message: 'URL eliminada correctamente.' })
            loadData()
        } catch (err) {
            console.error('Failed to delete URL:', err)
            setToast({ type: 'error', message: 'Error al eliminar la URL.' })
        }
    }

    async function handleScan(urlAssetId) {
        setScanningId(urlAssetId)
        try {
            await api.post('/scans/trigger/', { url_asset_id: urlAssetId })
            setToast({ type: 'success', message: 'Escaneo iniciado exitosamente.' })
            loadData()
        } catch (err) {
            const msg = err.response?.data?.detail || 'Error al iniciar escaneo.'
            setToast({ type: 'error', message: msg })
        } finally {
            setScanningId(null)
        }
    }

    // Determine which URLs are over the limit (blocked)
    const isUrlBlocked = (index) => index >= urlLimit

    return (
        <div className="space-y-6">
            {/* Toast notification */}
            {toast && (
                <div className={`fixed top-6 right-6 z-50 flex items-center gap-3 px-4 py-3 rounded-xl shadow-2xl border transition-all duration-300
                    ${toast.type === 'success'
                        ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                        : 'bg-red-500/10 border-red-500/30 text-red-400'
                    } backdrop-blur-xl`}
                >
                    {toast.type === 'success'
                        ? <CheckCircle2 className="w-5 h-5 flex-shrink-0" />
                        : <AlertCircle className="w-5 h-5 flex-shrink-0" />
                    }
                    <span className="text-sm font-medium">{toast.message}</span>
                    <button
                        onClick={() => setToast(null)}
                        className="p-0.5 hover:bg-white/10 rounded transition-colors"
                    >
                        <X className="w-3.5 h-3.5" />
                    </button>
                </div>
            )}

            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold flex items-center gap-2">
                        <Globe className="w-6 h-6 text-blue-400" />
                        URLs Registradas
                    </h1>
                    <p className="text-muted-foreground text-sm mt-1">
                        Registra y gestiona los sitios web que deseas auditar.
                    </p>
                </div>
            </div>

            {/* URL Usage indicator */}
            <div className="glass-card rounded-xl p-4">
                <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                        <span className="text-sm font-medium">URLs utilizadas</span>
                        <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${
                            currentPlan === 'ultimate' ? 'plan-badge-ultimate'
                                : currentPlan === 'pro' ? 'plan-badge-pro'
                                    : 'plan-badge-free'
                        }`}>
                            Plan {currentPlan.charAt(0).toUpperCase() + currentPlan.slice(1)}
                        </span>
                    </div>
                    <span className={`text-sm font-bold ${isAtLimit ? 'text-amber-400' : 'text-foreground'}`}>
                        {urlsUsed} / {urlLimit}
                    </span>
                </div>
                <div className="w-full h-2.5 rounded-full bg-white/10 overflow-hidden">
                    <div
                        className={`progress-bar-fill ${usagePercent >= 100 ? '!bg-gradient-to-r !from-amber-500 !to-red-500' : ''}`}
                        style={{ width: `${usagePercent}%` }}
                    />
                </div>
            </div>

            {/* Add URL Form or Upgrade Banner */}
            {isAtLimit ? (
                <div className="glass-card rounded-xl p-6 border-amber-500/20">
                    <div className="flex items-start gap-4">
                        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-amber-500 to-orange-500 flex items-center justify-center flex-shrink-0 shadow-lg shadow-amber-500/20">
                            <Lock className="w-6 h-6 text-white" />
                        </div>
                        <div className="flex-1">
                            <h3 className="font-semibold text-lg mb-1">Límite de URLs alcanzado</h3>
                            <p className="text-sm text-muted-foreground mb-4">
                                Tu plan <strong className="text-foreground capitalize">{currentPlan}</strong> permite un máximo de {urlLimit} URL{urlLimit > 1 ? 's' : ''}.
                                Actualiza tu plan para agregar más sitios web.
                            </p>
                            <Link
                                to="/plans"
                                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg gradient-primary text-white font-medium text-sm hover:opacity-90 transition-opacity shadow-lg shadow-blue-500/25"
                            >
                                <Sparkles className="w-4 h-4" />
                                Ver planes disponibles
                            </Link>
                        </div>
                    </div>
                </div>
            ) : (
                <form onSubmit={handleAddUrl} className="glass-card rounded-xl p-6">
                    <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                        <Plus className="w-5 h-5 text-emerald-400" />
                        Registrar Nueva URL
                    </h2>
                    <div className="flex gap-3">
                        <div className="flex-1 relative">
                            <Globe className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                            <input
                                type="url"
                                value={newUrl}
                                onChange={(e) => setNewUrl(e.target.value)}
                                placeholder="https://ejemplo.com"
                                className="w-full pl-10 pr-4 py-2.5 rounded-lg bg-white/5 border border-white/10 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none transition-all text-sm"
                                required
                            />
                        </div>
                        <button
                            type="submit"
                            disabled={submitting}
                            className="px-6 py-2.5 rounded-lg gradient-primary text-white font-medium text-sm hover:opacity-90 transition-opacity disabled:opacity-50 flex items-center gap-2"
                        >
                            {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
                            Registrar
                        </button>
                    </div>
                    {error && (
                        <div className="mt-3 flex items-center gap-2 text-red-400 text-sm bg-red-500/5 border border-red-500/10 p-3 rounded-lg">
                            <AlertCircle className="w-4 h-4 flex-shrink-0" />
                            {error}
                        </div>
                    )}
                </form>
            )}

            {/* URL List */}
            <div className="glass-card rounded-xl overflow-hidden">
                {loading ? (
                    <div className="divide-y divide-white/5">
                        {[1, 2, 3].map(i => (
                            <div key={i} className="flex items-center justify-between p-4">
                                <div className="flex items-center gap-3 flex-1">
                                    <div className="skeleton w-2.5 h-2.5 rounded-full" />
                                    <div className="flex-1">
                                        <div className="skeleton h-4 w-64 mb-2" />
                                        <div className="skeleton h-3 w-48" />
                                    </div>
                                </div>
                                <div className="flex items-center gap-2">
                                    <div className="skeleton h-8 w-24 rounded-lg" />
                                    <div className="skeleton h-8 w-8 rounded-lg" />
                                </div>
                            </div>
                        ))}
                    </div>
                ) : urls.length === 0 ? (
                    <div className="text-center py-12 text-muted-foreground">
                        <Globe className="w-12 h-12 mx-auto mb-3 opacity-30 empty-state-icon" />
                        <p className="font-medium">No hay URLs registradas.</p>
                        <p className="text-sm mt-1">Usa el formulario de arriba para agregar la primera.</p>
                    </div>
                ) : (
                    <div className="divide-y divide-white/5">
                        {urls.map((url, index) => {
                            const blocked = isUrlBlocked(index)
                            return (
                                <div
                                    key={url.id}
                                    className={`flex items-center justify-between p-4 transition-colors ${
                                        blocked
                                            ? 'opacity-50 bg-amber-500/5'
                                            : 'hover:bg-white/5'
                                    }`}
                                >
                                    <div className="flex items-center gap-3 min-w-0 flex-1">
                                        {blocked ? (
                                            <Lock className="w-4 h-4 text-amber-400 flex-shrink-0" />
                                        ) : (
                                            <div className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${getStatusColor(url.last_scan_status)} bg-current`} />
                                        )}
                                        <div className="min-w-0">
                                            <div className="flex items-center gap-2">
                                                <a
                                                    href={url.url}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    className={`text-sm font-medium transition-colors flex items-center gap-1 truncate ${
                                                        blocked ? 'text-muted-foreground' : 'hover:text-blue-400'
                                                    }`}
                                                >
                                                    {url.url}
                                                    <ExternalLink className="w-3 h-3 flex-shrink-0 opacity-50" />
                                                </a>
                                                {blocked && (
                                                    <span className="plan-badge-ultimate px-1.5 py-0.5 rounded text-[10px] font-bold leading-none flex-shrink-0">
                                                        BLOQUEADA
                                                    </span>
                                                )}
                                            </div>
                                            <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
                                                {blocked ? (
                                                    <span className="text-amber-400">Actualiza tu plan para desbloquear</span>
                                                ) : (
                                                    <>
                                                        <span className={getStatusColor(url.last_scan_status)}>
                                                            {getStatusLabel(url.last_scan_status)}
                                                        </span>
                                                        {url.last_scan_at && (
                                                            <span>Último escaneo: {formatDate(url.last_scan_at)}</span>
                                                        )}
                                                        <span className="hidden sm:inline">Registrada: {formatDate(url.created_at)}</span>
                                                    </>
                                                )}
                                            </div>
                                        </div>
                                    </div>

                                    <div className="flex items-center gap-2 ml-4">
                                        {!blocked && (
                                            <>
                                                <button
                                                    onClick={() => handleScan(url.id)}
                                                    disabled={scanningId === url.id}
                                                    className="px-3 py-1.5 rounded-lg bg-blue-500/10 text-blue-400 hover:bg-blue-500/20 transition-colors text-sm font-medium flex items-center gap-1.5 disabled:opacity-50"
                                                >
                                                    {scanningId === url.id ? (
                                                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                                                    ) : (
                                                        <ScanSearch className="w-3.5 h-3.5" />
                                                    )}
                                                    <span className="hidden sm:inline">Escanear</span>
                                                </button>
                                            </>
                                        )}

                                        {/* Delete with inline confirmation */}
                                        {deleteConfirmId === url.id ? (
                                            <div className="flex items-center gap-1.5 animate-fade-in">
                                                <span className="text-xs text-muted-foreground">¿Eliminar?</span>
                                                <button
                                                    onClick={() => handleDelete(url.id)}
                                                    className="px-2 py-1 rounded-md bg-red-500/20 text-red-400 hover:bg-red-500/30 transition-colors text-xs font-medium"
                                                >
                                                    Sí
                                                </button>
                                                <button
                                                    onClick={() => setDeleteConfirmId(null)}
                                                    className="px-2 py-1 rounded-md bg-white/5 text-muted-foreground hover:bg-white/10 transition-colors text-xs font-medium"
                                                >
                                                    No
                                                </button>
                                            </div>
                                        ) : (
                                            <button
                                                onClick={() => setDeleteConfirmId(url.id)}
                                                className="p-1.5 rounded-lg text-muted-foreground hover:text-red-400 hover:bg-red-500/10 transition-colors"
                                                aria-label="Eliminar URL"
                                            >
                                                <Trash2 className="w-4 h-4" />
                                            </button>
                                        )}
                                    </div>
                                </div>
                            )
                        })}
                    </div>
                )}
            </div>
        </div>
    )
}
