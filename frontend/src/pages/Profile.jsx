import { useState, useEffect } from 'react'
import { useUser } from '@clerk/clerk-react'
import api from '../lib/api'
import { User, Building, Save, Loader2, CheckCircle2, LogOut, AlertTriangle } from 'lucide-react'

export default function Profile() {
    const { user } = useUser()
    const [profile, setProfile] = useState({ first_name: '', last_name: '', organization_name: '', member_count: 1 })
    const [saving, setSaving] = useState(false)
    const [saved, setSaved] = useState(false)
    const [leaving, setLeaving] = useState(false)
    const [leaveError, setLeaveError] = useState(null)
    const [showModal, setShowModal] = useState(false)

    useEffect(() => { loadProfile() }, [])

    async function loadProfile() {
        try {
            const res = await api.get('/auth/profile/')
            setProfile({
                first_name: res.data.first_name || '',
                last_name: res.data.last_name || '',
                organization_name: res.data.organization?.name || '',
                member_count: res.data.organization?.member_count || 1,
            })
        } catch (err) {
            console.error('Failed to load profile:', err)
        }
    }

    async function handleSave(e) {
        e.preventDefault()
        setSaving(true)
        setSaved(false)
        try {
            await api.patch('/auth/profile/', profile)
            if (profile.organization_name) {
                await api.patch('/auth/organization/', { name: profile.organization_name })
            }
            setSaved(true)
            setTimeout(() => setSaved(false), 3000)
        } catch (err) {
            console.error('Failed to save profile:', err)
        } finally {
            setSaving(false)
        }
    }

    async function leaveOrganization() {
        setLeaving(true)
        setLeaveError(null)
        try {
            await api.post('/auth/team/leave/')
            window.location.reload() // Reload app to clear old context
        } catch (err) {
            setLeaveError(err.response?.data?.detail || 'Error al intentar salir.')
            setLeaving(false)
        }
    }

    return (
        <div className="max-w-2xl mx-auto space-y-6">
            <div>
                <h1 className="text-2xl font-bold flex items-center gap-2">
                    <User className="w-6 h-6 text-blue-400" />
                    Perfil
                </h1>
                <p className="text-muted-foreground text-sm mt-1">
                    Gestiona tu información personal y organización.
                </p>
            </div>

            <form onSubmit={handleSave} className="glass rounded-xl p-6 space-y-5">
                {/* Email (read-only) */}
                <div>
                    <label className="block text-sm font-medium mb-1.5">Email</label>
                    <input
                        type="email"
                        value={user?.primaryEmailAddress?.emailAddress || ''}
                        disabled
                        className="w-full px-4 py-2.5 rounded-lg bg-white/5 border border-white/10 text-muted-foreground text-sm cursor-not-allowed"
                    />
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                        <label className="block text-sm font-medium mb-1.5">Nombre</label>
                        <input
                            type="text"
                            value={profile.first_name}
                            onChange={(e) => setProfile({ ...profile, first_name: e.target.value })}
                            className="w-full px-4 py-2.5 rounded-lg bg-white/5 border border-white/10 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none transition-colors text-sm"
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium mb-1.5">Apellido</label>
                        <input
                            type="text"
                            value={profile.last_name}
                            onChange={(e) => setProfile({ ...profile, last_name: e.target.value })}
                            className="w-full px-4 py-2.5 rounded-lg bg-white/5 border border-white/10 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none transition-colors text-sm"
                        />
                    </div>
                </div>

                <div>
                    <label className="block text-sm font-medium mb-1.5 flex items-center gap-1.5">
                        <Building className="w-4 h-4 text-purple-400" />
                        Organización
                    </label>
                    <input
                        type="text"
                        value={profile.organization_name}
                        onChange={(e) => setProfile({ ...profile, organization_name: e.target.value })}
                        placeholder="Nombre de tu empresa"
                        className="w-full px-4 py-2.5 rounded-lg bg-white/5 border border-white/10 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none transition-colors text-sm"
                    />
                    
                    <div className="mt-6 p-4 rounded-xl bg-red-500/5 border border-red-500/10 flex flex-col sm:flex-row items-center justify-between gap-4">
                        <div className="flex items-start gap-3 text-sm">
                            <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                            <div>
                                <p className="font-medium text-red-300">Salir de la organización</p>
                                <p className="text-muted-foreground text-xs mt-0.5">
                                    Perderás el acceso a los datos ({profile.member_count} miembros actuales).
                                </p>
                            </div>
                        </div>
                        <button
                            type="button"
                            onClick={() => setShowModal(true)}
                            className="w-full sm:w-auto px-4 py-2 rounded-lg bg-red-500/10 text-red-400 hover:bg-red-500/20 text-sm font-medium flex items-center justify-center gap-2 transition-colors whitespace-nowrap"
                        >
                            <LogOut className="w-4 h-4" />
                            Salir
                        </button>
                    </div>
                </div>

                <div className="flex items-center justify-between pt-2">
                    <div>
                        {saved && (
                            <span className="text-emerald-400 text-sm flex items-center gap-1">
                                <CheckCircle2 className="w-4 h-4" /> Guardado exitosamente
                            </span>
                        )}
                    </div>
                    <button
                        type="submit"
                        disabled={saving}
                        className="px-6 py-2.5 rounded-lg gradient-primary text-white font-medium text-sm hover:opacity-90 transition-opacity flex items-center gap-2"
                    >
                        {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                        Guardar
                    </button>
                </div>
            </form>

            {/* Leave Organization Modal */}
            {showModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
                    <div className="bg-slate-900 border border-white/10 rounded-2xl p-6 max-w-md w-full shadow-2xl shadow-red-500/10">
                        <div className="flex items-center gap-4 mb-4">
                            <div className="w-12 h-12 rounded-full bg-red-500/10 flex items-center justify-center flex-shrink-0">
                                <AlertTriangle className="w-6 h-6 text-red-400" />
                            </div>
                            <div>
                                <h3 className="text-xl font-bold text-white">¿Salir de la organización?</h3>
                                <p className="text-sm text-muted-foreground mt-1">
                                    Esta acción es irreversible. Perderás el acceso a todos los datos y escaneos asociados.
                                </p>
                            </div>
                        </div>
                        
                        <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3 mb-6">
                            <p className="text-xs text-red-200 text-center">
                                Quedarás sin organización temporalmente y podrás aceptar nuevas invitaciones de forma libre o crear la tuya propia cuando desees.
                            </p>
                        </div>

                        {leaveError && (
                            <p className="text-red-400 text-sm text-center mb-4 bg-red-500/10 p-2 rounded-lg">
                                {leaveError}
                            </p>
                        )}

                        <div className="flex gap-3">
                            <button
                                type="button"
                                onClick={() => !leaving && setShowModal(false)}
                                disabled={leaving}
                                className="flex-1 py-2.5 rounded-xl border border-white/10 text-white font-medium hover:bg-white/5 transition-colors disabled:opacity-50"
                            >
                                Cancelar
                            </button>
                            <button
                                type="button"
                                onClick={leaveOrganization}
                                disabled={leaving}
                                className="flex-1 py-2.5 rounded-xl bg-red-500 hover:bg-red-600 text-white font-semibold transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
                            >
                                {leaving ? <Loader2 className="w-5 h-5 animate-spin" /> : <LogOut className="w-5 h-5" />}
                                {leaving ? 'Saliendo...' : 'Confirmar Salida'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}
