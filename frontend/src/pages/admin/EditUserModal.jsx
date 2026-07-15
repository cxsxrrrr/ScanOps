import { useState, useEffect } from 'react'
import {
    Dialog, DialogContent, DialogHeader,
    DialogTitle, DialogDescription, DialogFooter,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Loader2, Trash2 } from 'lucide-react'
import api from '../../lib/api'
import { toast } from 'sonner'

export function EditUserModal({ user, orgs, open, onOpenChange, onSuccess }) {
    const [loading, setLoading] = useState(false)
    const [deleting, setDeleting] = useState(false)
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
            toast.error('Error al actualizar usuario')
        } finally {
            setLoading(false)
        }
    }

    async function handleDelete() {
        if (!confirm(`¿Estás seguro de que quieres eliminar a ${user.email}? Esta acción no se puede deshacer.`)) return
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
                    <DialogTitle>Editar Usuario</DialogTitle>
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
                </div>

                <DialogFooter className="flex items-center sm:justify-between">
                    <Button 
                        variant="destructive" 
                        size="sm" 
                        onClick={handleDelete}
                        disabled={deleting || loading}
                        className="w-full sm:w-auto"
                    >
                        {deleting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Trash2 className="w-4 h-4 mr-2" />}
                        Eliminar
                    </Button>
                    <div className="flex gap-2 w-full sm:w-auto mt-2 sm:mt-0">
                        <Button variant="outline" onClick={() => onOpenChange(false)} disabled={loading} className="w-full sm:w-auto">
                            Cancelar
                        </Button>
                        <Button onClick={handleSave} disabled={loading || deleting} className="w-full sm:w-auto">
                            {loading && <Loader2 className="w-4 h-4 animate-spin mr-2" />}
                            Guardar
                        </Button>
                    </div>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    )
}
