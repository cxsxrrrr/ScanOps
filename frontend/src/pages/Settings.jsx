import { useState, useEffect } from 'react'
import { toast } from 'sonner'
import api from '../lib/api'
import { formatDate } from '../lib/utils'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Separator } from '@/components/ui/separator'
import { Skeleton } from '@/components/ui/skeleton'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import {
    Settings as SettingsIcon, Bell, Mail, Save, Loader2, CheckCircle2,
    Users, Link2, Copy, Trash2, UserPlus, Crown, Shield, Send, Calendar, Cpu
} from 'lucide-react'

export default function Settings() {
    const [config,        setConfig]        = useState({ frequency: 'weekly', enabled: true })
    const [logs,          setLogs]          = useState([])
    const [loading,       setLoading]       = useState(true)
    const [saving,        setSaving]        = useState(false)
    const [sendingReport, setSendingReport] = useState(false)
    const [members,       setMembers]       = useState([])
    const [invitations,   setInvitations]   = useState([])
    const [org,           setOrg]           = useState(null)
    const [myRole,        setMyRole]        = useState('user')
    const [creatingInvite,setCreatingInvite]= useState(false)
    const [copied,        setCopied]        = useState(null)
    const [teamError,     setTeamError]     = useState(null)

    const [llmConfig,     setLlmConfig]     = useState({ provider: 'default', api_key: '', model_name: '' })
    const [savingLlm,     setSavingLlm]     = useState(false)

    useEffect(() => {
        const controller = new AbortController()
        loadAll(controller.signal)
        return () => controller.abort()
    }, [])

    async function loadAll(signal) {
        const cfg = { signal }
        try {
            const [configRes, logsRes, membersRes, invitesRes, orgRes, llmRes, profileRes] = await Promise.all([
                api.get('/notifications/config/', cfg).catch(() => ({ data: { frequency: 'weekly', enabled: true } })),
                api.get('/notifications/logs/', cfg).catch(() => ({ data: [] })),
                api.get('/auth/team/', cfg).catch(() => ({ data: [] })),
                api.get('/auth/invitations/', cfg).catch(() => ({ data: [] })),
                api.get('/auth/organization/', cfg).catch(() => ({ data: null })),
                api.get('/auth/organization/llm-config/', cfg).catch(() => ({ data: { provider: 'default', api_key: '', model_name: '' } })),
                api.get('/auth/profile/', cfg).catch(() => ({ data: null })),
            ])
            setConfig(configRes.data)
            setLogs(logsRes.data)
            setMembers(membersRes.data)
            setInvitations(invitesRes.data)
            setOrg(orgRes.data)
            setLlmConfig({ ...llmRes.data, api_key: '' }) // Clear key for security, handle has_api_key visually if needed
            setMyRole(profileRes.data?.role || 'user')
        } catch (err) {
            if (err.code === 'ERR_CANCELED') return
            console.error('Failed to load settings:', err)
        } finally {
            setLoading(false)
        }
    }

    async function handleSave(e) {
        e.preventDefault()
        setSaving(true)
        try {
            const res = await api.put('/notifications/config/', config)
            setConfig(res.data)
            toast.success('Configuración guardada.')
            const logsRes = await api.get('/notifications/logs/').catch(() => ({ data: [] }))
            setLogs(logsRes.data)
        } catch {
            toast.error('Error al guardar la configuración.')
        } finally {
            setSaving(false)
        }
    }

    async function handleSaveLlm(e) {
        e.preventDefault()
        setSavingLlm(true)
        try {
            const dataToSave = { ...llmConfig }
            if (!dataToSave.api_key) {
                delete dataToSave.api_key
            }
            const res = await api.put('/auth/organization/llm-config/', dataToSave)
            setLlmConfig({ ...res.data, api_key: '' })
            toast.success('Configuración de IA guardada.')
        } catch (err) {
            toast.error(err.response?.data?.detail || 'Error al guardar configuración IA.')
        } finally {
            setSavingLlm(false)
        }
    }

    async function handleSendReport() {
        setSendingReport(true)
        try {
            await api.post('/notifications/send-report/')
            toast.success('¡Reporte enviado! Revisa tu correo.')
            const logsRes = await api.get('/notifications/logs/').catch(() => ({ data: [] }))
            setLogs(logsRes.data)
        } catch (err) {
            toast.error(err.response?.data?.detail || 'Error al enviar el reporte.')
        } finally {
            setSendingReport(false)
        }
    }

    async function createInvitation() {
        setCreatingInvite(true)
        setTeamError(null)
        try {
            const res = await api.post('/auth/invitations/', {})
            setInvitations([res.data, ...invitations])
            copyToClipboard(res.data.token)
        } catch (err) {
            setTeamError(err.response?.data?.detail || 'Error al crear la invitación.')
        } finally {
            setCreatingInvite(false)
        }
    }

    async function revokeInvitation(id) {
        try {
            await api.delete(`/auth/invitations/${id}/revoke/`)
            setInvitations(invitations.filter(inv => inv.id !== id))
            toast.success('Invitación revocada.')
        } catch {
            toast.error('Error al revocar la invitación.')
        }
    }

    function copyToClipboard(token) {
        const url = `${window.location.origin}/invite/${token}`
        navigator.clipboard.writeText(url)
        setCopied(token)
        toast.success('Enlace copiado al portapapeles.')
        setTimeout(() => setCopied(null), 2000)
    }

    function formatNextSend(dateStr) {
        if (!dateStr) return null
        const date   = new Date(dateStr)
        const now    = new Date()
        const diffMs = date - now
        const diffDays = Math.ceil(diffMs / (1000 * 60 * 60 * 24))
        const formatted = date.toLocaleDateString('es-VE', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' })
        if (diffDays <= 0) return `Hoy · ${formatted}`
        if (diffDays === 1) return `Mañana · ${formatted}`
        return `En ${diffDays} días · ${formatted}`
    }

    function getEmailTypeLabel(type) {
        const labels = { scheduled: '📨 Reporte Periódico', alert: '⚠️ Alerta', manual: '📤 Manual', scan_complete: '🔍 Escaneo' }
        return labels[type] || '📧 Correo'
    }

    const visibleMemberCount = members.length
    const canManageTeam = myRole === 'org_admin' || myRole === 'admin'
    const canInvite = canManageTeam && org && visibleMemberCount < org.member_limit
    const isFree    = org?.plan === 'free'

    const roleBadge = {
        admin:     { label: 'Admin',        className: 'text-amber-500 border-amber-500/30', Icon: Crown },
        org_admin: { label: 'Admin equipo', className: 'text-purple-500 border-purple-500/30', Icon: Shield },
        user:      { label: 'Usuario',      className: 'text-blue-500 border-blue-500/30', Icon: Shield },
    }

    if (loading) return (
        <div className="max-w-3xl mx-auto space-y-5">
            {[1,2,3].map(i => <Card key={i}><CardContent className="p-6 space-y-3"><Skeleton className="h-6 w-40" /><Skeleton className="h-24 w-full rounded-xl" /></CardContent></Card>)}
        </div>
    )

    return (
        <div className="max-w-3xl mx-auto space-y-5">
            <div>
                <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
                    <SettingsIcon className="w-6 h-6 text-blue-500" /> Configuración
                </h1>
                <p className="text-muted-foreground text-sm mt-1">Gestiona tu equipo y notificaciones.</p>
            </div>

            {/* ── Team ── */}
            <Card>
                <CardHeader className="pb-4">
                    <div className="flex items-center justify-between">
                        <CardTitle className="text-base flex items-center gap-2">
                            <Users className="w-4 h-4 text-blue-500" /> Equipo
                        </CardTitle>
                        {org && (
                            <Badge variant="outline" className="text-xs">
                                {visibleMemberCount} / {org.member_limit} miembros
                            </Badge>
                        )}
                    </div>
                </CardHeader>
                <CardContent className="space-y-4">
                    {members.length > 0 ? (
                        <div className="divide-y divide-border">
                            {members.map((m) => (
                                <div key={m.id} className="py-3 flex items-center justify-between">
                                    <div className="flex items-center gap-3">
                                        <div className="w-9 h-9 rounded-full gradient-primary flex items-center justify-center text-sm font-bold text-white flex-shrink-0">
                                            {(m.first_name?.[0] || m.email[0] || '?').toUpperCase()}
                                        </div>
                                        <div>
                                            <p className="text-sm font-medium">
                                                {m.first_name && m.last_name ? `${m.first_name} ${m.last_name}` : m.email}
                                            </p>
                                            <p className="text-xs text-muted-foreground">{m.email}</p>
                                        </div>
                                    </div>
                                    <Badge variant="outline" className={`text-xs ${(roleBadge[m.role] || roleBadge.user).className}`}>
                                        {(() => { const Icon = (roleBadge[m.role] || roleBadge.user).Icon; return <Icon className="w-3 h-3 mr-1" /> })()}
                                        {(roleBadge[m.role] || roleBadge.user).label}
                                    </Badge>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <p className="text-sm text-muted-foreground text-center py-3">Sin miembros en la organización.</p>
                    )}

                    <Separator />

                    {isFree ? (
                        <div className="flex items-center gap-3 p-4 rounded-xl bg-amber-500/5 border border-amber-500/15">
                            <Crown className="w-5 h-5 text-amber-400 flex-shrink-0" />
                            <div>
                                <p className="text-sm font-medium text-amber-500">Plan Free</p>
                                <p className="text-xs text-muted-foreground">Actualiza a Pro o Ultimate para invitar miembros.</p>
                            </div>
                        </div>
                    ) : !canManageTeam ? (
                        <div className="flex items-center gap-3 p-4 rounded-xl bg-muted/50 border border-border">
                            <Link2 className="w-5 h-5 text-muted-foreground flex-shrink-0" />
                            <p className="text-sm text-muted-foreground">
                                Solo un administrador de la organización puede gestionar invitaciones.
                            </p>
                        </div>
                    ) : (
                        <div className="space-y-3">
                            <div className="flex items-center justify-between">
                                <p className="text-sm font-medium flex items-center gap-2">
                                    <Link2 className="w-4 h-4 text-purple-500" /> Enlaces de invitación
                                </p>
                                <Button size="sm" onClick={createInvitation} disabled={creatingInvite || !canInvite}>
                                    {creatingInvite ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <UserPlus className="w-3.5 h-3.5" />}
                                    Generar enlace
                                </Button>
                            </div>

                            {teamError && <p className="text-sm text-red-500 bg-red-500/5 border border-red-500/15 p-3 rounded-lg">{teamError}</p>}
                            {!canInvite && !isFree && <p className="text-sm text-amber-500 bg-amber-500/5 border border-amber-500/15 p-3 rounded-lg">Has alcanzado el límite de miembros.</p>}

                            {invitations.length > 0 && (
                                <div className="space-y-2">
                                    {invitations.map((inv) => (
                                        <div key={inv.id} className={`flex items-center justify-between p-3 rounded-xl bg-muted/50 border border-border ${!inv.is_valid ? 'opacity-50' : ''}`}>
                                            <div className="flex-1 min-w-0">
                                                <p className="text-xs font-mono text-muted-foreground truncate">
                                                    {window.location.origin}/invite/{inv.token}
                                                </p>
                                                <p className="text-xs text-muted-foreground mt-0.5">
                                                    {inv.uses} uso(s){inv.max_uses > 0 && ` / ${inv.max_uses} máx`} ·{' '}
                                                    <span className={inv.is_valid ? 'text-emerald-500' : 'text-red-500'}>
                                                        {inv.is_valid ? 'Activo' : 'Expirado'}
                                                    </span>
                                                    {inv.expires_at && (
                                                        <> · {inv.is_valid ? 'Expira' : 'Expiró'} {formatDate(inv.expires_at)}</>
                                                    )}
                                                </p>
                                            </div>
                                            <div className="flex items-center gap-1.5 ml-3">
                                                {inv.is_valid && (
                                                    <>
                                                        <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => copyToClipboard(inv.token)} title="Copiar">
                                                            {copied === inv.token
                                                                ? <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                                                                : <Copy className="w-4 h-4 text-muted-foreground" />}
                                                        </Button>
                                                        <Button variant="ghost" size="icon" className="h-8 w-8 hover:text-red-500 hover:bg-red-500/10" onClick={() => revokeInvitation(inv.id)} title="Revocar">
                                                            <Trash2 className="w-4 h-4" />
                                                        </Button>
                                                    </>
                                                )}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* ── Notifications ── */}
            <Card>
                <CardHeader className="pb-4">
                    <CardTitle className="text-base flex items-center gap-2">
                        <Bell className="w-4 h-4 text-purple-500" /> Notificaciones por Email
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <form onSubmit={handleSave} className="space-y-5">
                        <div className="flex items-center justify-between p-4 rounded-xl bg-muted/50">
                            <div>
                                <Label htmlFor="reports-toggle" className="font-medium">Reportes periódicos</Label>
                                <p className="text-xs text-muted-foreground mt-0.5">Recibir resúmenes de seguridad por correo</p>
                            </div>
                            <Switch
                                id="reports-toggle"
                                checked={config.enabled}
                                onCheckedChange={(checked) => setConfig({ ...config, enabled: checked })}
                            />
                        </div>

                        <div className="space-y-2">
                            <Label>Frecuencia de envío</Label>
                            <Select
                                value={config.frequency}
                                onValueChange={(val) => setConfig({ ...config, frequency: val })}
                            >
                                <SelectTrigger>
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="daily">Diario</SelectItem>
                                    <SelectItem value="weekly">Semanal</SelectItem>
                                    <SelectItem value="monthly">Mensual</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>

                        {config.enabled && config.next_send_at && (
                            <div className="flex items-center gap-3 p-4 rounded-xl bg-blue-500/5 border border-blue-500/15">
                                <Calendar className="w-5 h-5 text-blue-500 flex-shrink-0" />
                                <div>
                                    <p className="text-sm font-medium text-blue-500">Próximo envío programado</p>
                                    <p className="text-xs text-muted-foreground mt-0.5">{formatNextSend(config.next_send_at)}</p>
                                </div>
                            </div>
                        )}

                        <div className="flex justify-end">
                            <Button type="submit" disabled={saving}>
                                {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                                Guardar
                            </Button>
                        </div>
                    </form>
                </CardContent>
            </Card>

            {/* ── AI Config ── */}
            <Card>
                <CardHeader className="pb-4">
                    <CardTitle className="text-base flex items-center gap-2">
                        <Cpu className="w-4 h-4 text-purple-500" /> Inteligencia Artificial
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <form onSubmit={handleSaveLlm} className="space-y-4">
                        <p className="text-sm text-muted-foreground mb-4">
                            Configura el proveedor de inteligencia artificial que generará los reportes automáticos.
                        </p>
                        <div className="space-y-2">
                            <Label>Proveedor</Label>
                            <Select
                                value={llmConfig.provider || 'default'}
                                onValueChange={(val) => setLlmConfig({ ...llmConfig, provider: val })}
                            >
                                <SelectTrigger>
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="default">Por defecto (Google Gemini)</SelectItem>
                                    <SelectItem value="opencode_go">OpenCode Go</SelectItem>
                                    <SelectItem value="openai">OpenAI</SelectItem>
                                    <SelectItem value="anthropic">Anthropic</SelectItem>
                                    <SelectItem value="gemini">Google Gemini (Clave Propia)</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                        {llmConfig.provider !== 'default' && (
                            <>
                                <div className="space-y-2">
                                    <Label>Nombre del Modelo</Label>
                                    {llmConfig.provider === 'opencode_go' ? (
                                        <Select
                                            value={llmConfig.model_name}
                                            onValueChange={(val) => setLlmConfig({ ...llmConfig, model_name: val })}
                                        >
                                            <SelectTrigger><SelectValue placeholder="Selecciona un modelo" /></SelectTrigger>
                                            <SelectContent>
                                                <SelectItem value="opencode-go/glm-5.1">GLM-5.1</SelectItem>
                                                <SelectItem value="opencode-go/glm-5">GLM-5</SelectItem>
                                                <SelectItem value="opencode-go/kimi-k2.6">Kimi K2.6</SelectItem>
                                                <SelectItem value="opencode-go/kimi-k2.5">Kimi K2.5</SelectItem>
                                                <SelectItem value="opencode-go/deepseek-v4-pro">DeepSeek V4 Pro</SelectItem>
                                                <SelectItem value="opencode-go/deepseek-v4-flash">DeepSeek V4 Flash</SelectItem>
                                                <SelectItem value="opencode-go/mimo-v2.5">MiMo V2.5</SelectItem>
                                                <SelectItem value="opencode-go/mimo-v2.5-pro">MiMo V2.5 Pro</SelectItem>
                                                <SelectItem value="opencode-go/minimax-m3">MiniMax M3</SelectItem>
                                                <SelectItem value="opencode-go/minimax-m2.7">MiniMax M2.7</SelectItem>
                                                <SelectItem value="opencode-go/minimax-m2.5">MiniMax M2.5</SelectItem>
                                                <SelectItem value="opencode-go/qwen3.7-max">Qwen3.7 Max</SelectItem>
                                                <SelectItem value="opencode-go/qwen3.6-plus">Qwen3.6 Plus</SelectItem>
                                            </SelectContent>
                                        </Select>
                                    ) : (
                                        <Input 
                                            placeholder="Ej. gpt-4o, claude-3-5-sonnet-20240620" 
                                            value={llmConfig.model_name || ''} 
                                            onChange={e => setLlmConfig({...llmConfig, model_name: e.target.value})}
                                        />
                                    )}
                                </div>
                                <div className="space-y-2">
                                    <Label>API Key</Label>
                                    <Input 
                                        type="password" 
                                        placeholder={llmConfig.has_api_key ? '•••••••••••••••• (Guardada)' : 'Ingresa tu API Key'} 
                                        value={llmConfig.api_key || ''}
                                        onChange={e => setLlmConfig({...llmConfig, api_key: e.target.value})}
                                    />
                                    <p className="text-[10px] text-muted-foreground">La API Key se guarda cifrada y solo se usa para generar los reportes de tu organización.</p>
                                </div>
                            </>
                        )}
                        <div className="flex justify-end pt-2">
                            <Button type="submit" disabled={savingLlm}>
                                {savingLlm ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                                Guardar IA
                            </Button>
                        </div>
                    </form>
                </CardContent>
            </Card>

            {/* ── Send manual report ── */}
            <Card>
                <CardHeader className="pb-4">
                    <CardTitle className="text-base flex items-center gap-2">
                        <Send className="w-4 h-4 text-blue-500" /> Enviar Reporte Manual
                    </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    <p className="text-sm text-muted-foreground">
                        Envía un reporte de seguridad detallado al correo de todos los miembros de tu organización ahora mismo.
                    </p>
                    <Button onClick={handleSendReport} disabled={sendingReport} className="w-full">
                        {sendingReport ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                        {sendingReport ? 'Enviando reporte...' : 'Enviar Reporte Ahora'}
                    </Button>
                </CardContent>
            </Card>

            {/* ── Email logs ── */}
            <Card>
                <CardHeader className="pb-4">
                    <CardTitle className="text-base flex items-center gap-2">
                        <Mail className="w-4 h-4 text-emerald-500" /> Historial de Correos
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    {logs.length === 0 ? (
                        <p className="text-sm text-muted-foreground text-center py-6">Sin correos enviados aún.</p>
                    ) : (
                        <div className="divide-y divide-border max-h-72 overflow-y-auto custom-scrollbar">
                            {logs.map((log) => (
                                <div key={log.id} className="py-3 flex items-center justify-between">
                                    <div>
                                        <p className="text-sm font-medium">{getEmailTypeLabel(log.email_type)}</p>
                                        <p className="text-xs text-muted-foreground">{new Date(log.sent_at).toLocaleString('es-VE')}</p>
                                    </div>
                                    <Badge variant="outline" className={`text-xs ${log.status === 'sent' ? 'text-emerald-500 border-emerald-500/30' : 'text-red-500 border-red-500/30'}`}>
                                        {log.status === 'sent' ? 'Enviado' : 'Error'}
                                    </Badge>
                                </div>
                            ))}
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    )
}
