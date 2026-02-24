import { useState, useEffect } from 'react'
import api from '../lib/api'
import { formatDate, getStatusColor, getStatusLabel } from '../lib/utils'
import {
    Globe, Plus, Trash2, ScanSearch, Loader2,
    ExternalLink, AlertCircle, CheckCircle2, X,
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

    useEffect(() => { loadUrls() }, [])

    // Auto-dismiss toast
    useEffect(() => {
        if (toast) {
            const timer = setTimeout(() => setToast(null), 4000)
            return () => clearTimeout(timer)
        }
    }, [toast])

    async function loadUrls() {
        try {
            const res = await api.get('/urls/')
            setUrls(res.data.results || res.data || [])
        } catch (err) {
            console.error('Failed to load URLs:', err)
        } finally {
            setLoading(false)
        }
    }

    async function handleAddUrl(e) {
        e.preventDefault()
        setError('')
        setSubmitting(true)
        try {
            await api.post('/urls/', { url: newUrl })
            setNewUrl('')
            setToast({ type: 'success', message: 'URL registrada exitosamente.' })
            loadUrls()
        } catch (err) {
            const msg = err.response?.data
            if (typeof msg === 'object') {
                setError(Object.values(msg).flat().join(' '))
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
            loadUrls()
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
            loadUrls()
        } catch (err) {
            const msg = err.response?.data?.detail || 'Error al iniciar escaneo.'
            setToast({ type: 'error', message: msg })
        } finally {
            setScanningId(null)
        }
    }

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

            {/* Add URL Form */}
            <form onSubmit={handleAddUrl} className="glass rounded-xl p-6">
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

            {/* URL List */}
            <div className="glass rounded-xl overflow-hidden">
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
                        {urls.map((url) => (
                            <div
                                key={url.id}
                                className="flex items-center justify-between p-4 hover:bg-white/5 transition-colors"
                            >
                                <div className="flex items-center gap-3 min-w-0 flex-1">
                                    <div className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${getStatusColor(url.last_scan_status)} bg-current`} />
                                    <div className="min-w-0">
                                        <a
                                            href={url.url}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="text-sm font-medium hover:text-blue-400 transition-colors flex items-center gap-1 truncate"
                                        >
                                            {url.url}
                                            <ExternalLink className="w-3 h-3 flex-shrink-0 opacity-50" />
                                        </a>
                                        <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
                                            <span className={getStatusColor(url.last_scan_status)}>
                                                {getStatusLabel(url.last_scan_status)}
                                            </span>
                                            {url.last_scan_at && (
                                                <span>Último escaneo: {formatDate(url.last_scan_at)}</span>
                                            )}
                                            <span className="hidden sm:inline">Registrada: {formatDate(url.created_at)}</span>
                                        </div>
                                    </div>
                                </div>

                                <div className="flex items-center gap-2 ml-4">
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
                        ))}
                    </div>
                )}
            </div>
        </div>
    )
}
