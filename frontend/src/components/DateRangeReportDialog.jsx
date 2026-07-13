import { useState, useMemo } from 'react'
import { Download, Loader2, CalendarRange, FileSpreadsheet, FileText, Calendar } from 'lucide-react'
import { toast } from 'sonner'
import api from '../lib/api'
import {
    Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import {
    Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select'
import { Label } from '@/components/ui/label'

const MONTHS_ES = [
    'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
]

const PRESETS = [
    { value: '7d',              label: 'Últimos 7 días' },
    { value: '30d',             label: 'Últimos 30 días' },
    { value: 'this_month',      label: 'Mes actual' },
    { value: 'specific_month',  label: 'Mes específico' },
    { value: 'custom',          label: 'Personalizado' },
]

function fmt(d) {
    const y = d.getFullYear()
    const m = String(d.getMonth() + 1).padStart(2, '0')
    const day = String(d.getDate()).padStart(2, '0')
    return `${y}-${m}-${day}`
}

function rangeForPreset(preset, monthValue) {
    const today = new Date()
    today.setHours(23, 59, 59, 999)
    if (preset === '7d') {
        const start = new Date(); start.setDate(start.getDate() - 6); start.setHours(0, 0, 0, 0)
        return { start: fmt(start), end: fmt(today) }
    }
    if (preset === '30d') {
        const start = new Date(); start.setDate(start.getDate() - 29); start.setHours(0, 0, 0, 0)
        return { start: fmt(start), end: fmt(today) }
    }
    if (preset === 'this_month') {
        const start = new Date(today.getFullYear(), today.getMonth(), 1)
        return { start: fmt(start), end: fmt(today) }
    }
    if (preset === 'specific_month' && monthValue) {
        const [y, m] = monthValue.split('-').map(Number)
        const start = new Date(y, m - 1, 1)
        const end = new Date(y, m, 0)
        return { start: fmt(start), end: fmt(end) }
    }
    return null
}

const dateInputClasses =
    'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50'

export default function DateRangeReportDialog({ open, onClose }) {
    const [preset, setPreset] = useState('30d')
    const [customStart, setCustomStart] = useState('')
    const [customEnd, setCustomEnd] = useState('')
    const [downloading, setDownloading] = useState(false)

    const currentYear = new Date().getFullYear()
    const years = useMemo(
        () => Array.from({ length: 6 }, (_, i) => currentYear - i),
        [currentYear]
    )
    const [selectedYear, setSelectedYear] = useState(String(currentYear))
    const [selectedMonth, setSelectedMonth] = useState(String(new Date().getMonth() + 1))

    const monthValue = useMemo(() => {
        if (!selectedYear || !selectedMonth) return ''
        return `${selectedYear}-${String(selectedMonth).padStart(2, '0')}`
    }, [selectedYear, selectedMonth])

    const range = useMemo(() => {
        if (preset === 'custom') {
            if (!customStart || !customEnd) return null
            if (customStart > customEnd) return null
            return { start: customStart, end: customEnd }
        }
        return rangeForPreset(preset, monthValue)
    }, [preset, monthValue, customStart, customEnd])

    const blocked = !range || downloading

    async function handleDownload(format, ext) {
        if (!range) {
            toast.error('Selecciona un rango de fechas válido.')
            return
        }
        setDownloading(true)
        try {
            const res = await api.get(
                `/reports/org/?start=${range.start}&end=${range.end}&format=${format}`,
                { responseType: 'blob' }
            )
            const ctype = res.headers['content-type'] || ''
            if (ctype.includes('application/json') || res.data.type === 'application/json') {
                const text = await res.data.text()
                try {
                    const parsed = JSON.parse(text)
                    if (parsed.detail) {
                        toast.error(parsed.detail)
                        return
                    }
                } catch { /* fall through to download */ }
            }
            const url = URL.createObjectURL(res.data)
            const a = document.createElement('a')
            a.href = url
            a.download = `reporte_org_${range.start}_${range.end}.${ext}`
            document.body.appendChild(a)
            a.click()
            document.body.removeChild(a)
            URL.revokeObjectURL(url)
            toast.success(`Reporte ${format.toUpperCase()} descargado.`)
        } catch (err) {
            if (err.response && err.response.data instanceof Blob) {
                const text = await err.response.data.text()
                try {
                    const parsed = JSON.parse(text)
                    toast.error(parsed.detail || 'Error al generar el reporte.')
                    return
                } catch { /* ignore */ }
            }
            toast.error(err.response?.data?.detail || 'Error al generar el reporte.')
        } finally {
            setDownloading(false)
        }
    }

    return (
        <Dialog open={open} onOpenChange={(v) => { if (!v) onClose() }}>
            <DialogContent className="sm:max-w-md">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                        <CalendarRange className="w-5 h-5 text-purple-500" />
                        Reporte por rango de fechas
                    </DialogTitle>
                    <DialogDescription>
                        Genera un reporte PDF o Excel con todos los escaneos
                        de tu organización en el período seleccionado.
                    </DialogDescription>
                </DialogHeader>

                <div className="space-y-4">
                    <div className="space-y-2">
                        <Label htmlFor="preset">Período</Label>
                        <Select value={preset} onValueChange={setPreset}>
                            <SelectTrigger id="preset">
                                <SelectValue placeholder="Elige un período" />
                            </SelectTrigger>
                            <SelectContent>
                                {PRESETS.map((p) => (
                                    <SelectItem key={p.value} value={p.value}>
                                        {p.label}
                                    </SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                    </div>

                    {preset === 'specific_month' && (
                        <div className="space-y-2">
                            <Label>Mes</Label>
                            <div className="relative flex items-center rounded-md border border-input bg-background focus-within:ring-2 focus-within:ring-ring focus-within:ring-offset-2">
                                <Select value={selectedMonth} onValueChange={setSelectedMonth}>
                                    <SelectTrigger
                                        className="flex-1 border-0 bg-transparent shadow-none focus:ring-0 focus:ring-offset-0 rounded-r-none"
                                        aria-label="Mes"
                                    >
                                        <SelectValue placeholder="Mes" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {MONTHS_ES.map((label, idx) => {
                                            const val = String(idx + 1)
                                            return (
                                                <SelectItem key={val} value={val}>
                                                    {label}
                                                </SelectItem>
                                            )
                                        })}
                                    </SelectContent>
                                </Select>
                                <div className="h-6 w-px bg-border" />
                                <Select value={selectedYear} onValueChange={setSelectedYear}>
                                    <SelectTrigger
                                        className="w-[7.5rem] border-0 bg-transparent shadow-none focus:ring-0 focus:ring-offset-0 rounded-l-none"
                                        aria-label="Año"
                                    >
                                        <SelectValue placeholder="Año" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {years.map((y) => (
                                            <SelectItem key={y} value={String(y)}>
                                                {y}
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                                <Calendar className="w-4 h-4 text-muted-foreground absolute right-3 pointer-events-none" />
                            </div>
                        </div>
                    )}

                    {preset === 'custom' && (
                        <div className="grid grid-cols-2 gap-3">
                            <div className="space-y-2">
                                <Label htmlFor="start">Fecha inicio</Label>
                                <div className="relative">
                                    <input
                                        id="start"
                                        type="date"
                                        value={customStart}
                                        onChange={(e) => setCustomStart(e.target.value)}
                                        className={dateInputClasses + ' pr-9'}
                                    />
                                    <Calendar className="w-4 h-4 text-muted-foreground absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
                                </div>
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="end">Fecha fin</Label>
                                <div className="relative">
                                    <input
                                        id="end"
                                        type="date"
                                        value={customEnd}
                                        onChange={(e) => setCustomEnd(e.target.value)}
                                        className={dateInputClasses + ' pr-9'}
                                    />
                                    <Calendar className="w-4 h-4 text-muted-foreground absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
                                </div>
                            </div>
                        </div>
                    )}

                    {range && (
                        <div className="rounded-md border border-border bg-muted/40 p-3 text-sm">
                            <p className="text-muted-foreground">Rango seleccionado</p>
                            <p className="font-medium mt-0.5 text-foreground">
                                {range.start} → {range.end}
                            </p>
                        </div>
                    )}

                    {preset === 'custom' && customStart && customEnd && customStart > customEnd && (
                        <p className="text-sm text-destructive">
                            La fecha de inicio no puede ser mayor que la fecha de fin.
                        </p>
                    )}
                </div>

                <DialogFooter className="gap-2 sm:gap-2">
                    <Button
                        variant="outline"
                        className="gap-2"
                        disabled={blocked}
                        onClick={() => handleDownload('excel', 'xlsx')}
                    >
                        {downloading
                            ? <Loader2 className="w-4 h-4 animate-spin" />
                            : <FileSpreadsheet className="w-4 h-4" />}
                        Excel
                    </Button>
                    <Button
                        className="gap-2 bg-red-600 hover:bg-red-700 text-white"
                        disabled={blocked}
                        onClick={() => handleDownload('pdf', 'pdf')}
                    >
                        {downloading
                            ? <Loader2 className="w-4 h-4 animate-spin" />
                            : <FileText className="w-4 h-4" />}
                        PDF
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    )
}