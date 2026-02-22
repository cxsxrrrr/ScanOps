import { useState, useEffect } from 'react'
import { useUser } from '@clerk/clerk-react'
import api from '../lib/api'
import { User, Building, Save, Loader2, CheckCircle2 } from 'lucide-react'

export default function Profile() {
    const { user } = useUser()
    const [profile, setProfile] = useState({ first_name: '', last_name: '', organization_name: '' })
    const [saving, setSaving] = useState(false)
    const [saved, setSaved] = useState(false)

    useEffect(() => { loadProfile() }, [])

    async function loadProfile() {
        try {
            const res = await api.get('/auth/profile/')
            setProfile({
                first_name: res.data.first_name || '',
                last_name: res.data.last_name || '',
                organization_name: res.data.organization?.name || '',
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

    return (
        <div className="max-w-2xl mx-auto space-y-6 animate-fade-in">
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
        </div>
    )
}
