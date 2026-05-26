import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuth, useUser } from '@clerk/clerk-react'
import { motion } from 'framer-motion'
import api from '../lib/api'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Users, Building2, Loader2, CheckCircle2, XCircle, AlertTriangle } from 'lucide-react'

export default function JoinTeam() {
    const { token }   = useParams()
    const navigate    = useNavigate()
    const { isSignedIn } = useAuth()
    const { user } = useUser()

    const [info,    setInfo]    = useState(null)
    const [loading, setLoading] = useState(true)
    const [joining, setJoining] = useState(false)
    const [error,   setError]   = useState(null)
    const [success, setSuccess] = useState(false)
    const [firstName, setFirstName] = useState('')
    const [lastName, setLastName]   = useState('')

    useEffect(() => {
        loadInviteInfo()
    }, [token])

    useEffect(() => {
        if (user) {
            setFirstName(user.firstName || '')
            setLastName(user.lastName || '')
        }
    }, [user])

    async function loadInviteInfo() {
        try {
            const res = await api.get(`/auth/invitations/${token}/info/`)
            setInfo(res.data)
        } catch (err) {
            const status = err.response?.status
            if (status === 404)      setError('Esta invitación no existe.')
            else if (status === 410) setError('Esta invitación ya no es válida.')
            else if (status === 403) setError('Esta organización ha alcanzado el límite de miembros.')
            else                     setError('No se pudo cargar la invitación.')
        } finally {
            setLoading(false)
        }
    }

    async function handleJoin() {
        if (!isSignedIn) {
            sessionStorage.setItem('pendingInvite', token)
            navigate('/register')
            return
        }
        setJoining(true)
        setError(null)
        try {
            await api.post(`/auth/invitations/${token}/accept/`, {
                first_name: firstName,
                last_name: lastName,
            })
            setSuccess(true)
            setTimeout(() => navigate('/'), 2000)
        } catch (err) {
            const detail = err.response?.data?.detail
            setError(detail || 'Error al unirse a la organización.')
        } finally {
            setJoining(false)
        }
    }

    const Wrapper = ({ children }) => (
        <div className="min-h-screen gradient-bg flex items-center justify-center p-6">
            <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
                className="max-w-md w-full"
            >
                {children}
            </motion.div>
        </div>
    )

    if (loading) return (
        <Wrapper>
            <Card>
                <CardContent className="py-12 text-center">
                    <Loader2 className="w-8 h-8 animate-spin text-blue-500 mx-auto" />
                    <p className="text-muted-foreground mt-3 text-sm">Cargando invitación...</p>
                </CardContent>
            </Card>
        </Wrapper>
    )

    if (error && !info) return (
        <Wrapper>
            <Card>
                <CardContent className="py-10 text-center space-y-4">
                    <div className="w-16 h-16 rounded-full bg-destructive/10 flex items-center justify-center mx-auto">
                        <XCircle className="w-8 h-8 text-destructive" />
                    </div>
                    <h1 className="text-xl font-bold">Invitación Inválida</h1>
                    <p className="text-muted-foreground text-sm">{error}</p>
                    <Button onClick={() => navigate(isSignedIn ? '/' : '/login')}>
                        {isSignedIn ? 'Ir al Dashboard' : 'Iniciar Sesión'}
                    </Button>
                </CardContent>
            </Card>
        </Wrapper>
    )

    if (success) return (
        <Wrapper>
            <Card>
                <CardContent className="py-10 text-center space-y-4">
                    <div className="w-16 h-16 rounded-full bg-emerald-500/10 flex items-center justify-center mx-auto">
                        <CheckCircle2 className="w-8 h-8 text-emerald-500" />
                    </div>
                    <h1 className="text-xl font-bold">¡Bienvenido al equipo!</h1>
                    <p className="text-muted-foreground text-sm">
                        Te has unido a <strong>{info?.organization_name}</strong> exitosamente.
                    </p>
                    <p className="text-xs text-muted-foreground">Redirigiendo al dashboard...</p>
                </CardContent>
            </Card>
        </Wrapper>
    )

    return (
        <Wrapper>
            <Card>
                <CardContent className="p-8 space-y-6">
                    {/* Header */}
                    <div className="text-center space-y-3">
                        <div className="w-16 h-16 rounded-2xl gradient-primary flex items-center justify-center mx-auto shadow-lg shadow-blue-500/20">
                            <Building2 className="w-8 h-8 text-white" />
                        </div>
                        <h1 className="text-2xl font-bold">Únete al equipo</h1>
                        <p className="text-muted-foreground text-sm">Has sido invitado a unirte a la organización</p>
                    </div>

                    {/* Org info */}
                    <div className="rounded-xl bg-muted/50 border border-border p-5 space-y-3">
                        <h2 className="text-lg font-semibold text-center">{info?.organization_name}</h2>
                        <div className="flex justify-center gap-6 text-sm">
                            <div className="text-center">
                                <p className="text-muted-foreground text-xs">Plan</p>
                                <p className="font-medium text-blue-500">{info?.organization_plan}</p>
                            </div>
                            <div className="text-center">
                                <p className="text-muted-foreground text-xs">Miembros</p>
                                <p className="font-medium">
                                    <span>{info?.member_count}</span>
                                    <span className="text-muted-foreground"> / {info?.member_limit}</span>
                                </p>
                            </div>
                        </div>
                    </div>

                    {/* Error */}
                    {error && (
                        <div className="flex items-center gap-2 p-3 rounded-lg bg-destructive/10 border border-destructive/20">
                            <AlertTriangle className="w-4 h-4 text-destructive flex-shrink-0" />
                            <p className="text-sm text-destructive">{error}</p>
                        </div>
                    )}

                    {/* Action */}
                    {isSignedIn ? (
                        <div className="space-y-4">
                            <div className="grid grid-cols-2 gap-3">
                                <div className="space-y-1.5">
                                    <Label htmlFor="join-first">Nombre</Label>
                                    <Input
                                        id="join-first"
                                        value={firstName}
                                        onChange={(e) => setFirstName(e.target.value)}
                                        placeholder="Tu nombre"
                                    />
                                </div>
                                <div className="space-y-1.5">
                                    <Label htmlFor="join-last">Apellido</Label>
                                    <Input
                                        id="join-last"
                                        value={lastName}
                                        onChange={(e) => setLastName(e.target.value)}
                                        placeholder="Tu apellido"
                                    />
                                </div>
                            </div>
                            <Button className="w-full" size="lg" onClick={handleJoin} disabled={joining}>
                                {joining ? <Loader2 className="w-5 h-5 animate-spin" /> : <Users className="w-5 h-5" />}
                                {joining ? 'Uniendose...' : 'Unirse a la organizacion'}
                            </Button>
                        </div>
                    ) : (
                        <div className="space-y-3">
                            <p className="text-sm text-center text-muted-foreground">
                                Debes iniciar sesión o registrarte para unirte.
                            </p>
                            <div className="flex gap-3">
                                <Button
                                    variant="outline"
                                    className="flex-1"
                                    onClick={() => { sessionStorage.setItem('pendingInvite', token); navigate('/login') }}
                                >
                                    Iniciar Sesión
                                </Button>
                                <Button
                                    className="flex-1"
                                    onClick={() => { sessionStorage.setItem('pendingInvite', token); navigate('/register') }}
                                >
                                    Registrarse
                                </Button>
                            </div>
                        </div>
                    )}
                </CardContent>
            </Card>
        </Wrapper>
    )
}
