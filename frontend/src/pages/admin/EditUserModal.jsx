import { useState, useEffect } from 'react'
import {
    Dialog, DialogContent, DialogHeader,
    DialogTitle, DialogDescription, DialogFooter,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { Loader2, Trash2, Ban, ShieldCheck } from 'lucide-react'
import api from '../../lib/api'
import { toast } from 'sonner'

export function EditUserModal({ user, orgs, open, onOpenChange, onSuccess }) {
    const [loading, setLoading] = useState(false)
    const [deleting, setDeleting] = useState(false)
    const [blocking, setBlocking] = useState(false)
    const [confirmingDelete, setConfirmingDelete] = useState(false)
    const [isActive, setIsActive] = useState(true)
    const [formData, setFormData] = useState({
        first_name: '',
        last_name: '',
        role: 'user',
        organization: null,
    })

    useEffect(() => {
        if (user && open) {
            setFormData({
                first_name: user.first_name || '',
                last_name: user.last_name || '',
                role: user.role || 'user',
                // user_list (admin panel) returns a flat organization_id, not a
                // nested organization object — reading user.organization?.id
                // was always undefined, silently resetting every edited user
                // to "Sin organización" and wiping their org FK on save.
                organization: user.organization_id ?? user.organization?.id ?? null,
            })
            setIsActive(user.is_active !== false)
            setConfirmingDelete(false)
        }
    }, [user, open])

    if (!user) return null

    async function handleSave() {
        setLoading(true)
        try {
            await api.put(`/admin/users/${user.id}/`, formData)
            toast.success('Usuario actualizado')
            onSuccess()
            onOpenChange(false)
        } catch (err) {
            const detail = err.response?.data?.organization?.[0]
                || err.response?.data?.role?.[0]
                || err.response?.data?.detail
            toast.error(detail || 'Error al actualizar usuario')
        } finally {
            setLoading(false)
        }
    }

    async function handleToggleBlock() {
        setBlocking(true)
        try {
            const nextActive = !isActive
            await api.put(`/admin/users/${user.id}/`, { is_active: nextActive })
            setIsActive(nextActive)
            toast.success(nextActive ? 'Usuario desbloqueado' : 'Usuario bloqueado')
            onSuccess()
        } catch (err) {
            toast.error(err.response?.data?.detail || 'Error al actualizar el estado del usuario')
        } finally {
            setBlocking(false)
        }
    }

    async function handleDelete() {
        setDeleting(true)
        try {
            await api.delete(`/admin/users/${user.id}/`)
            toast.success('Usuario eliminado')
            onSuccess()
            onOpenChange(false)
        } catch (err) {
            toast.error('Error al eliminar usuario')
        } finally {
            setDeleting(false)
        }
    }

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[425px]">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                        Editar Usuario
                        {!isActive && (
                            <Badge variant="destructive" className="text-[10px]">BLOQUEADO</Badge>
                        )}
                    </DialogTitle>
                    <DialogDescription>
                        {user.email}
                    </DialogDescription>
                </DialogHeader>

                <div className="grid gap-4 py-4">
                    <div className="grid grid-cols-2 gap-4">
                        <div className="grid gap-2">
                            <Label htmlFor="first_name">Nombre</Label>
                            <Input
                                id="first_name"
                                value={formData.first_name}
                                onChange={(e) => setFormData(p => ({ ...p, first_name: e.target.value }))}
                            />
                        </div>
                        <div className="grid gap-2">
                            <Label htmlFor="last_name">Apellido</Label>
                            <Input
                                id="last_name"
                                value={formData.last_name}
                                onChange={(e) => setFormData(p => ({ ...p, last_name: e.target.value }))}
                            />
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div className="grid gap-2">
                            <Label>Rol</Label>
                            <Select
                                value={formData.role}
                                onValueChange={(v) => setFormData(p => ({ ...p, role: v }))}
                            >
                                <SelectTrigger>
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="user">User</SelectItem>
                                    <SelectItem value="org_admin">Org Admin</SelectItem>
                                    <SelectItem value="admin">Admin (plataforma)</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                        <div className="grid gap-2">
                            <Label>Organización</Label>
                            <Select
                                value={formData.organization ? String(formData.organization) : "none"}
                                onValueChange={(v) => setFormData(p => ({ ...p, organization: v === "none" ? null : parseInt(v) }))}
                            >
                                <SelectTrigger>
                                    <SelectValue placeholder="Sin organización" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="none">Sin organización</SelectItem>
                                    {orgs?.map(org => (
                                        <SelectItem key={org.id} value={String(org.id)}>{org.name}</SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>
                    </div>

                    <div className="flex items-center justify-between p-3 rounded-lg bg-muted/50 border border-border">
                        <div className="text-sm">
                            <p className="font-medium">{isActive ? 'Cuenta activa' : 'Cuenta bloqueada'}</p>
                            <p className="text-xs text-muted-foreground">
                                {isActive
                                    ? 'El usuario puede iniciar sesión y usar la plataforma.'
                                    : 'El usuario no puede autenticarse ni realizar ninguna acción.'}
                            </p>
                        </div>
                        <Button
                            variant={isActive ? 'outline' : 'default'}
                            size="sm"
                            onClick={handleToggleBlock}
                            disabled={blocking}
                        >
                            {blocking ? <Loader2 className="w-3.5 h-3.5 animate-spin mr-1.5" />
                                : isActive ? <Ban className="w-3.5 h-3.5 mr-1.5" /> : <ShieldCheck className="w-3.5 h-3.5 mr-1.5" />}
                            {isActive ? 'Bloquear' : 'Desbloquear'}
                        </Button>
                    </div>
                </div>

                <DialogFooter className="flex items-center sm:justify-between">
                    {confirmingDelete ? (
                        <div className="flex items-center gap-2 w-full sm:w-auto">
                            <span className="text-xs text-muted-foreground">¿Eliminar a {user.email}? No se puede deshacer.</span>
                            <Button variant="destructive" size="sm" onClick={handleDelete} disabled={deleting}>
                                {deleting ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Sí, eliminar'}
                            </Button>
                            <Button variant="ghost" size="sm" onClick={() => setConfirmingDelete(false)} disabled={deleting}>
                                Cancelar
                            </Button>
                        </div>
                    ) : (
                        <Button
                            variant="destructive"
                            size="sm"
                            onClick={() => setConfirmingDelete(true)}
                            disabled={deleting || loading}
                            className="w-full sm:w-auto"
                        >
                            <Trash2 className="w-4 h-4 mr-2" />
                            Eliminar
                        </Button>
                    )}
                    {!confirmingDelete && (
                        <div className="flex gap-2 w-full sm:w-auto mt-2 sm:mt-0">
                            <Button variant="outline" onClick={() => onOpenChange(false)} disabled={loading} className="w-full sm:w-auto">
                                Cancelar
                            </Button>
                            <Button onClick={handleSave} disabled={loading || deleting} className="w-full sm:w-auto">
                                {loading && <Loader2 className="w-4 h-4 animate-spin mr-2" />}
                                Guardar
                            </Button>
                        </div>
                    )}
                </DialogFooter>
            </DialogContent>
        </Dialog>
    )
}
