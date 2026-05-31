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

export function EditOrgModal({ org, open, onOpenChange, onSuccess }) {
    const [loading, setLoading] = useState(false)
    const [deleting, setDeleting] = useState(false)
    const [formData, setFormData] = useState({
        name: '',
        plan: 'free',
        url_limit: 1,
    })

    useEffect(() => {
        if (org && open) {
            setFormData({
                name: org.name || '',
                plan: org.plan || 'free',
                url_limit: org.url_limit || 1,
            })
        }
    }, [org, open])

    if (!org) return null

    async function handleSave() {
        setLoading(true)
        try {
            await api.put(`/admin/organizations/${org.id}/`, formData)
            toast.success('Organización actualizada')
            onSuccess()
            onOpenChange(false)
        } catch (err) {
            toast.error('Error al actualizar organización')
        } finally {
            setLoading(false)
        }
    }

    async function handleDelete() {
        if (!confirm(`¿Estás seguro de que quieres eliminar la organización ${org.name}? Los usuarios quedarán huérfanos.`)) return
        setDeleting(true)
        try {
            await api.delete(`/admin/organizations/${org.id}/`)
            toast.success('Organización eliminada')
            onSuccess()
            onOpenChange(false)
        } catch (err) {
            toast.error('Error al eliminar organización')
        } finally {
            setDeleting(false)
        }
    }

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[425px]">
                <DialogHeader>
                    <DialogTitle>Editar Organización</DialogTitle>
                    <DialogDescription>
                        Realiza cambios administrativos en {org.name}.
                    </DialogDescription>
                </DialogHeader>
                
                <div className="grid gap-4 py-4">
                    <div className="grid gap-2">
                        <Label htmlFor="name">Nombre</Label>
                        <Input
                            id="name"
                            value={formData.name}
                            onChange={(e) => setFormData(p => ({ ...p, name: e.target.value }))}
                        />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                        <div className="grid gap-2">
                            <Label>Plan</Label>
                            <Select
                                value={formData.plan}
                                onValueChange={(v) => setFormData(p => ({ ...p, plan: v }))}
                            >
                                <SelectTrigger>
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="free">Free</SelectItem>
                                    <SelectItem value="pro">Pro</SelectItem>
                                    <SelectItem value="ultimate">Ultimate</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                        <div className="grid gap-2">
                            <Label htmlFor="url_limit">Límite URLs</Label>
                            <Input
                                id="url_limit"
                                type="number"
                                min="1"
                                value={formData.url_limit}
                                onChange={(e) => setFormData(p => ({ ...p, url_limit: parseInt(e.target.value) || 1 }))}
                            />
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
