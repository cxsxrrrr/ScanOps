import { useState, useEffect } from 'react'
import { toast } from 'sonner'
import api from '../../lib/api'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Input } from '@/components/ui/input'
import {
    Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select'
import { LifeBuoy, Loader2, ArrowLeft, Send, Search } from 'lucide-react'

const CATEGORY_LABELS = { error: 'Error', incidencia: 'Incidencia', duda: 'Duda', otro: 'Otro' }
const PRIORITY_LABELS = { low: 'Baja', medium: 'Media', high: 'Alta' }
const STATUS_LABELS = { open: 'Abierto', in_progress: 'En progreso', closed: 'Cerrado' }
// Status colors read as urgency: open (unanswered) is the most critical, closed is resolved/calm.
const STATUS_COLOR = {
    open: 'severity-high',
    in_progress: 'severity-medium',
    closed: 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/25',
}
// Reuse the same severity palette used for scan findings, so criticality reads consistently app-wide.
const PRIORITY_COLOR = {
    low: 'severity-low',
    medium: 'severity-medium',
    high: 'severity-critical',
}

function formatDate(iso) {
    return new Date(iso).toLocaleString('es-VE', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })
}

export function AdminSupportPanel() {
    const [tickets, setTickets] = useState([])
    const [loading, setLoading] = useState(true)
    const [selected, setSelected] = useState(null)
    const [statusFilter, setStatusFilter] = useState('all')
    const [search, setSearch] = useState('')

    useEffect(() => { loadTickets() }, [])

    async function loadTickets() {
        setLoading(true)
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

    const filtered = tickets
        .filter(t => statusFilter === 'all' || t.status === statusFilter)
        .filter(t =>
            t.subject.toLowerCase().includes(search.toLowerCase()) ||
            t.created_by_email.toLowerCase().includes(search.toLowerCase()) ||
            t.organization.toLowerCase().includes(search.toLowerCase())
        )

    if (selected) {
        return (
            <AdminTicketThread
                ticket={selected}
                onBack={() => { setSelected(null); loadTickets() }}
                onUpdated={setSelected}
            />
        )
    }

    return (
        <div className="space-y-3">
            <div className="flex items-center justify-between gap-2 flex-wrap">
                <h3 className="text-sm font-semibold flex items-center gap-2">
                    <LifeBuoy className="w-4 h-4 text-emerald-500" /> Tickets de Soporte
                    {!loading && (
                        <Badge variant="secondary" className="text-xs font-semibold">
                            {tickets.length}
                        </Badge>
                    )}
                </h3>
                <div className="flex items-center gap-2">
                    <div className="relative">
                        <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
                        <Input
                            value={search}
                            onChange={e => setSearch(e.target.value)}
                            placeholder="Buscar..."
                            className="h-8 text-xs pl-8 w-48"
                        />
                    </div>
                    <Select value={statusFilter} onValueChange={setStatusFilter}>
                        <SelectTrigger className="w-40 h-8 text-xs"><SelectValue /></SelectTrigger>
                        <SelectContent>
                            <SelectItem value="all">Todos</SelectItem>
                            <SelectItem value="open">Abierto</SelectItem>
                            <SelectItem value="in_progress">En progreso</SelectItem>
                            <SelectItem value="closed">Cerrado</SelectItem>
                        </SelectContent>
                    </Select>
                </div>
            </div>

            <Card>
                {loading ? (
                    <CardContent className="py-8 flex justify-center">
                        <Loader2 className="w-6 h-6 animate-spin text-emerald-500" />
                    </CardContent>
                ) : filtered.length === 0 ? (
                    <CardContent className="py-10 text-center text-muted-foreground text-sm">
                        Sin tickets de soporte.
                    </CardContent>
                ) : (
                    <CardContent className="p-0">
                        <div className="divide-y divide-border">
                            {filtered.map(t => (
                                <button
                                    key={t.id}
                                    onClick={() => openTicket(t.id)}
                                    className="w-full flex items-center justify-between p-3 hover:bg-accent/50 transition-colors text-left"
                                >
                                    <div className="min-w-0 flex-1">
                                        <p className="text-sm font-medium truncate">{t.subject}</p>
                                        <p className="text-xs text-muted-foreground mt-0.5">
                                            {t.organization} · {t.created_by_email} · {formatDate(t.updated_at)}
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
        </div>
    )
}

function AdminTicketThread({ ticket, onBack, onUpdated }) {
    const [body, setBody] = useState('')
    const [sending, setSending] = useState(false)
    const [updatingStatus, setUpdatingStatus] = useState(false)

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

    async function handleStatusChange(newStatus) {
        setUpdatingStatus(true)
        try {
            await api.patch(`/support/tickets/${ticket.id}/`, { status: newStatus })
            const res = await api.get(`/support/tickets/${ticket.id}/`)
            onUpdated(res.data)
            toast.success('Estado actualizado.')
        } catch (err) {
            toast.error('Error al actualizar el estado.')
        } finally {
            setUpdatingStatus(false)
        }
    }

    return (
        <div className="space-y-4">
            <Button variant="ghost" size="sm" onClick={onBack} className="gap-1.5 -ml-2">
                <ArrowLeft className="w-4 h-4" /> Volver a tickets
            </Button>

            <Card>
                <CardContent className="p-5 space-y-3">
                    <div className="flex items-start justify-between gap-3 flex-wrap">
                        <div>
                            <h2 className="text-lg font-semibold">{ticket.subject}</h2>
                            <p className="text-xs text-muted-foreground mt-0.5">
                                {ticket.organization} · {ticket.created_by_email} · Abierto {formatDate(ticket.created_at)}
                            </p>
                        </div>
                        <Select value={ticket.status} onValueChange={handleStatusChange} disabled={updatingStatus}>
                            <SelectTrigger className="w-40 h-8 text-xs"><SelectValue /></SelectTrigger>
                            <SelectContent>
                                <SelectItem value="open">Abierto</SelectItem>
                                <SelectItem value="in_progress">En progreso</SelectItem>
                                <SelectItem value="closed">Cerrado</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>
                </CardContent>
            </Card>

            <div className="space-y-3">
                {ticket.messages.map(m => (
                    <div key={m.id} className={`flex ${m.is_staff ? 'justify-end' : 'justify-start'}`}>
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

            <div className="flex gap-2">
                <Textarea
                    rows={2}
                    value={body}
                    onChange={e => setBody(e.target.value)}
                    placeholder="Responder al usuario..."
                    className="resize-none"
                />
                <Button onClick={handleSend} disabled={sending || !body.trim()} className="self-end gap-1.5">
                    {sending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                </Button>
            </div>
        </div>
    )
}
