import { useState, useEffect } from 'react'
import { useUser } from '@clerk/clerk-react'
import { motion } from 'framer-motion'
import { toast } from 'sonner'
import api from '../lib/api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'
import {
    Dialog, DialogContent, DialogHeader, DialogTitle,
    DialogDescription, DialogFooter,
} from '@/components/ui/dialog'
import { User, Building, Save, Loader2, LogOut, AlertTriangle } from 'lucide-react'

export default function Profile() {
    const { user } = useUser()
    const [profile, setProfile] = useState({ first_name: '', last_name: '', organization_name: '', member_count: 1 })
    const [originalOrgName, setOriginalOrgName] = useState('')
    const [role, setRole] = useState('user')
    const [saving,    setSaving]    = useState(false)
    const [leaving,   setLeaving]   = useState(false)
    const [leaveError, setLeaveError] = useState(null)
    const [showModal, setShowModal] = useState(false)
    const [showRenameConfirm, setShowRenameConfirm] = useState(false)

    // Only the org's own admins can rename it — a regular invited member
    // can view it but the only membership action available to them is
    // leaving (below).
    const canEditOrgName = role === 'org_admin' || role === 'admin'

    useEffect(() => {
        const controller = new AbortController()
        loadProfile(controller.signal)
        return () => controller.abort()
    }, [])

    async function loadProfile(signal) {
        try {
            const res = await api.get('/auth/profile/', { signal })
            const orgName = res.data.organization?.name || ''
            setProfile({
                first_name: res.data.first_name || '',
                last_name: res.data.last_name || '',
                organization_name: orgName,
                member_count: res.data.organization?.member_count || 1,
            })
            setOriginalOrgName(orgName)
            setRole(res.data.role || 'user')
        } catch (err) {
            if (err.code === 'ERR_CANCELED') return
            console.error('Failed to load profile:', err)
        }
    }

    function handleSubmit(e) {
        e.preventDefault()
        const orgNameChanged = canEditOrgName && profile.organization_name !== originalOrgName
        if (orgNameChanged) {
            setShowRenameConfirm(true)
            return
        }
        doSave()
    }

    async function doSave() {
        setShowRenameConfirm(false)
        setSaving(true)
        try {
            await api.patch('/auth/profile/', profile)
            if (canEditOrgName && profile.organization_name !== originalOrgName) {
                await api.patch('/auth/organization/', { name: profile.organization_name })
                setOriginalOrgName(profile.organization_name)
            }
            toast.success('Perfil guardado exitosamente.')
        } catch (err) {
            const detail = err.response?.data?.detail
            toast.error(detail || 'Error al guardar el perfil.')
        } finally {
            setSaving(false)
        }
    }

    async function leaveOrganization() {
        setLeaving(true)
        setLeaveError(null)
        try {
            await api.post('/auth/team/leave/')
            window.location.reload()
        } catch (err) {
            setLeaveError(err.response?.data?.detail || 'Error al intentar salir.')
            setLeaving(false)
        }
    }

    return (
        <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            className="max-w-2xl mx-auto space-y-6"
        >
            <div>
                <h1 className="text-2xl font-bold flex items-center gap-2">
                    <User className="w-6 h-6 text-blue-500" /> Perfil
                </h1>
                <p className="text-muted-foreground text-sm mt-1">
                    Gestiona tu información personal y organización.
                </p>
            </div>

            <Card>
                <CardHeader className="pb-4">
                    <CardTitle className="text-base">Información Personal</CardTitle>
                </CardHeader>
                <CardContent>
                    <form onSubmit={handleSubmit} className="space-y-5">
                        {/* Email read-only */}
                        <div className="space-y-1.5">
                            <Label>Email</Label>
                            <Input
                                type="email"
                                value={user?.primaryEmailAddress?.emailAddress || ''}
                                disabled
                                className="text-muted-foreground"
                            />
                        </div>

                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                            <div className="space-y-1.5">
                                <Label htmlFor="first_name">Nombre</Label>
                                <Input
                                    id="first_name"
                                    value={profile.first_name}
                                    onChange={(e) => setProfile({ ...profile, first_name: e.target.value })}
                                />
                            </div>
                            <div className="space-y-1.5">
                                <Label htmlFor="last_name">Apellido</Label>
                                <Input
                                    id="last_name"
                                    value={profile.last_name}
                                    onChange={(e) => setProfile({ ...profile, last_name: e.target.value })}
                                />
                            </div>
                        </div>

                        <div className="space-y-1.5">
                            <Label htmlFor="org_name" className="flex items-center gap-1.5">
                                <Building className="w-4 h-4 text-purple-500" /> Organización
                            </Label>
                            <Input
                                id="org_name"
                                value={profile.organization_name}
                                onChange={(e) => setProfile({ ...profile, organization_name: e.target.value })}
                                placeholder="Nombre de tu empresa"
                                disabled={!canEditOrgName}
                                className={!canEditOrgName ? 'text-muted-foreground' : ''}
                            />
                            {!canEditOrgName && (
                                <p className="text-xs text-muted-foreground">
                                    Solo un administrador de la organización puede cambiar este nombre.
                                </p>
                            )}
                        </div>

                        <div className="flex justify-end pt-2">
                            <Button type="submit" disabled={saving}>
                                {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                                Guardar
                            </Button>
                        </div>
                    </form>
                </CardContent>
            </Card>

            {/* Danger zone */}
            <Card className="border-destructive/20">
                <CardContent className="p-5">
                    <div className="flex items-start gap-3">
                        <div className="w-10 h-10 rounded-lg bg-destructive/10 flex items-center justify-center flex-shrink-0">
                            <AlertTriangle className="w-5 h-5 text-destructive" />
                        </div>
                        <div className="flex-1 min-w-0">
                            <p className="font-medium text-sm">Salir de la organización</p>
                            <p className="text-xs text-muted-foreground mt-0.5">
                                Perderás el acceso a los datos ({profile.member_count} miembros actuales).
                            </p>
                        </div>
                        <Button
                            variant="destructive"
                            size="sm"
                            onClick={() => setShowModal(true)}
                            className="flex-shrink-0"
                        >
                            <LogOut className="w-4 h-4" /> Salir
                        </Button>
                    </div>
                </CardContent>
            </Card>

            {/* Leave confirmation dialog */}
            <Dialog open={showModal} onOpenChange={(open) => !leaving && setShowModal(open)}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle className="flex items-center gap-2">
                            <AlertTriangle className="w-5 h-5 text-destructive" />
                            ¿Salir de la organización?
                        </DialogTitle>
                        <DialogDescription>
                            Esta acción es irreversible. Perderás el acceso a todos los datos y escaneos asociados.
                        </DialogDescription>
                    </DialogHeader>

                    <div className="rounded-lg bg-destructive/5 border border-destructive/15 p-3 text-xs text-center text-muted-foreground">
                        Podrás aceptar nuevas invitaciones o crear tu propia organización cuando quieras.
                    </div>

                    {leaveError && (
                        <p className="text-destructive text-sm text-center bg-destructive/10 p-2 rounded-lg">
                            {leaveError}
                        </p>
                    )}

                    <DialogFooter className="gap-2">
                        <Button variant="outline" onClick={() => setShowModal(false)} disabled={leaving}>
                            Cancelar
                        </Button>
                        <Button variant="destructive" onClick={leaveOrganization} disabled={leaving}>
                            {leaving ? <Loader2 className="w-4 h-4 animate-spin" /> : <LogOut className="w-4 h-4" />}
                            {leaving ? 'Saliendo...' : 'Confirmar Salida'}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            {/* Org rename confirmation dialog */}
            <Dialog open={showRenameConfirm} onOpenChange={(open) => !saving && setShowRenameConfirm(open)}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle className="flex items-center gap-2">
                            <Building className="w-5 h-5 text-purple-500" />
                            ¿Cambiar el nombre de la organización?
                        </DialogTitle>
                        <DialogDescription>
                            Todo tu equipo verá el nuevo nombre <strong>"{profile.organization_name}"</strong> en
                            lugar de "{originalOrgName}".
                        </DialogDescription>
                    </DialogHeader>
                    <DialogFooter className="gap-2">
                        <Button variant="outline" onClick={() => setShowRenameConfirm(false)} disabled={saving}>
                            Cancelar
                        </Button>
                        <Button onClick={doSave} disabled={saving}>
                            {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                            Confirmar Cambio
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </motion.div>
    )
}
