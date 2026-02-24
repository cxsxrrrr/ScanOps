import { useState, useEffect } from 'react'
import api from '../lib/api'
import { Settings as SettingsIcon, Bell, Mail, Save, Loader2, CheckCircle2 } from 'lucide-react'

export default function Settings() {
    const [config, setConfig] = useState({ frequency: 'weekly', enabled: true })
    const [logs, setLogs] = useState([])
    const [loading, setLoading] = useState(true)
    const [saving, setSaving] = useState(false)
    const [saved, setSaved] = useState(false)

    useEffect(() => { loadSettings() }, [])

    async function loadSettings() {
        try {
            const [configRes, logsRes] = await Promise.all([
                api.get('/notifications/config/').catch(() => ({ data: { frequency: 'weekly', enabled: true } })),
                api.get('/notifications/logs/').catch(() => ({ data: [] })),
            ])
            setConfig(configRes.data)
            setLogs(logsRes.data)
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
            await api.put('/notifications/config/', config)
            setSaved(true)
            setTimeout(() => setSaved(false), 3000)
        } catch (err) {
            console.error('Failed to save config:', err)
        } finally {
            setSaving(false)
        }
    }

    return (
        <div className="max-w-3xl mx-auto space-y-6">
            <div>
                <h1 className="text-2xl font-bold flex items-center gap-2">
                    <SettingsIcon className="w-6 h-6 text-blue-400" />
                    Configuración
                </h1>
                <p className="text-muted-foreground text-sm mt-1">
                    Configura las notificaciones por correo electrónico.
                </p>
            </div>

            {/* Notification config */}
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

                <div className="flex items-center justify-between pt-2">
                    {saved && (
                        <span className="text-emerald-400 text-sm flex items-center gap-1">
                            <CheckCircle2 className="w-4 h-4" /> Guardado
                        </span>
                    )}
                    <div className="flex-1" />
                    <button
                        type="submit"
                        disabled={saving}
                        className="px-6 py-2.5 rounded-lg gradient-primary text-white font-medium text-sm hover:opacity-90 flex items-center gap-2"
                    >
                        {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                        Guardar
                    </button>
                </div>
            </form>

            {/* Email logs */}
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
                                        {log.email_type === 'scheduled' ? '📨 Reporte Periódico' : '⚠️ Alerta de Seguridad'}
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
