import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { toast } from 'sonner'
import api from '../lib/api'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import {
    Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select'
import {
    Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter,
} from '@/components/ui/dialog'
import { LifeBuoy, Plus, Loader2, Send, ArrowLeft, CheckCircle2 } from 'lucide-react'

const CATEGORY_LABELS = { error: 'Error', incidencia: 'Incidencia', duda: 'Duda', otro: 'Otro' }
const PRIORITY_LABELS = { low: 'Baja', medium: 'Media', high: 'Alta' }
const STATUS_LABELS = { open: 'Abierto', in_progress: 'En progreso', closed: 'Cerrado' }
const STATUS_COLOR = {
    open: 'bg-blue-500/15 text-blue-500 border-blue-500/30',
    in_progress: 'bg-amber-500/15 text-amber-500 border-amber-500/30',
    closed: 'bg-emerald-500/15 text-emerald-500 border-emerald-500/30',
}
const PRIORITY_COLOR = {
    low: 'bg-slate-500/15 text-slate-500 border-slate-500/30',
    medium: 'bg-amber-500/15 text-amber-500 border-amber-500/30',
    high: 'bg-destructive/15 text-destructive border-destructive/30',
}

function formatDate(iso) {
    return new Date(iso).toLocaleString('es-VE', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })
}

export default function Support() {
    const [tickets, setTickets] = useState([])
    const [loading, setLoading] = useState(true)
    const [selected, setSelected] = useState(null)
    const [showNewDialog, setShowNewDialog] = useState(false)

    useEffect(() => { loadTickets() }, [])

    async function loadTickets() {
        try {
            const res = await api.get('/support/tickets/')
            setTickets(res.data)
        } catch (err) {
            toast.error('Error al cargar tickets de soporte.')
        } finally {
            setLoading(false)
        }
    }

    async function openTicket(id) {
        try {
            const res = await api.get(`/support/tickets/${id}/`)
            setSelected(res.data)
        } catch (err) {
            toast.error('Error al cargar el ticket.')
        }
    }

    return (
        <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            className="max-w-3xl mx-auto space-y-5"
        >
            {selected ? (
                <TicketThread
                    ticket={selected}
                    onBack={() => { setSelected(null); loadTickets() }}
                    onUpdated={setSelected}
                />
            ) : (
                <>
                    <div className="flex items-start justify-between flex-wrap gap-4">
                        <div>
                            <h1 className="text-2xl font-bold flex items-center gap-2">
                                <LifeBuoy className="w-6 h-6 text-emerald-500" /> Soporte
                            </h1>
                            <p className="text-muted-foreground text-sm mt-1">
                                Reporta errores, incidencias o dudas sobre la plataforma.
                            </p>
                        </div>
                        <Button onClick={() => setShowNewDialog(true)} className="gap-2">
                            <Plus className="w-4 h-4" /> Nuevo Ticket
                        </Button>
                    </div>

                    <Card>
                        {loading ? (
                            <CardContent className="py-8 flex justify-center">
                                <Loader2 className="w-6 h-6 animate-spin text-emerald-500" />
                            </CardContent>
                        ) : tickets.length === 0 ? (
                            <CardContent className="py-14 text-center text-muted-foreground">
                                <LifeBuoy className="w-10 h-10 mx-auto mb-3 opacity-25" />
                                <p className="text-sm font-medium">Sin tickets de soporte.</p>
                                <p className="text-xs mt-1">Abre uno si tienes un error, incidencia o duda.</p>
                            </CardContent>
                        ) : (
                            <CardContent className="p-0">
                                <div className="divide-y divide-border">
                                    {tickets.map(t => (
                                        <button
                                            key={t.id}
                                            onClick={() => openTicket(t.id)}
                                            className="w-full flex items-center justify-between p-4 hover:bg-accent/50 transition-colors text-left"
                                        >
                                            <div className="min-w-0 flex-1">
                                                <p className="text-sm font-medium truncate">{t.subject}</p>
                                                <p className="text-xs text-muted-foreground mt-0.5">
                                                    {CATEGORY_LABELS[t.category]} · {formatDate(t.updated_at)}
                                                </p>
                                            </div>
                                            <div className="flex items-center gap-2 ml-4 flex-shrink-0">
                                                <Badge variant="outline" className={`text-[10px] ${PRIORITY_COLOR[t.priority]}`}>
                                                    {PRIORITY_LABELS[t.priority]}
                                                </Badge>
                                                <Badge variant="outline" className={`text-[10px] ${STATUS_COLOR[t.status]}`}>
                                                    {STATUS_LABELS[t.status]}
                                                </Badge>
                                            </div>
                                        </button>
                                    ))}
                                </div>
                            </CardContent>
                        )}
                    </Card>
                </>
            )}

            <NewTicketDialog
                open={showNewDialog}
                onOpenChange={setShowNewDialog}
                onCreated={(ticket) => { setShowNewDialog(false); loadTickets(); setSelected(ticket) }}
            />
        </motion.div>
    )
}

function NewTicketDialog({ open, onOpenChange, onCreated }) {
    const [subject, setSubject] = useState('')
    const [category, setCategory] = useState('duda')
    const [priority, setPriority] = useState('medium')
    const [body, setBody] = useState('')
    const [saving, setSaving] = useState(false)

    useEffect(() => {
        if (open) {
            setSubject(''); setCategory('duda'); setPriority('medium'); setBody('')
        }
    }, [open])

    async function handleSubmit(e) {
        e.preventDefault()
        if (!subject.trim() || !body.trim()) {
            toast.error('Completa el asunto y la descripción.')
            return
        }
        setSaving(true)
        try {
            const res = await api.post('/support/tickets/', { subject, category, priority, body })
            toast.success('Ticket creado. Te responderemos pronto.')
            onCreated(res.data)
        } catch (err) {
            toast.error('Error al crear el ticket.')
        } finally {
            setSaving(false)
        }
    }

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-lg">
                <DialogHeader>
                    <DialogTitle>Nuevo Ticket de Soporte</DialogTitle>
                    <DialogDescription>
                        Cuéntanos qué pasó — un error, una incidencia o una duda.
                    </DialogDescription>
                </DialogHeader>
                <form onSubmit={handleSubmit} className="space-y-4">
                    <div className="space-y-1.5">
                        <Label htmlFor="subject">Asunto</Label>
                        <Input
                            id="subject"
                            value={subject}
                            onChange={e => setSubject(e.target.value)}
                            placeholder="Ej. El escaneo no termina nunca"
                        />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-1.5">
                            <Label>Categoría</Label>
                            <Select value={category} onValueChange={setCategory}>
                                <SelectTrigger><SelectValue /></SelectTrigger>
                                <SelectContent>
                                    {Object.entries(CATEGORY_LABELS).map(([v, l]) => (
                                        <SelectItem key={v} value={v}>{l}</SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>
                        <div className="space-y-1.5">
                            <Label>Prioridad</Label>
                            <Select value={priority} onValueChange={setPriority}>
                                <SelectTrigger><SelectValue /></SelectTrigger>
                                <SelectContent>
                                    {Object.entries(PRIORITY_LABELS).map(([v, l]) => (
                                        <SelectItem key={v} value={v}>{l}</SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>
                    </div>
                    <div className="space-y-1.5">
                        <Label htmlFor="body">Descripción</Label>
                        <Textarea
                            id="body"
                            rows={4}
                            value={body}
                            onChange={e => setBody(e.target.value)}
                            placeholder="Describe el problema con el mayor detalle posible..."
                        />
                    </div>
                    <DialogFooter>
                        <Button type="button" variant="outline" onClick={() => onOpenChange(false)} disabled={saving}>
                            Cancelar
                        </Button>
                        <Button type="submit" disabled={saving}>
                            {saving && <Loader2 className="w-4 h-4 animate-spin mr-2" />}
                            Enviar Ticket
                        </Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    )
}

function TicketThread({ ticket, onBack, onUpdated }) {
    const [body, setBody] = useState('')
    const [sending, setSending] = useState(false)

    async function handleSend() {
        if (!body.trim()) return
        setSending(true)
        try {
            await api.post(`/support/tickets/${ticket.id}/messages/`, { body })
            const res = await api.get(`/support/tickets/${ticket.id}/`)
            onUpdated(res.data)
            setBody('')
        } catch (err) {
            toast.error('Error al enviar el mensaje.')
        } finally {
            setSending(false)
        }
    }

    const isClosed = ticket.status === 'closed'

    return (
        <div className="space-y-4">
            <Button variant="ghost" size="sm" onClick={onBack} className="gap-1.5 -ml-2">
                <ArrowLeft className="w-4 h-4" /> Volver a mis tickets
            </Button>

            <Card>
                <CardContent className="p-5 space-y-3">
                    <div className="flex items-start justify-between gap-3 flex-wrap">
                        <div>
                            <h2 className="text-lg font-semibold">{ticket.subject}</h2>
                            <p className="text-xs text-muted-foreground mt-0.5">
                                {CATEGORY_LABELS[ticket.category]} · Abierto {formatDate(ticket.created_at)}
                            </p>
                        </div>
                        <div className="flex items-center gap-2">
                            <Badge variant="outline" className={`text-[10px] ${PRIORITY_COLOR[ticket.priority]}`}>
                                {PRIORITY_LABELS[ticket.priority]}
                            </Badge>
                            <Badge variant="outline" className={`text-[10px] ${STATUS_COLOR[ticket.status]}`}>
                                {STATUS_LABELS[ticket.status]}
                            </Badge>
                        </div>
                    </div>
                </CardContent>
            </Card>

            <div className="space-y-3">
                {ticket.messages.map(m => (
                    <div key={m.id} className={`flex ${m.is_staff ? 'justify-start' : 'justify-end'}`}>
                        <div className={`max-w-[80%] rounded-xl p-3 text-sm ${
                            m.is_staff
                                ? 'bg-emerald-500/10 border border-emerald-500/20'
                                : 'bg-accent border border-border'
                        }`}>
                            <p className="whitespace-pre-wrap">{m.body}</p>
                            <p className="text-[10px] text-muted-foreground mt-1.5">
                                {m.is_staff ? 'Soporte Vigia' : m.author_email} · {formatDate(m.created_at)}
                            </p>
                        </div>
                    </div>
                ))}
            </div>

            {isClosed ? (
                <div className="flex items-center gap-2 justify-center text-sm text-muted-foreground py-3 border rounded-xl bg-muted/30">
                    <CheckCircle2 className="w-4 h-4 text-emerald-500" /> Ticket cerrado. Escribe para reabrirlo.
                </div>
            ) : null}

            <div className="flex gap-2">
                <Textarea
                    rows={2}
                    value={body}
                    onChange={e => setBody(e.target.value)}
                    placeholder="Escribe tu respuesta..."
                    className="resize-none"
                />
                <Button onClick={handleSend} disabled={sending || !body.trim()} className="self-end gap-1.5">
                    {sending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                </Button>
            </div>
        </div>
    )
}
