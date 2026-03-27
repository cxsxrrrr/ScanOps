import { useState, useEffect } from 'react'
import api from '../lib/api'
import {
    Settings as SettingsIcon, Bell, Mail, Save, Loader2, CheckCircle2,
    Users, Link2, Copy, Trash2, UserPlus, Crown, Shield, Send, Calendar, Clock
} from 'lucide-react'

export default function Settings() {
    const [config, setConfig] = useState({ frequency: 'weekly', enabled: true })
    const [logs, setLogs] = useState([])
    const [loading, setLoading] = useState(true)
    const [saving, setSaving] = useState(false)
    const [saved, setSaved] = useState(false)
    const [sendingReport, setSendingReport] = useState(false)
    const [reportSent, setReportSent] = useState(false)
    const [reportError, setReportError] = useState(null)

    // Team state
    const [members, setMembers] = useState([])
    const [invitations, setInvitations] = useState([])
    const [org, setOrg] = useState(null)
    const [creatingInvite, setCreatingInvite] = useState(false)
    const [copied, setCopied] = useState(null)
    const [teamError, setTeamError] = useState(null)

    useEffect(() => { loadAll() }, [])

    async function loadAll() {
        try {
            const [configRes, logsRes, membersRes, invitesRes, orgRes] = await Promise.all([
                api.get('/notifications/config/').catch(() => ({ data: { frequency: 'weekly', enabled: true } })),
                api.get('/notifications/logs/').catch(() => ({ data: [] })),
                api.get('/auth/team/').catch(() => ({ data: [] })),
                api.get('/auth/invitations/').catch(() => ({ data: [] })),
                api.get('/auth/organization/').catch(() => ({ data: null })),
            ])
            setConfig(configRes.data)
            setLogs(logsRes.data)
            setMembers(membersRes.data)
            setInvitations(invitesRes.data)
            setOrg(orgRes.data)
        } catch (err) {
            console.error('Failed to load settings:', err)
        } finally {
            setLoading(false)
        }
    }

    async function handleSave(e) {
        e.preventDefault()
        setSaving(true)
        setSaved(false)
        try {
            const res = await api.put('/notifications/config/', config)
            setConfig(res.data)
            setSaved(true)
            setTimeout(() => setSaved(false), 3000)
            // Reload logs to show if an initial report was sent
            const logsRes = await api.get('/notifications/logs/').catch(() => ({ data: [] }))
            setLogs(logsRes.data)
        } catch (err) {
            console.error('Failed to save config:', err)
        } finally {
            setSaving(false)
        }
    }

    async function handleSendReport() {
        setSendingReport(true)
        setReportSent(false)
        setReportError(null)
        try {
            await api.post('/notifications/send-report/')
            setReportSent(true)
            setTimeout(() => setReportSent(false), 5000)
            // Reload logs
            const logsRes = await api.get('/notifications/logs/').catch(() => ({ data: [] }))
            setLogs(logsRes.data)
        } catch (err) {
            setReportError(err.response?.data?.detail || 'Error al enviar el reporte.')
            setTimeout(() => setReportError(null), 5000)
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
        } catch (err) {
            console.error('Failed to revoke invitation:', err)
        }
    }

    function copyToClipboard(token) {
        const url = `${window.location.origin}/invite/${token}`
        navigator.clipboard.writeText(url)
        setCopied(token)
        setTimeout(() => setCopied(null), 2000)
    }

    function formatNextSend(dateStr) {
        if (!dateStr) return null
        const date = new Date(dateStr)
        const now = new Date()
        const diffMs = date - now
        const diffDays = Math.ceil(diffMs / (1000 * 60 * 60 * 24))

        const formatted = date.toLocaleDateString('es-VE', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
        })

        if (diffDays <= 0) return `Hoy · ${formatted}`
        if (diffDays === 1) return `Mañana · ${formatted}`
        return `En ${diffDays} días · ${formatted}`
    }

    function getEmailTypeLabel(type) {
        switch (type) {
            case 'scheduled': return '📨 Reporte Periódico'
            case 'alert': return '⚠️ Alerta de Seguridad'
            case 'manual': return '📤 Reporte Manual'
            case 'scan_complete': return '🔍 Escaneo Completado'
            default: return '📧 Correo'
        }
    }

    const canInvite = org && org.member_count < org.member_limit
    const isFree = org?.plan === 'free'

    return (
        <div className="max-w-3xl mx-auto space-y-6">
            <div>
                <h1 className="text-2xl font-bold flex items-center gap-2">
                    <SettingsIcon className="w-6 h-6 text-blue-400" />
                    Configuración
                </h1>
                <p className="text-muted-foreground text-sm mt-1">
                    Gestiona tu equipo y notificaciones.
                </p>
            </div>

            {/* ============ TEAM SECTION ============ */}
            <div className="glass rounded-xl p-6 space-y-5">
                <div className="flex items-center justify-between">
                    <h2 className="text-lg font-semibold flex items-center gap-2">
                        <Users className="w-5 h-5 text-blue-400" />
                        Equipo
                    </h2>
                    {org && (
                        <span className="text-xs text-muted-foreground bg-white/5 px-3 py-1 rounded-full">
                            {org.member_count} / {org.member_limit} miembros
                        </span>
                    )}
                </div>

                {/* Members list */}
                {members.length > 0 ? (
                    <div className="divide-y divide-white/5">
                        {members.map((m) => (
                            <div key={m.id} className="py-3 flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                    <div className="w-9 h-9 rounded-full gradient-primary flex items-center justify-center text-sm font-bold text-white flex-shrink-0">
                                        {(m.first_name?.[0] || m.email[0] || '?').toUpperCase()}
                                    </div>
                                    <div>
                                        <p className="text-sm font-medium">
                                            {m.first_name && m.last_name
                                                ? `${m.first_name} ${m.last_name}`
                                                : m.email}
                                        </p>
                                        <p className="text-xs text-muted-foreground">{m.email}</p>
                                    </div>
                                </div>
                                <span className={`text-xs font-medium px-2 py-1 rounded flex items-center gap-1 ${
                                    m.role === 'admin'
                                        ? 'bg-amber-500/10 text-amber-400'
                                        : 'bg-blue-500/10 text-blue-400'
                                }`}>
                                    {m.role === 'admin' ? <Crown className="w-3 h-3" /> : <Shield className="w-3 h-3" />}
                                    {m.role === 'admin' ? 'Admin' : 'Usuario'}
                                </span>
                            </div>
                        ))}
                    </div>
                ) : (
                    <p className="text-muted-foreground text-sm text-center py-3">
                        No hay miembros en tu organización.
                    </p>
                )}

                {/* Invite link section */}
                <div className="pt-2 border-t border-white/5">
                    {isFree ? (
                        <div className="flex items-center gap-3 p-4 rounded-lg bg-amber-500/5 border border-amber-500/10">
                            <Crown className="w-5 h-5 text-amber-400 flex-shrink-0" />
                            <div>
                                <p className="text-sm font-medium text-amber-300">Plan Free</p>
                                <p className="text-xs text-muted-foreground">
                                    Actualiza a Pro o Ultimate para invitar miembros a tu equipo.
                                </p>
                            </div>
                        </div>
                    ) : (
                        <>
                            <div className="flex items-center justify-between mb-3">
                                <p className="text-sm font-medium flex items-center gap-2">
                                    <Link2 className="w-4 h-4 text-purple-400" />
                                    Enlaces de invitación
                                </p>
                                <button
                                    onClick={createInvitation}
                                    disabled={creatingInvite || !canInvite}
                                    className="px-4 py-2 rounded-lg gradient-primary text-white text-sm font-medium hover:opacity-90 flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-blue-500/20"
                                >
                                    {creatingInvite ? (
                                        <Loader2 className="w-4 h-4 animate-spin" />
                                    ) : (
                                        <UserPlus className="w-4 h-4" />
                                    )}
                                    Generar enlace
                                </button>
                            </div>

                            {teamError && (
                                <div className="mb-3 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-sm text-red-300">
                                    {teamError}
                                </div>
                            )}

                            {!canInvite && !isFree && (
                                <div className="mb-3 p-3 rounded-lg bg-amber-500/10 border border-amber-500/10 text-sm text-amber-300">
                                    Has alcanzado el límite de miembros de tu plan.
                                </div>
                            )}

                            {invitations.length > 0 && (
                                <div className="space-y-2">
                                    {invitations.map((inv) => (
                                        <div
                                            key={inv.id}
                                            className={`flex items-center justify-between p-3 rounded-lg bg-white/5 ${
                                                !inv.is_valid ? 'opacity-50' : ''
                                            }`}
                                        >
                                            <div className="flex-1 min-w-0">
                                                <p className="text-xs font-mono text-muted-foreground truncate">
                                                    {window.location.origin}/invite/{inv.token}
                                                </p>
                                                <p className="text-xs text-muted-foreground mt-0.5">
                                                    {inv.uses} uso(s)
                                                    {inv.max_uses > 0 && ` / ${inv.max_uses} máx`}
                                                    {' · '}
                                                    {inv.is_valid ? (
                                                        <span className="text-emerald-400">Activo</span>
                                                    ) : (
                                                        <span className="text-red-400">Inactivo</span>
                                                    )}
                                                </p>
                                            </div>
                                            <div className="flex items-center gap-1.5 ml-3">
                                                {inv.is_valid && (
                                                    <button
                                                        onClick={() => copyToClipboard(inv.token)}
                                                        className="p-2 rounded-lg hover:bg-white/10 transition-colors"
                                                        title="Copiar enlace"
                                                    >
                                                        {copied === inv.token ? (
                                                            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                                                        ) : (
                                                            <Copy className="w-4 h-4 text-muted-foreground" />
                                                        )}
                                                    </button>
                                                )}
                                                {inv.is_valid && (
                                                    <button
                                                        onClick={() => revokeInvitation(inv.id)}
                                                        className="p-2 rounded-lg hover:bg-red-500/10 transition-colors"
                                                        title="Revocar"
                                                    >
                                                        <Trash2 className="w-4 h-4 text-red-400" />
                                                    </button>
                                                )}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </>
                    )}
                </div>
            </div>

            {/* ============ NOTIFICATION CONFIG ============ */}
            <form onSubmit={handleSave} className="glass rounded-xl p-6 space-y-5">
                <h2 className="text-lg font-semibold flex items-center gap-2">
                    <Bell className="w-5 h-5 text-purple-400" />
                    Notificaciones por Email
                </h2>

                <div className="flex items-center justify-between p-4 rounded-lg bg-white/5">
                    <div>
                        <p className="font-medium">Reportes periódicos</p>
                        <p className="text-sm text-muted-foreground">Recibir resúmenes por correo</p>
                    </div>
                    <button
                        type="button"
                        role="switch"
                        aria-checked={config.enabled}
                        aria-label="Activar reportes periódicos"
                        onClick={() => setConfig({ ...config, enabled: !config.enabled })}
                        className={`w-12 h-6 rounded-full transition-colors duration-200 relative ${config.enabled ? 'bg-blue-500' : 'bg-white/20'}`}
                    >
                        <div
                            className={`w-5 h-5 rounded-full bg-white absolute top-0.5 transition-all duration-200 shadow-sm ${config.enabled ? 'left-[26px]' : 'left-0.5'
                                }`}
                        />
                    </button>
                </div>

                <div>
                    <label className="block text-sm font-medium mb-1.5">Frecuencia de envío</label>
                    <select
                        value={config.frequency}
                        onChange={(e) => setConfig({ ...config, frequency: e.target.value })}
                        className="w-full px-4 py-2.5 rounded-lg bg-white/5 border border-white/10 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none text-sm appearance-none cursor-pointer"
                        style={{ backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%239ca3af' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m6 9 6 6 6-6'/%3E%3C/svg%3E")`, backgroundRepeat: 'no-repeat', backgroundPosition: 'right 12px center' }}
                    >
                        <option value="daily">Diario</option>
                        <option value="weekly">Semanal</option>
                        <option value="monthly">Mensual</option>
                    </select>
                </div>

                {/* Next send date */}
                {config.enabled && config.next_send_at && (
                    <div className="flex items-center gap-3 p-4 rounded-lg bg-gradient-to-r from-blue-500/5 to-purple-500/5 border border-blue-500/10">
                        <Calendar className="w-5 h-5 text-blue-400 flex-shrink-0" />
                        <div>
                            <p className="text-sm font-medium text-blue-300">Próximo envío programado</p>
                            <p className="text-xs text-muted-foreground mt-0.5">
                                {formatNextSend(config.next_send_at)}
                            </p>
                        </div>
                    </div>
                )}

                <div className="flex items-center justify-between pt-2 flex-wrap gap-3">
                    <div className="flex items-center gap-3">
                        {saved && (
                            <span className="text-emerald-400 text-sm flex items-center gap-1 animate-fade-in">
                                <CheckCircle2 className="w-4 h-4" /> Configuración guardada
                            </span>
                        )}
                    </div>
                    <div className="flex items-center gap-2">
                        <button
                            type="submit"
                            disabled={saving}
                            className="px-6 py-2.5 rounded-lg gradient-primary text-white font-medium text-sm hover:opacity-90 flex items-center gap-2"
                        >
                            {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                            Guardar
                        </button>
                    </div>
                </div>
            </form>

            {/* ============ SEND MANUAL REPORT ============ */}
            <div className="glass rounded-xl p-6 space-y-4">
                <h2 className="text-lg font-semibold flex items-center gap-2">
                    <Send className="w-5 h-5 text-blue-400" />
                    Enviar Reporte Manual
                </h2>
                <p className="text-sm text-muted-foreground">
                    Envía un reporte de seguridad detallado al correo de todos los miembros de tu organización ahora mismo.
                </p>

                {reportSent && (
                    <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-sm text-emerald-300 flex items-center gap-2 animate-fade-in">
                        <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
                        ¡Reporte enviado exitosamente! Revisa tu correo.
                    </div>
                )}

                {reportError && (
                    <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-sm text-red-300 flex items-center gap-2 animate-fade-in">
                        {reportError}
                    </div>
                )}

                <button
                    onClick={handleSendReport}
                    disabled={sendingReport}
                    className="w-full px-6 py-3 rounded-lg bg-gradient-to-r from-blue-600 to-purple-600 text-white font-semibold text-sm hover:from-blue-500 hover:to-purple-500 transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-blue-500/20"
                >
                    {sendingReport ? (
                        <>
                            <Loader2 className="w-4 h-4 animate-spin" />
                            Enviando reporte...
                        </>
                    ) : (
                        <>
                            <Send className="w-4 h-4" />
                            Enviar Reporte Ahora
                        </>
                    )}
                </button>
            </div>

            {/* ============ EMAIL LOGS ============ */}
            <div className="glass rounded-xl p-6">
                <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                    <Mail className="w-5 h-5 text-emerald-400" />
                    Historial de Correos
                </h2>
                {logs.length === 0 ? (
                    <p className="text-muted-foreground text-sm text-center py-4">
                        No hay correos enviados aún.
                    </p>
                ) : (
                    <div className="divide-y divide-white/5">
                        {logs.map((log) => (
                            <div key={log.id} className="py-3 flex items-center justify-between">
                                <div>
                                    <p className="text-sm font-medium">
                                        {getEmailTypeLabel(log.email_type)}
                                    </p>
                                    <p className="text-xs text-muted-foreground">{new Date(log.sent_at).toLocaleString('es-VE')}</p>
                                </div>
                                <span className={`text-xs font-medium px-2 py-1 rounded ${log.status === 'sent' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'
                                    }`}>
                                    {log.status === 'sent' ? 'Enviado' : 'Error'}
                                </span>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    )
}
