import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { toast } from 'sonner'
import api from '../lib/api'
import { formatDate, getStatusColor, getStatusLabel } from '../lib/utils'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Skeleton } from '@/components/ui/skeleton'
import { Alert, AlertDescription } from '@/components/ui/alert'
import {
    Globe, Plus, Trash2, ScanSearch, Loader2,
    ExternalLink, AlertCircle, Lock, Sparkles, AlertTriangle,
    Pencil, Check, X,
} from 'lucide-react'

export default function URLs() {
    const [urls,            setUrls]            = useState([])
    const [loading,         setLoading]         = useState(true)
    const [newUrl,          setNewUrl]          = useState('')
    const [newName,         setNewName]         = useState('')
    const [submitting,      setSubmitting]      = useState(false)
    const [error,           setError]           = useState('')
    const [scanningId,      setScanningId]      = useState(null)
    const [deleteConfirmId, setDeleteConfirmId] = useState(null)
    const [orgData,         setOrgData]         = useState(null)
    const [editingId,       setEditingId]       = useState(null)
    const [editName,        setEditName]        = useState('')
    const [savingName,      setSavingName]      = useState(false)

    useEffect(() => {
        const controller = new AbortController()
        loadData(controller.signal)
        return () => controller.abort()
    }, [])

    async function loadData(signal = undefined) {
        const config = signal ? { signal } : {}
        try {
            const [urlsRes, orgRes] = await Promise.all([
                api.get('/urls/', config),
                api.get('/auth/organization/', config).catch(() => ({ data: null })),
            ])
            setUrls(urlsRes.data.results || urlsRes.data || [])
            setOrgData(orgRes.data)
        } catch (err) {
            if (err.code === 'ERR_CANCELED') return
            console.error('Failed to load data:', err)
        } finally {
            setLoading(false)
        }
    }

    const urlLimit     = orgData?.url_limit || 1
    const urlsUsed     = urls.length
    const usagePercent = Math.min((urlsUsed / urlLimit) * 100, 100)
    const isAtLimit    = urlsUsed >= urlLimit
    const currentPlan  = orgData?.plan || 'free'

    async function handleAddUrl(e) {
        e.preventDefault()
        setError('')
        setSubmitting(true)
        try {
            await api.post('/urls/', { url: newUrl, name: newName.trim() })
            setNewUrl('')
            setNewName('')
            toast.success('URL registrada exitosamente.')
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

    function startEditName(url) {
        setEditingId(url.id)
        setEditName(url.name || '')
    }

    function cancelEditName() {
        setEditingId(null)
        setEditName('')
    }

    async function saveEditName(id) {
        setSavingName(true)
        try {
            await api.patch(`/urls/${id}/`, { name: editName.trim() })
            setUrls(prev => prev.map(u => u.id === id ? { ...u, name: editName.trim() } : u))
            setEditingId(null)
            toast.success('Nombre actualizado.')
        } catch {
            toast.error('Error al actualizar el nombre.')
        } finally {
            setSavingName(false)
        }
    }

    async function handleDelete(id) {
        try {
            await api.delete(`/urls/${id}/`)
            setDeleteConfirmId(null)
            toast.success('URL eliminada correctamente.')
            loadData()
        } catch {
            toast.error('Error al eliminar la URL.')
        }
    }

    async function handleScan(urlAssetId) {
        setScanningId(urlAssetId)
        try {
            await api.post('/scans/trigger/', { url_asset_id: urlAssetId })
            toast.success('Escaneo iniciado exitosamente.')
            loadData()
        } catch (err) {
            const msg = err.response?.data?.detail || 'Error al iniciar escaneo.'
            toast.error(msg)
        } finally {
            setScanningId(null)
        }
    }

    const isUrlBlocked = (index) => index >= urlLimit

    return (
        <div className="space-y-5">
            {/* Header */}
            <div>
                <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
                    <Globe className="w-6 h-6 text-blue-500" /> URLs Registradas
                </h1>
                <p className="text-muted-foreground text-sm mt-1">
                    Registra y gestiona los sitios web que deseas auditar.
                </p>
            </div>

            {/* Usage */}
            <Card>
                <CardContent className="p-4">
                    <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                            <span className="text-sm font-medium">URLs utilizadas</span>
                            <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                                currentPlan === 'ultimate' ? 'plan-badge-ultimate'
                                    : currentPlan === 'pro' ? 'plan-badge-pro'
                                    : 'plan-badge-free'
                            }`}>
                                Plan {currentPlan.charAt(0).toUpperCase() + currentPlan.slice(1)}
                            </span>
                        </div>
                        <span className={`text-sm font-bold tabular-nums ${isAtLimit ? 'text-amber-500' : ''}`}>
                            {urlsUsed} / {urlLimit}
                        </span>
                    </div>
                    <Progress value={usagePercent} className={`h-2 ${usagePercent >= 100 ? '[&>div]:bg-gradient-to-r [&>div]:from-amber-500 [&>div]:to-red-500' : ''}`} />
                </CardContent>
            </Card>

            {/* Add URL or upgrade banner */}
            <AnimatePresence mode="wait">
                {isAtLimit ? (
                    <motion.div key="limit" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
                        <Card className="border-amber-500/25">
                            <CardContent className="p-6">
                                <div className="flex items-start gap-4">
                                    <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-amber-500 to-orange-500 flex items-center justify-center flex-shrink-0 shadow-md">
                                        <Lock className="w-5 h-5 text-white" />
                                    </div>
                                    <div className="flex-1">
                                        <h3 className="font-semibold mb-1">Límite de URLs alcanzado</h3>
                                        <p className="text-sm text-muted-foreground mb-4">
                                            Tu plan <strong className="text-foreground capitalize">{currentPlan}</strong> permite máximo {urlLimit} URL{urlLimit > 1 ? 's' : ''}.
                                        </p>
                                        <Button asChild size="sm">
                                            <Link to="/plans">
                                                <Sparkles className="w-3.5 h-3.5" /> Ver planes disponibles
                                            </Link>
                                        </Button>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    </motion.div>
                ) : (
                    <motion.div key="form" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
                        <Card>
                            <CardHeader className="pb-3">
                                <CardTitle className="text-base flex items-center gap-2">
                                    <Plus className="w-4 h-4 text-emerald-500" /> Registrar Nueva URL
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                <form onSubmit={handleAddUrl} className="space-y-3">
                                    <div className="flex flex-col sm:flex-row gap-3">
                                        <div className="flex-1 relative">
                                            <Globe className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                                            <Input
                                                type="url"
                                                value={newUrl}
                                                onChange={(e) => setNewUrl(e.target.value)}
                                                placeholder="https://ejemplo.com"
                                                className="pl-9"
                                                required
                                            />
                                        </div>
                                        <div className="flex-1 sm:max-w-[220px]">
                                            <Input
                                                type="text"
                                                value={newName}
                                                onChange={(e) => setNewName(e.target.value)}
                                                placeholder="Nombre (opcional)"
                                                maxLength={120}
                                            />
                                        </div>
                                        <Button type="submit" disabled={submitting}>
                                            {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
                                            Registrar
                                        </Button>
                                    </div>
                                    {error && (
                                        <Alert variant="destructive" className="py-2">
                                            <AlertCircle className="h-4 w-4" />
                                            <AlertDescription className="text-sm">{error}</AlertDescription>
                                        </Alert>
                                    )}
                                </form>
                            </CardContent>
                        </Card>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* URL List */}
            <Card>
                {loading ? (
                    <CardContent className="p-0 divide-y divide-border">
                        {[1,2,3].map(i => (
                            <div key={i} className="flex items-center justify-between p-4">
                                <div className="flex items-center gap-3 flex-1">
                                    <Skeleton className="w-2.5 h-2.5 rounded-full" />
                                    <div className="flex-1"><Skeleton className="h-4 w-64 mb-1.5" /><Skeleton className="h-3 w-44" /></div>
                                </div>
                                <div className="flex gap-2"><Skeleton className="h-8 w-24 rounded-lg" /><Skeleton className="h-8 w-8 rounded-lg" /></div>
                            </div>
                        ))}
                    </CardContent>
                ) : urls.length === 0 ? (
                    <CardContent className="py-14 text-center text-muted-foreground">
                        <Globe className="w-10 h-10 mx-auto mb-3 opacity-25 empty-state-icon" />
                        <p className="text-sm font-medium">Sin URLs registradas</p>
                        <p className="text-xs mt-1">Usa el formulario de arriba para agregar la primera.</p>
                    </CardContent>
                ) : (
                    <CardContent className="p-0">
                        <div className="divide-y divide-border">
                            <AnimatePresence>
                                {urls.map((url, index) => {
                                    const blocked = isUrlBlocked(index)
                                    return (
                                        <motion.div
                                            key={url.id}
                                            initial={{ opacity: 0, x: -8 }}
                                            animate={{ opacity: 1, x: 0 }}
                                            exit={{ opacity: 0, x: 8 }}
                                            transition={{ delay: index * 0.04, duration: 0.25 }}
                                            className={`flex items-center justify-between p-4 transition-colors ${
                                                blocked ? 'opacity-50 bg-amber-500/3' : 'hover:bg-accent/50'
                                            }`}
                                        >
                                            <div className="flex items-center gap-3 min-w-0 flex-1">
                                                {blocked ? (
                                                    <Lock className="w-3.5 h-3.5 text-amber-400 flex-shrink-0" />
                                                ) : (
                                                    <span className={`w-2 h-2 rounded-full flex-shrink-0 ${getStatusColor(url.last_scan_status)} bg-current`} />
                                                )}
                                                <div className="min-w-0 flex-1">
                                                    {editingId === url.id ? (
                                                        <div className="flex items-center gap-1.5 mb-1">
                                                            <Input
                                                                autoFocus
                                                                value={editName}
                                                                onChange={(e) => setEditName(e.target.value)}
                                                                onKeyDown={(e) => {
                                                                    if (e.key === 'Enter') saveEditName(url.id)
                                                                    if (e.key === 'Escape') cancelEditName()
                                                                }}
                                                                placeholder="Nombre de la URL"
                                                                maxLength={120}
                                                                className="h-7 text-sm max-w-[220px]"
                                                            />
                                                            <Button
                                                                size="icon" variant="ghost" className="h-7 w-7 text-emerald-500"
                                                                disabled={savingName}
                                                                onClick={() => saveEditName(url.id)}
                                                                aria-label="Guardar nombre"
                                                            >
                                                                <Check className="w-3.5 h-3.5" />
                                                            </Button>
                                                            <Button
                                                                size="icon" variant="ghost" className="h-7 w-7 text-muted-foreground"
                                                                disabled={savingName}
                                                                onClick={cancelEditName}
                                                                aria-label="Cancelar"
                                                            >
                                                                <X className="w-3.5 h-3.5" />
                                                            </Button>
                                                        </div>
                                                    ) : (
                                                        <div className="flex items-center gap-1.5 group/name">
                                                            <a
                                                                href={url.url}
                                                                target="_blank"
                                                                rel="noopener noreferrer"
                                                                className={`text-sm font-medium transition-colors flex items-center gap-1 truncate ${
                                                                    blocked ? 'text-muted-foreground' : 'hover:text-blue-500'
                                                                }`}
                                                            >
                                                                {url.name || url.url}
                                                                <ExternalLink className="w-4 h-4 flex-shrink-0 opacity-70" />
                                                            </a>
                                                            {blocked && (
                                                                <Badge variant="outline" className="text-[10px] text-amber-500 border-amber-500/30 flex-shrink-0">
                                                                    BLOQUEADA
                                                                </Badge>
                                                            )}
                                                            <button
                                                                onClick={() => startEditName(url)}
                                                                className="opacity-0 group-hover/name:opacity-100 transition-opacity text-muted-foreground hover:text-foreground flex-shrink-0"
                                                                aria-label="Editar nombre"
                                                            >
                                                                <Pencil className="w-4 h-4" />
                                                            </button>
                                                        </div>
                                                    )}
                                                    {url.name && (
                                                        <a
                                                            href={url.url}
                                                            target="_blank"
                                                            rel="noopener noreferrer"
                                                            className="text-xs text-muted-foreground hover:text-blue-500 transition-colors flex items-center gap-1 truncate"
                                                        >
                                                            {url.url}
                                                            <ExternalLink className="w-3.5 h-3.5 flex-shrink-0 opacity-60" />
                                                        </a>
                                                    )}
                                                    <div className="flex items-center gap-3 mt-0.5 text-xs text-muted-foreground">
                                                        {blocked ? (
                                                            <span className="text-amber-500">Actualiza tu plan para desbloquear</span>
                                                        ) : (
                                                            <>
                                                                <span className={getStatusColor(url.last_scan_status)}>
                                                                    {getStatusLabel(url.last_scan_status)}
                                                                </span>
                                                                {url.last_scan_at && <span>Último: {formatDate(url.last_scan_at)}</span>}
                                                            </>
                                                        )}
                                                    </div>
                                                </div>
                                            </div>

                                            <div className="flex items-center gap-2 ml-4">
                                                {!blocked && (
                                                    <Button
                                                        variant="outline"
                                                        size="sm"
                                                        onClick={() => handleScan(url.id)}
                                                        disabled={scanningId === url.id}
                                                        className="text-blue-500 border-blue-500/25 hover:bg-blue-500/10 hover:text-blue-500"
                                                    >
                                                        {scanningId === url.id
                                                            ? <Loader2 className="w-3.5 h-3.5 animate-spin" />
                                                            : <ScanSearch className="w-3.5 h-3.5" />
                                                        }
                                                        <span className="hidden sm:inline">Escanear</span>
                                                    </Button>
                                                )}

                                                <AnimatePresence mode="wait">
                                                    {deleteConfirmId === url.id ? (
                                                        <motion.div
                                                            key="confirm"
                                                            initial={{ opacity: 0, scale: 0.9 }}
                                                            animate={{ opacity: 1, scale: 1 }}
                                                            exit={{ opacity: 0, scale: 0.9 }}
                                                            className="flex items-center gap-1.5"
                                                        >
                                                            <span className="text-xs text-muted-foreground">¿Eliminar?</span>
                                                            <Button size="sm" variant="destructive" className="h-7 px-2 text-xs" onClick={() => handleDelete(url.id)}>Sí</Button>
                                                            <Button size="sm" variant="ghost" className="h-7 px-2 text-xs" onClick={() => setDeleteConfirmId(null)}>No</Button>
                                                        </motion.div>
                                                    ) : (
                                                        <motion.div key="delete" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                                                            <Button
                                                                variant="ghost"
                                                                size="icon"
                                                                className="h-8 w-8 text-muted-foreground hover:text-red-500 hover:bg-red-500/10"
                                                                onClick={() => setDeleteConfirmId(url.id)}
                                                                aria-label="Eliminar URL"
                                                            >
                                                                <Trash2 className="w-4 h-4" />
                                                            </Button>
                                                        </motion.div>
                                                    )}
                                                </AnimatePresence>
                                            </div>
                                        </motion.div>
                                    )
                                })}
                            </AnimatePresence>
                        </div>
                    </CardContent>
                )}
            </Card>
        </div>
    )
}
