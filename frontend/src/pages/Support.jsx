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
import {
    LifeBuoy, Plus, Loader2, Send, ArrowLeft, CheckCircle2, Search,
    MoreHorizontal, Paperclip, ShieldCheck, FilePlus2,
} from 'lucide-react'
import {
    CATEGORY_LABELS, CATEGORY_ICONS, CATEGORY_ICON_COLOR,
    PRIORITY_LABELS, PRIORITY_COLOR, STATUS_LABELS, STATUS_COLOR,
    formatDate, AttachmentThumbs, useImageDropzone, DropOverlay,
    ImageFileInput, ImageThumbnails,
} from '../lib/supportShared.jsx'

export default function Support() {
    const [tickets, setTickets] = useState([])
    const [loading, setLoading] = useState(true)
    const [selected, setSelected] = useState(null)
    const [showNewDialog, setShowNewDialog] = useState(false)
    const [search, setSearch] = useState('')

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

    const filtered = tickets.filter(t => t.subject.toLowerCase().includes(search.toLowerCase()))

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
                                <span className="w-9 h-9 rounded-xl flex items-center justify-center bg-emerald-500/10">
                                    <LifeBuoy className="w-5 h-5 text-emerald-500" />
                                </span>
                                Soporte
                                {!loading && (
                                    <Badge variant="secondary" className="text-xs font-semibold">
                                        {tickets.length} {tickets.length === 1 ? 'ticket' : 'tickets'}
                                    </Badge>
                                )}
                            </h1>
                            <p className="text-muted-foreground text-sm mt-1">
                                Reporta errores, incidencias o dudas sobre la plataforma.
                            </p>
                        </div>
                        <Button onClick={() => setShowNewDialog(true)} className="gap-2">
                            <Plus className="w-4 h-4" /> Nuevo Ticket
                        </Button>
                    </div>

                    {tickets.length > 0 && (
                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                            <Input
                                value={search}
                                onChange={e => setSearch(e.target.value)}
                                placeholder="Buscar por asunto..."
                                className="pl-9"
                            />
                        </div>
                    )}

                    <Card>
                        {loading ? (
                            <CardContent className="py-8 flex justify-center">
                                <Loader2 className="w-6 h-6 animate-spin text-emerald-500" />
                            </CardContent>
                        ) : tickets.length === 0 ? (
                            <CardContent className="py-14 text-center text-muted-foreground">
                                <div className="w-14 h-14 rounded-2xl bg-emerald-500/10 flex items-center justify-center mx-auto mb-3">
                                    <LifeBuoy className="w-7 h-7 text-emerald-500" />
                                </div>
                                <p className="text-sm font-medium text-foreground">Sin tickets de soporte.</p>
                                <p className="text-xs mt-1">Abre uno si tienes un error, incidencia o duda.</p>
                            </CardContent>
                        ) : filtered.length === 0 ? (
                            <CardContent className="py-10 text-center text-muted-foreground text-sm">
                                Sin resultados para "{search}".
                            </CardContent>
                        ) : (
                            <CardContent className="p-0">
                                <div className="divide-y divide-border">
                                    {filtered.map(t => {
                                        const CategoryIcon = CATEGORY_ICONS[t.category] || MoreHorizontal
                                        return (
                                            <button
                                                key={t.id}
                                                onClick={() => openTicket(t.id)}
                                                className="w-full flex items-center gap-3 p-4 hover:bg-accent/50 transition-colors text-left"
                                            >
                                                <span className={`w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 ${CATEGORY_ICON_COLOR[t.category]}`}>
                                                    <CategoryIcon className="w-4 h-4" />
                                                </span>
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
                                        )
                                    })}
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
    const [images, setImages] = useState([])
    const [saving, setSaving] = useState(false)
    const { inputRef, isDragging, dragHandlers, addFiles, removeAt, isFull, openPicker } = useImageDropzone(images, setImages)

    useEffect(() => {
        if (open) {
            setSubject(''); setCategory('duda'); setPriority('medium'); setBody(''); setImages([])
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
            const formData = new FormData()
            formData.append('subject', subject)
            formData.append('category', category)
            formData.append('priority', priority)
            formData.append('body', body)
            images.forEach(img => formData.append('images', img.file))

            const res = await api.post('/support/tickets/', formData, {
                headers: { 'Content-Type': undefined },
            })
            toast.success('Ticket creado. Te responderemos pronto.')
            onCreated(res.data)
        } catch (err) {
            toast.error(err.response?.data?.detail || 'Error al crear el ticket.')
        } finally {
            setSaving(false)
        }
    }

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-lg" {...dragHandlers}>
                <DropOverlay show={isDragging} />
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                        <LifeBuoy className="w-5 h-5 text-emerald-500" /> Nuevo Ticket de Soporte
                    </DialogTitle>
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
                    <div className="space-y-1.5">
                        <Label className="flex items-center gap-1.5">
                            <Paperclip className="w-3.5 h-3.5" /> Capturas de pantalla (opcional)
                        </Label>
                        {images.length === 0 ? (
                            <button
                                type="button"
                                onClick={openPicker}
                                className="w-full flex flex-col items-center gap-1 py-3 rounded-xl border-2 border-dashed border-border text-muted-foreground hover:text-emerald-500 hover:border-emerald-500/50 transition-colors"
                            >
                                <FilePlus2 className="w-5 h-5" />
                                <span className="text-xs">
                                    Arrastra, pega (Ctrl+V) o <span className="underline">selecciona</span> una imagen
                                </span>
                            </button>
                        ) : (
                            <ImageThumbnails images={images} onRemove={removeAt} onAddClick={openPicker} isFull={isFull} />
                        )}
                        <ImageFileInput inputRef={inputRef} onFiles={addFiles} />
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

function MessageBubble({ m }) {
    return (
        <div className={`flex gap-2.5 ${m.is_staff ? 'justify-start' : 'justify-end'}`}>
            {m.is_staff && (
                <span className="w-7 h-7 rounded-full bg-emerald-500/15 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" />
                </span>
            )}
            <div className={`max-w-[80%] rounded-2xl px-3.5 py-2.5 text-sm ${
                m.is_staff
                    ? 'bg-emerald-500/10 border border-emerald-500/20 rounded-tl-sm'
                    : 'bg-accent border border-border rounded-tr-sm'
            }`}>
                <p className="whitespace-pre-wrap">{m.body}</p>
                <AttachmentThumbs attachments={m.attachments} />
                <p className="text-[10px] text-muted-foreground mt-1.5">
                    {m.is_staff ? 'Soporte Vigia' : m.author_email} · {formatDate(m.created_at)}
                </p>
            </div>
        </div>
    )
}

function TicketThread({ ticket, onBack, onUpdated }) {
    const [body, setBody] = useState('')
    const [images, setImages] = useState([])
    const [sending, setSending] = useState(false)
    const { inputRef, isDragging, dragHandlers, addFiles, removeAt, isFull, openPicker } = useImageDropzone(images, setImages)

    async function handleSend() {
        if (!body.trim()) return
        setSending(true)
        try {
            const formData = new FormData()
            formData.append('body', body)
            images.forEach(img => formData.append('images', img.file))
            await api.post(`/support/tickets/${ticket.id}/messages/`, formData, {
                headers: { 'Content-Type': undefined },
            })
            const res = await api.get(`/support/tickets/${ticket.id}/`)
            onUpdated(res.data)
            setBody('')
            setImages([])
        } catch (err) {
            toast.error(err.response?.data?.detail || 'Error al enviar el mensaje.')
        } finally {
            setSending(false)
        }
    }

    const isClosed = ticket.status === 'closed'
    const CategoryIcon = CATEGORY_ICONS[ticket.category] || MoreHorizontal

    return (
        <div className="space-y-4">
            <Button variant="ghost" size="sm" onClick={onBack} className="gap-1.5 -ml-2">
                <ArrowLeft className="w-4 h-4" /> Volver a mis tickets
            </Button>

            <Card>
                <CardContent className="p-5 space-y-3">
                    <div className="flex items-start justify-between gap-3 flex-wrap">
                        <div className="flex items-start gap-3">
                            <span className={`w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 ${CATEGORY_ICON_COLOR[ticket.category]}`}>
                                <CategoryIcon className="w-4 h-4" />
                            </span>
                            <div>
                                <h2 className="text-lg font-semibold leading-tight">{ticket.subject}</h2>
                                <p className="text-xs text-muted-foreground mt-0.5">
                                    {CATEGORY_LABELS[ticket.category]} · Abierto {formatDate(ticket.created_at)}
                                </p>
                            </div>
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
                {ticket.messages.map(m => <MessageBubble key={m.id} m={m} />)}
            </div>

            {isClosed ? (
                <div className="flex items-center gap-2 justify-center text-sm text-muted-foreground py-3 border rounded-xl bg-muted/30">
                    <CheckCircle2 className="w-4 h-4 text-emerald-500" /> Ticket cerrado. Escribe para reabrirlo.
                </div>
            ) : null}

            <div className="relative rounded-xl" {...dragHandlers}>
                <DropOverlay show={isDragging} />
                <div className="space-y-2">
                    <ImageThumbnails images={images} onRemove={removeAt} onAddClick={openPicker} isFull={isFull} />
                    <div className="flex gap-2">
                        <Textarea
                            rows={2}
                            value={body}
                            onChange={e => setBody(e.target.value)}
                            placeholder="Escribe tu respuesta..."
                            className="resize-none"
                        />
                        <div className="flex flex-col gap-2 self-end">
                            <Button
                                type="button"
                                variant="outline"
                                size="icon"
                                onClick={openPicker}
                                aria-label="Adjuntar imagen"
                            >
                                <Paperclip className="w-4 h-4" />
                            </Button>
                            <Button onClick={handleSend} disabled={sending || !body.trim()} className="gap-1.5">
                                {sending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                            </Button>
                        </div>
                    </div>
                </div>
                <ImageFileInput inputRef={inputRef} onFiles={addFiles} />
            </div>
        </div>
    )
}
