import { useRef, useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { toast } from 'sonner'
import { AlertTriangle, Zap, HelpCircle, MoreHorizontal, Paperclip, X, FilePlus2, Maximize2 } from 'lucide-react'
import { Dialog, DialogContent, DialogTitle, DialogDescription } from '@/components/ui/dialog'

export const CATEGORY_LABELS = { error: 'Error', incidencia: 'Incidencia', duda: 'Duda', otro: 'Otro' }
export const CATEGORY_ICONS = { error: AlertTriangle, incidencia: Zap, duda: HelpCircle, otro: MoreHorizontal }
export const CATEGORY_ICON_COLOR = {
    error: 'text-red-500 bg-red-500/10',
    incidencia: 'text-amber-500 bg-amber-500/10',
    duda: 'text-blue-500 bg-blue-500/10',
    otro: 'text-slate-500 bg-slate-500/10',
}
export const PRIORITY_LABELS = { low: 'Baja', medium: 'Media', high: 'Alta' }
export const STATUS_LABELS = { open: 'Abierto', in_progress: 'En progreso', closed: 'Cerrado' }
// Status colors read as urgency: open (unanswered) is the most critical, closed is resolved/calm.
export const STATUS_COLOR = {
    open: 'severity-high',
    in_progress: 'severity-medium',
    closed: 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/25',
}
// Reuse the same severity palette used for scan findings, so criticality reads consistently app-wide.
export const PRIORITY_COLOR = {
    low: 'severity-low',
    medium: 'severity-medium',
    high: 'severity-critical',
}
export const MAX_IMAGES = 3

export function formatDate(iso) {
    return new Date(iso).toLocaleString('es-VE', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })
}

/**
 * Poll `callback` every `intervalMs` while `enabled`. The callback ref is
 * refreshed every render (no deps) so it always sees latest props/state
 * without tearing down and rebuilding the interval on every change —
 * only `intervalMs`/`enabled` changes do that.
 */
export function usePolling(callback, intervalMs, enabled = true) {
    const callbackRef = useRef(callback)
    useEffect(() => { callbackRef.current = callback })

    useEffect(() => {
        if (!enabled) return
        const id = setInterval(() => callbackRef.current(), intervalMs)
        return () => clearInterval(id)
    }, [intervalMs, enabled])
}

/** Small red count badge for the top-right corner of a ticket row. */
export function UnreadBadge({ count }) {
    if (!count) return null
    return (
        <span className="absolute -top-1.5 -right-1.5 min-w-[18px] h-[18px] px-1 rounded-full bg-red-500 text-white text-[10px] font-bold flex items-center justify-center shadow">
            {count > 9 ? '9+' : count}
        </span>
    )
}

/**
 * Drag-and-drop + clipboard-paste + click-to-browse state for screenshot
 * attachments. Paste is bound on window while mounted so users don't have
 * to click into a specific box first. Spread `dragHandlers` onto whatever
 * container should act as the drop target (the whole dialog/composer, not
 * just a small box) and render <DropOverlay show={isDragging} /> inside it.
 */
export function useImageDropzone(images, onChange) {
    const inputRef = useRef(null)
    const [isDragging, setIsDragging] = useState(false)
    const dragCounter = useRef(0)

    const addFiles = useCallback((fileList) => {
        const incoming = Array.from(fileList).filter(f => f.type.startsWith('image/'))
        if (!incoming.length) return
        const room = MAX_IMAGES - images.length
        if (incoming.length > room) {
            toast.error(`Máximo ${MAX_IMAGES} imágenes por mensaje.`)
        }
        const accepted = incoming.slice(0, room).map(file => ({ file, url: URL.createObjectURL(file) }))
        if (accepted.length) onChange([...images, ...accepted])
    }, [images, onChange])

    function removeAt(i) {
        URL.revokeObjectURL(images[i].url)
        onChange(images.filter((_, idx) => idx !== i))
    }

    useEffect(() => {
        function onPaste(e) {
            const items = e.clipboardData?.items
            if (!items) return
            const files = Array.from(items)
                .filter(item => item.type.startsWith('image/'))
                .map(item => item.getAsFile())
                .filter(Boolean)
            if (files.length) {
                e.preventDefault()
                addFiles(files)
            }
        }
        window.addEventListener('paste', onPaste)
        return () => window.removeEventListener('paste', onPaste)
    }, [addFiles])

    const dragHandlers = {
        onDragEnter: (e) => { e.preventDefault(); dragCounter.current += 1; setIsDragging(true) },
        onDragLeave: (e) => { e.preventDefault(); dragCounter.current -= 1; if (dragCounter.current <= 0) setIsDragging(false) },
        onDragOver: (e) => e.preventDefault(),
        onDrop: (e) => {
            e.preventDefault()
            dragCounter.current = 0
            setIsDragging(false)
            if (e.dataTransfer.files?.length) addFiles(e.dataTransfer.files)
        },
    }

    return {
        inputRef,
        isDragging,
        dragHandlers,
        addFiles,
        removeAt,
        isFull: images.length >= MAX_IMAGES,
        openPicker: () => inputRef.current?.click(),
    }
}

/** Full-panel drag-over overlay — covers the whole drop target, not a tiny box. */
export function DropOverlay({ show }) {
    return (
        <AnimatePresence>
            {show && (
                <motion.div
                    initial={{ opacity: 0, scale: 0.97 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.97 }}
                    transition={{ duration: 0.15 }}
                    className="absolute -inset-1 z-50 flex items-center justify-center gap-2 rounded-xl border-2 border-dashed border-emerald-500 bg-emerald-500/10 backdrop-blur-sm shadow-lg pointer-events-none"
                >
                    <motion.div animate={{ y: [0, -4, 0] }} transition={{ repeat: Infinity, duration: 1.2 }}>
                        <FilePlus2 className="w-5 h-5 text-emerald-600 dark:text-emerald-400" strokeWidth={1.75} />
                    </motion.div>
                    <p className="text-sm font-semibold text-emerald-700 dark:text-emerald-300">Suelta tu imagen aquí</p>
                </motion.div>
            )}
        </AnimatePresence>
    )
}

export function ImageFileInput({ inputRef, onFiles }) {
    return (
        <input
            ref={inputRef}
            type="file"
            accept="image/*"
            multiple
            className="hidden"
            onChange={e => { if (e.target.files.length) onFiles(e.target.files); e.target.value = '' }}
        />
    )
}

export function ImageThumbnails({ images, onRemove, onAddClick, isFull }) {
    if (images.length === 0) return null
    return (
        <div className="flex items-center gap-2 flex-wrap">
            {images.map((img, i) => (
                <div key={img.url} className="relative w-16 h-16 rounded-lg overflow-hidden border border-border group">
                    <img src={img.url} alt="" className="w-full h-full object-cover" />
                    <button
                        type="button"
                        onClick={() => onRemove(i)}
                        className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center"
                    >
                        <X className="w-4 h-4 text-white" />
                    </button>
                </div>
            ))}
            {!isFull && (
                <button
                    type="button"
                    onClick={onAddClick}
                    className="w-16 h-16 rounded-lg border-2 border-dashed border-border flex items-center justify-center text-muted-foreground hover:border-emerald-500/50 hover:text-emerald-500 transition-colors"
                >
                    <Paperclip className="w-4 h-4" />
                </button>
            )}
        </div>
    )
}

// Clicking a thumbnail opens a lightbox with the full, uncropped image —
// the thumbnail itself uses object-cover to fill its square, which crops
// the source image, so a raw "open in new tab" isn't enough on its own.
export function AttachmentThumbs({ attachments }) {
    const [lightbox, setLightbox] = useState(null)

    if (!attachments?.length) return null

    return (
        <>
            <div className="flex gap-2 flex-wrap mt-2">
                {attachments.map(a => (
                    <button
                        key={a.id}
                        type="button"
                        onClick={() => setLightbox(a.image)}
                        className="relative w-20 h-20 rounded-lg overflow-hidden border border-border group"
                    >
                        <img src={a.image} alt="Adjunto" className="w-full h-full object-cover" />
                        <span className="absolute inset-0 bg-black/0 group-hover:bg-black/40 transition-colors flex items-center justify-center">
                            <Maximize2 className="w-4 h-4 text-white opacity-0 group-hover:opacity-100 transition-opacity" />
                        </span>
                    </button>
                ))}
            </div>

            <Dialog open={!!lightbox} onOpenChange={(v) => !v && setLightbox(null)}>
                <DialogContent className="max-w-3xl p-2 bg-transparent border-none shadow-none">
                    <DialogTitle className="sr-only">Captura adjunta</DialogTitle>
                    <DialogDescription className="sr-only">Vista ampliada de la imagen adjunta</DialogDescription>
                    {lightbox && (
                        <img src={lightbox} alt="Adjunto" className="w-full max-h-[80vh] object-contain rounded-lg" />
                    )}
                </DialogContent>
            </Dialog>
        </>
    )
}
