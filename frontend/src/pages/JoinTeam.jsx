import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuth, useUser } from '@clerk/clerk-react'
import api from '../lib/api'
import { Users, Building2, Loader2, CheckCircle2, XCircle, AlertTriangle } from 'lucide-react'

export default function JoinTeam() {
    const { token } = useParams()
    const navigate = useNavigate()
    const { isSignedIn, getToken } = useAuth()
    const { user: clerkUser } = useUser()

    const [info, setInfo] = useState(null)
    const [loading, setLoading] = useState(true)
    const [joining, setJoining] = useState(false)
    const [error, setError] = useState(null)
    const [success, setSuccess] = useState(false)

    useEffect(() => {
        loadInviteInfo()
    }, [token])

    async function loadInviteInfo() {
        try {
            const res = await api.get(`/auth/invitations/${token}/info/`)
            setInfo(res.data)
        } catch (err) {
            const status = err.response?.status
            if (status === 404) setError('Esta invitación no existe.')
            else if (status === 410) setError('Esta invitación ya no es válida.')
            else if (status === 403) setError('Esta organización ha alcanzado el límite de miembros.')
            else setError('No se pudo cargar la invitación.')
        } finally {
            setLoading(false)
        }
    }

    async function handleJoin() {
        if (!isSignedIn) {
            // Save invite token and redirect to register
            sessionStorage.setItem('pendingInvite', token)
            navigate('/register')
            return
        }

        setJoining(true)
        setError(null)
        try {
            const res = await api.post(`/auth/invitations/${token}/accept/`)
            setSuccess(true)
            setTimeout(() => navigate('/'), 2000)
        } catch (err) {
            const detail = err.response?.data?.detail
            setError(detail || 'Error al unirse a la organización.')
        } finally {
            setJoining(false)
        }
    }

    if (loading) {
        return (
            <div className="min-h-screen gradient-bg flex items-center justify-center p-6">
                <div className="glass-strong rounded-2xl p-10 text-center">
                    <Loader2 className="w-8 h-8 animate-spin text-blue-400 mx-auto" />
                    <p className="text-muted-foreground mt-3">Cargando invitación...</p>
                </div>
            </div>
        )
    }

    if (error && !info) {
        return (
            <div className="min-h-screen gradient-bg flex items-center justify-center p-6">
                <div className="max-w-md w-full glass-strong rounded-2xl p-8 text-center space-y-4">
                    <div className="w-16 h-16 rounded-full bg-red-500/10 flex items-center justify-center mx-auto">
                        <XCircle className="w-8 h-8 text-red-400" />
                    </div>
                    <h1 className="text-xl font-bold">Invitación Inválida</h1>
                    <p className="text-muted-foreground text-sm">{error}</p>
                    <button
                        onClick={() => navigate(isSignedIn ? '/' : '/login')}
                        className="px-6 py-2.5 rounded-xl gradient-primary text-white font-medium text-sm hover:opacity-90"
                    >
                        {isSignedIn ? 'Ir al Dashboard' : 'Iniciar Sesión'}
                    </button>
                </div>
            </div>
        )
    }

    if (success) {
        return (
            <div className="min-h-screen gradient-bg flex items-center justify-center p-6">
                <div className="max-w-md w-full glass-strong rounded-2xl p-8 text-center space-y-4">
                    <div className="w-16 h-16 rounded-full bg-emerald-500/10 flex items-center justify-center mx-auto">
                        <CheckCircle2 className="w-8 h-8 text-emerald-400" />
                    </div>
                    <h1 className="text-xl font-bold">¡Bienvenido al equipo!</h1>
                    <p className="text-muted-foreground text-sm">
                        Te has unido a <strong>{info?.organization_name}</strong> exitosamente.
                    </p>
                    <p className="text-xs text-muted-foreground">Redirigiendo al dashboard...</p>
                </div>
            </div>
        )
    }

    return (
        <div className="min-h-screen gradient-bg flex items-center justify-center p-6">
            <div className="max-w-md w-full glass-strong rounded-2xl p-8 space-y-6">
                {/* Header */}
                <div className="text-center space-y-3">
                    <div className="w-16 h-16 rounded-2xl gradient-primary flex items-center justify-center mx-auto shadow-lg shadow-blue-500/20">
                        <Building2 className="w-8 h-8 text-white" />
                    </div>
                    <h1 className="text-2xl font-bold">Únete al equipo</h1>
                    <p className="text-muted-foreground text-sm">
                        Has sido invitado a unirte a la organización
                    </p>
                </div>

                {/* Org info card */}
                <div className="rounded-xl bg-white/5 border border-white/10 p-5 space-y-3">
                    <h2 className="text-lg font-semibold text-center">{info?.organization_name}</h2>
                    <div className="flex justify-center gap-6 text-sm">
                        <div className="text-center">
                            <p className="text-muted-foreground text-xs">Plan</p>
                            <p className="font-medium text-blue-400">{info?.organization_plan}</p>
                        </div>
                        <div className="text-center">
                            <p className="text-muted-foreground text-xs">Miembros</p>
                            <p className="font-medium">
                                <span className="text-white">{info?.member_count}</span>
                                <span className="text-muted-foreground"> / {info?.member_limit}</span>
                            </p>
                        </div>
                    </div>
                </div>

                {/* Error */}
                {error && (
                    <div className="flex items-center gap-2 p-3 rounded-lg bg-red-500/10 border border-red-500/20">
                        <AlertTriangle className="w-4 h-4 text-red-400 flex-shrink-0" />
                        <p className="text-sm text-red-300">{error}</p>
                    </div>
                )}

                {/* Action */}
                {isSignedIn ? (
                    <button
                        onClick={handleJoin}
                        disabled={joining}
                        className="w-full py-3 rounded-xl gradient-primary text-white font-semibold hover:opacity-90 transition-opacity flex items-center justify-center gap-2 shadow-lg shadow-blue-500/20"
                    >
                        {joining ? (
                            <Loader2 className="w-5 h-5 animate-spin" />
                        ) : (
                            <Users className="w-5 h-5" />
                        )}
                        {joining ? 'Uniéndose...' : 'Unirse a la organización'}
                    </button>
                ) : (
                    <div className="space-y-3">
                        <p className="text-sm text-center text-muted-foreground">
                            Debes iniciar sesión o registrarte para unirte.
                        </p>
                        <div className="flex gap-3">
                            <button
                                onClick={() => {
                                    sessionStorage.setItem('pendingInvite', token)
                                    navigate('/login')
                                }}
                                className="flex-1 py-3 rounded-xl bg-white/5 border border-white/10 text-white font-medium hover:bg-white/10 transition-colors"
                            >
                                Iniciar Sesión
                            </button>
                            <button
                                onClick={() => {
                                    sessionStorage.setItem('pendingInvite', token)
                                    navigate('/register')
                                }}
                                className="flex-1 py-3 rounded-xl gradient-primary text-white font-semibold hover:opacity-90 transition-opacity shadow-lg shadow-blue-500/20"
                            >
                                Registrarse
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}
