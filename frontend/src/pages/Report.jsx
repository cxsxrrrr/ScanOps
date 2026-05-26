import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { toast } from 'sonner'
import api from '../lib/api'
import { formatDate, getSeverityColor, getSeverityLabel, getStatusColor, getStatusLabel } from '../lib/utils'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Separator } from '@/components/ui/separator'
import {
    FileText, Download, ArrowLeft, Loader2, ShieldAlert,
    ShieldCheck, BarChart3, AlertTriangle, Info, Shield,
    ClipboardList, ScanSearch, Filter,
} from 'lucide-react'

// Beautifully renders AI markdown into highly structured premium elements
function renderMarkdown(content) {
    let inList = false;
    const listItems = [];
    const elements = [];

    const lines = content.split('\n');
    
    lines.forEach((line, i) => {
        const trimmed = line.trim();
        
        // Handle list completion
        if (inList && !trimmed.startsWith('-') && !trimmed.startsWith('*') && !/^\d+\./.test(trimmed)) {
            inList = false;
            elements.push(
                <ul key={`list-${i}`} className="list-disc pl-5 space-y-1.5 my-3 text-muted-foreground">
                    {[...listItems]}
                </ul>
            );
            listItems.length = 0;
        }

        // Horizontal dividers
        if (trimmed === '---') {
            elements.push(<Separator key={`sep-${i}`} className="my-5 opacity-60" />);
            return;
        }

        // Headers
        if (trimmed.startsWith('# ')) {
            elements.push(<h1 key={i} className="text-xl font-extrabold tracking-tight mt-6 mb-3 text-foreground border-b pb-1">{trimmed.slice(2)}</h1>);
            return;
        }
        if (trimmed.startsWith('## ')) {
            elements.push(<h2 key={i} className="text-lg font-bold tracking-tight mt-5 mb-2 text-foreground">{trimmed.slice(3)}</h2>);
            return;
        }
        if (trimmed.startsWith('### ')) {
            elements.push(<h3 key={i} className="text-sm font-semibold tracking-tight mt-4 mb-1.5 text-blue-500 uppercase">{trimmed.slice(4)}</h3>);
            return;
        }

        // Bullet lists
        if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
            inList = true;
            const textContent = trimmed.slice(2);
            listItems.push(<li key={`li-${i}`} className="text-sm leading-relaxed">{parseInlineMarkdown(textContent)}</li>);
            return;
        }

        // Numbered lists
        const numListMatch = trimmed.match(/^(\d+)\.\s+(.*)/);
        if (numListMatch) {
            inList = true;
            const textContent = numListMatch[2];
            listItems.push(
                <li key={`li-${i}`} className="text-sm leading-relaxed list-decimal ml-1">
                    {parseInlineMarkdown(textContent)}
                </li>
            );
            return;
        }

        if (!trimmed) {
            elements.push(<div key={`br-${i}`} className="h-2" />);
            return;
        }

        // Normal paragraph
        elements.push(
            <p key={i} className="text-sm leading-relaxed text-muted-foreground mb-3">
                {parseInlineMarkdown(trimmed)}
            </p>
        );
    });

    // Push any remaining list
    if (inList && listItems.length > 0) {
        elements.push(
            <ul key="list-final" className="list-disc pl-5 space-y-1.5 my-3 text-muted-foreground">
                {listItems}
            </ul>
        );
    }

    return elements;
}

// Sub-helper to parse inline formatting (like bold **text**)
function parseInlineMarkdown(text) {
    const parts = text.split(/(\*\*[^*]+\*\*)/);
    return parts.map((part, j) => {
        if (part.startsWith('**') && part.endsWith('**')) {
            const boldText = part.slice(2, -2);
            // Highlight specific metrics elegantly
            if (boldText.toLowerCase().includes('alto') || boldText.toLowerCase().includes('alta') || boldText.toLowerCase().includes('crítico') || boldText.toLowerCase().includes('critica') || boldText.toLowerCase().includes('riesgo') || boldText.toLowerCase().includes('grave') || boldText.toLowerCase().includes('severo')) {
                return <span key={j} className="px-1.5 py-0.5 rounded text-xs font-bold bg-red-500/10 text-red-500 dark:text-red-400 border border-red-500/10">{boldText}</span>;
            }
            if (boldText.toLowerCase().includes('medio') || boldText.toLowerCase().includes('media') || boldText.toLowerCase().includes('moderado') || boldText.toLowerCase().includes('moderada')) {
                return <span key={j} className="px-1.5 py-0.5 rounded text-xs font-bold bg-amber-500/10 text-amber-500 dark:text-amber-400 border border-amber-500/10">{boldText}</span>;
            }
            if (boldText.toLowerCase().includes('bajo') || boldText.toLowerCase().includes('baja') || boldText.toLowerCase().includes('seguro') || boldText.toLowerCase().includes('leve')) {
                return <span key={j} className="px-1.5 py-0.5 rounded text-xs font-bold bg-blue-500/10 text-blue-500 dark:text-blue-400 border border-blue-500/10">{boldText}</span>;
            }
            return <strong key={j} className="text-foreground font-semibold">{boldText}</strong>;
        }
        return part;
    });
}

const SEVERITY_COLORS = {
    CRITICAL: { border: '#d946ef', icon: <AlertTriangle className="w-4 h-4 text-fuchsia-500" /> },
    HIGH:     { border: '#ef4444', icon: <AlertTriangle className="w-4 h-4 text-red-500" /> },
    MEDIUM:   { border: '#f59e0b', icon: <ShieldAlert className="w-4 h-4 text-amber-500" /> },
    LOW:      { border: '#3b82f6', icon: <Shield className="w-4 h-4 text-blue-500" /> },
    default:  { border: '#6b7280', icon: <Info className="w-4 h-4 text-slate-400" /> },
}

const SEVERITY_FILTERS = [
    { key: 'all',      label: 'Todos',   color: '' },
    { key: 'CRITICAL', label: 'Critico',  color: 'text-fuchsia-500' },
    { key: 'HIGH',     label: 'Alto',     color: 'text-red-500' },
    { key: 'MEDIUM',   label: 'Medio',    color: 'text-amber-500' },
    { key: 'LOW',      label: 'Bajo',     color: 'text-blue-500' },
]

const SECTION_STYLES = [
    { keys: ['vision','general','overview','resumen','alcance','scope','introduc','contexto'], icon: <ScanSearch className="w-4 h-4" />, color: '#3b82f6', bg: 'from-blue-500/10 to-transparent' },
    { keys: ['hallazgo','finding','vulnerab','debilidad','weakness','problema','fallo','error','detect'], icon: <AlertTriangle className="w-4 h-4" />, color: '#ef4444', bg: 'from-red-500/10 to-transparent' },
    { keys: ['riesgo','risk','amenaza','threat','criticidad','severidad','peligro','critico'], icon: <ShieldAlert className="w-4 h-4" />, color: '#f59e0b', bg: 'from-amber-500/10 to-transparent' },
    { keys: ['recomendac','recommend','mitigacion','mitigation','solucion','correcc','mejora','medida','parche','accion'], icon: <ShieldCheck className="w-4 h-4" />, color: '#10b981', bg: 'from-emerald-500/10 to-transparent' },
    { keys: ['plan','proximo','next','paso','cronograma','hoja de ruta','roadmap','prioridad'], icon: <ClipboardList className="w-4 h-4" />, color: '#8b5cf6', bg: 'from-purple-500/10 to-transparent' },
    { keys: ['conclus','summary','cierre','final','consideracion'], icon: <BarChart3 className="w-4 h-4" />, color: '#06b6d4', bg: 'from-cyan-500/10 to-transparent' },
    { keys: ['tecnic','technical','detalle','detail','analisis','metodologia'], icon: <FileText className="w-4 h-4" />, color: '#6366f1', bg: 'from-indigo-500/10 to-transparent' },
    { keys: ['impacto','impact','negocio','business','consecuencia','afecta'], icon: <AlertTriangle className="w-4 h-4" />, color: '#ec4899', bg: 'from-pink-500/10 to-transparent' },
    { keys: ['cumplim','compliance','norma','standard','regulac','legal','ley','normativ'], icon: <Shield className="w-4 h-4" />, color: '#14b8a6', bg: 'from-teal-500/10 to-transparent' },
    { keys: ['estadistic','stat','metrica','dato','numero','cifra'], icon: <BarChart3 className="w-4 h-4" />, color: '#8b5cf6', bg: 'from-violet-500/10 to-transparent' },
]

function getSectionStyle(title) {
    const lower = title.toLowerCase()
    for (const s of SECTION_STYLES) {
        if (s.keys.some(k => lower.includes(k))) return s
    }
    return { icon: <Info className="w-4 h-4" />, color: '#6b7280', bg: 'from-slate-500/10 to-transparent' }
}

function parseExecutiveSections(content) {
    const lines = content.split('\n')
    const sections = []
    let currentTitle = null
    let currentLines = []

    function flush() {
        const text = currentLines.join('\n').trim()
        if (text) sections.push({ title: currentTitle || 'Resumen General', content: text })
        currentLines = []
    }

    for (const line of lines) {
        const t = line.trim()
        if (t.startsWith('## ')) { flush(); currentTitle = t.slice(3) }
        else { currentLines.push(line) }
    }
    flush()
    if (!sections.length) sections.push({ title: 'Resumen General', content })
    return sections
}

function isTableStart(lines, idx) {
    const line = lines[idx]?.trim()
    if (!line?.startsWith('|')) return false
    const next = lines[idx + 1]?.trim()
    if (!next?.startsWith('|')) return false
    return next.split('|').filter(Boolean).every(c => /^:?-{3,}:?$/.test(c.trim()))
}

function parseTable(lines, startIdx) {
    const headers = lines[startIdx].trim().split('|').map(s => s.trim()).filter(Boolean)
    const rows = []
    let i = startIdx + 2
    while (i < lines.length && lines[i]?.trim()?.startsWith('|')) {
        rows.push(lines[i].trim().split('|').map(s => s.trim()).filter(Boolean))
        i++
    }
    return { headers, rows, end: i }
}

function renderTableElement({ headers, rows }) {
    return (
        <div className="my-3 overflow-x-auto rounded-lg border border-border/60 bg-card/50">
            <table className="w-full text-sm">
                <thead>
                    <tr className="bg-muted/50">
                        {headers.map((h, hi) => (
                            <th key={hi} className="px-4 py-2.5 text-left font-semibold text-foreground/80 border-b border-border/40 text-[11px] uppercase tracking-wider">{h}</th>
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {rows.map((row, ri) => (
                        <tr key={ri} className="border-b border-border/20 last:border-0 hover:bg-muted/30 transition-colors">
                            {row.map((cell, ci) => (
                                <td key={ci} className="px-4 py-2.5 text-muted-foreground">{parseInlineMarkdown(cell)}</td>
                            ))}
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    )
}

function renderContentWithTables(content) {
    if (!content) return null
    const lines = content.split('\n')
    const el = []
    let i = 0

    while (i < lines.length) {
        const t = lines[i].trim()

        if (isTableStart(lines, i)) {
            const table = parseTable(lines, i)
            el.push(<div key={`tbl-${i}`}>{renderTableElement(table)}</div>)
            i = table.end
            continue
        }

        if (!t) { i++; continue }

        if (t === '---' || t === '***') {
            el.push(<Separator key={`hr-${i}`} className="my-3 opacity-50" />)
            i++; continue
        }

        if (t.startsWith('### ')) {
            el.push(<h4 key={`h3-${i}`} className="text-sm font-bold text-blue-600 dark:text-blue-400 mt-3 mb-1.5">{t.slice(4)}</h4>)
            i++; continue
        }

        if (t.startsWith('#### ')) {
            el.push(<h5 key={`h4-${i}`} className="text-xs font-semibold text-muted-foreground mt-2 mb-1 uppercase tracking-wider">{t.slice(5)}</h5>)
            i++; continue
        }

        if (t.startsWith('> ')) {
            const q = []
            while (i < lines.length && lines[i]?.trim()?.startsWith('> ')) {
                q.push(lines[i].trim().slice(2))
                i++
            }
            el.push(
                <blockquote key={`bq-${i}`} className="border-l-[3px] border-blue-500/40 pl-4 my-3 italic text-muted-foreground text-sm">{q.join(' ')}</blockquote>
            )
            continue
        }

        if (t.startsWith('- ') || t.startsWith('* ')) {
            const items = []
            while (i < lines.length && (lines[i]?.trim()?.startsWith('- ') || lines[i]?.trim()?.startsWith('* '))) {
                items.push(<li key={`li-${i}`} className="text-sm leading-relaxed text-muted-foreground">{parseInlineMarkdown(lines[i].trim().slice(2))}</li>)
                i++
            }
            el.push(<ul key={`ul-${i}`} className="list-disc pl-5 space-y-1 my-2">{items}</ul>)
            continue
        }

        if (/^\d+\.\s+/.test(t)) {
            const items = []
            while (i < lines.length && /^\d+\.\s+/.test(lines[i]?.trim())) {
                const m = lines[i].trim().match(/^\d+\.\s+(.*)/)
                items.push(<li key={`oli-${i}`} className="text-sm leading-relaxed text-muted-foreground">{parseInlineMarkdown(m[1])}</li>)
                i++
            }
            el.push(<ol key={`ol-${i}`} className="list-decimal pl-5 space-y-1 my-2">{items}</ol>)
            continue
        }

        el.push(<p key={`p-${i}`} className="text-sm leading-relaxed text-muted-foreground mb-2">{parseInlineMarkdown(t)}</p>)
        i++
    }

    return <div className="space-y-0.5">{el}</div>
}

export default function Report() {
    const { scanId } = useParams()
    const [report,        setReport]        = useState(null)
    const [loading,       setLoading]       = useState(true)
    const [loadError,     setLoadError]     = useState(null)
    const [downloading,   setDownloading]   = useState(false)
    const [severityFilter, setSeverityFilter] = useState('all')
    const filteredFindings = severityFilter === 'all' ? (report?.findings || []) : (report?.findings || []).filter(f => f.severity === severityFilter)

    useEffect(() => {
        const controller = new AbortController()
        loadReport(controller.signal)
        return () => controller.abort()
    }, [scanId])

    async function loadReport(signal) {
        setLoadError(null)
        try {
            const res = await api.get(`/reports/${scanId}/`, { signal })
            setReport(res.data)
        } catch (err) {
            if (err.code === 'ERR_CANCELED') return
            const detail = err?.response?.data?.detail
            setLoadError(detail || 'No se pudo cargar el reporte.')
        } finally {
            setLoading(false)
        }
    }

    async function handleDownload(format, extension = format) {
        setDownloading(true)
        try {
            const res = await api.get(`/reports/${scanId}/?download=1&format=${format}`, { responseType: 'blob' })
            const url  = window.URL.createObjectURL(new Blob([res.data]))
            const link = document.createElement('a')
            link.href  = url
            link.setAttribute('download', `reporte_scan_${scanId}.${extension}`)
            document.body.appendChild(link)
            link.click()
            link.remove()
            window.URL.revokeObjectURL(url)
            toast.success(`Reporte ${format.toUpperCase()} descargado.`)
        } catch (err) {
            let detail = `Error al descargar el reporte ${format.toUpperCase()}.`
            try {
                const blob = err?.response?.data
                if (blob instanceof Blob && blob.type !== 'application/pdf' && blob.type !== 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet') {
                    const text = await blob.text()
                    const parsed = JSON.parse(text)
                    detail = parsed?.detail || detail
                }
            } catch (_) { /* use default error message */ }
            toast.error(detail)
        } finally {
            setDownloading(false)
        }
    }

    if (loading) return (
        <div className="flex items-center justify-center py-24">
            <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
        </div>
    )

    if (!report) return (
        <div className="text-center py-24 text-muted-foreground">
            <ShieldAlert className="w-12 h-12 mx-auto mb-3 opacity-25" />
            <p className="font-medium">{loadError || 'Reporte no encontrado.'}</p>
            <Link to="/scans" className="text-blue-500 hover:text-blue-400 text-sm mt-3 inline-flex items-center gap-1">
                <ArrowLeft className="w-3 h-3" /> Volver a escaneos
            </Link>
        </div>
    )

    return (
        <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            className="space-y-5 max-w-5xl mx-auto"
        >
            {/* Header */}
            <div className="flex items-start justify-between flex-wrap gap-4">
                <div>
                    <Link to="/scans" className="text-xs text-muted-foreground hover:text-foreground flex items-center gap-1 mb-2 transition-colors">
                        <ArrowLeft className="w-3 h-3" /> Volver a escaneos
                    </Link>
                    <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
                        <FileText className="w-6 h-6 text-blue-500" /> Reporte de Auditoría
                    </h1>
                    <p className="text-sm text-muted-foreground mt-1 font-mono">{report.url}</p>
                </div>
                <div className="flex gap-2">
                    <Button variant="outline" className="gap-2" onClick={() => handleDownload('excel', 'xlsx')} disabled={downloading}>
                        <Download className="w-4 h-4" /> Excel
                    </Button>
                    <Button className="gap-2 bg-red-600 hover:bg-red-700 text-white" onClick={() => handleDownload('pdf', 'pdf')} disabled={downloading}>
                        <Download className="w-4 h-4" /> PDF
                    </Button>
                </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
                {[
                    { label: 'Total',    value: report.stats.total,          color: 'text-foreground' },
                    { label: 'Crítico',  value: report.stats.critical || 0,  color: 'text-fuchsia-500' },
                    { label: 'Alto',     value: report.stats.high,           color: 'text-red-500' },
                    { label: 'Medio',    value: report.stats.medium,         color: 'text-amber-500' },
                    { label: 'Bajo',     value: report.stats.low,            color: 'text-blue-500' },
                ].map((s, i) => (
                    <motion.div key={s.label} initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: i * 0.06 }}>
                        <Card>
                            <CardContent className="p-4 text-center">
                                <div className={`text-2xl font-bold tabular-nums ${s.color}`}>{s.value}</div>
                                <p className="text-xs text-muted-foreground mt-0.5">{s.label}</p>
                            </CardContent>
                        </Card>
                    </motion.div>
                ))}
            </div>

            {/* Tabs */}
            <Tabs defaultValue="technical">
                <TabsList className="w-full">
                    <TabsTrigger value="technical" className="flex-1 flex items-center justify-center gap-2">
                        <ScanSearch className="w-4 h-4" /> Reporte Técnico
                    </TabsTrigger>
                    <TabsTrigger value="executive" className="flex-1 flex items-center justify-center gap-2">
                        <ClipboardList className="w-4 h-4" /> Resumen Ejecutivo
                    </TabsTrigger>
                </TabsList>

                <TabsContent value="technical" className="mt-4 space-y-3">
                    {/* Severity filter bar */}
                    <div className="flex items-center gap-1.5 flex-wrap">
                        <Filter className="w-3.5 h-3.5 text-muted-foreground mr-0.5" />
                        {SEVERITY_FILTERS.map(({ key, label, color }) => (
                            <Button
                                key={key}
                                variant={severityFilter === key ? 'default' : 'outline'}
                                size="sm"
                                onClick={() => setSeverityFilter(key)}
                                className={`h-7 text-xs px-3 ${severityFilter === key ? '' : `text-muted-foreground ${color}`}`}
                            >
                                {label}
                                {key !== 'all' && filteredFindings.length > 0 && severityFilter === key && (
                                    <span className="ml-1.5 px-1.5 py-0.5 rounded-full bg-background/30 text-[10px] font-bold">{filteredFindings.length}</span>
                                )}
                            </Button>
                        ))}
                    </div>

                    {filteredFindings.length === 0 ? (
                        <Card>
                            <CardContent className="py-12 text-center">
                                <ShieldCheck className="w-12 h-12 mx-auto mb-3 text-emerald-500" />
                                <p className="font-semibold text-emerald-500">
                                    {severityFilter === 'all' ? '¡Sin hallazgos!' : 'Sin hallazgos de este nivel'}
                                </p>
                                <p className="text-sm text-muted-foreground mt-1">
                                    {severityFilter === 'all'
                                        ? 'No se encontraron vulnerabilidades.'
                                        : `No hay hallazgos de criticidad ${SEVERITY_FILTERS.find(f => f.key === severityFilter)?.label || severityFilter}.`}
                                </p>
                            </CardContent>
                        </Card>
                    ) : (
                        filteredFindings.map((finding, i) => {
                            const sev = SEVERITY_COLORS[finding.severity] || SEVERITY_COLORS.default
                            return (
                                <motion.div
                                    key={finding.id}
                                    initial={{ opacity: 0, x: -8 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    transition={{ delay: i * 0.05, duration: 0.25 }}
                                >
                                    <Card className="overflow-hidden" style={{ borderLeft: `3px solid ${sev.border}` }}>
                                        <CardContent className="p-5">
                                            <div className="flex items-start justify-between gap-3 mb-2">
                                                <div className="flex items-center gap-2">
                                                    {sev.icon}
                                                    <h3 className="font-semibold text-sm">{finding.title}</h3>
                                                </div>
                                                <Badge className={`${getSeverityColor(finding.severity)} text-xs flex-shrink-0`}>
                                                    {getSeverityLabel(finding.severity)}
                                                </Badge>
                                            </div>
                                            <p className="text-sm text-muted-foreground">{finding.description}</p>
                                            {finding.recommendation && (
                                                <div className="mt-3 p-3 rounded-lg bg-blue-500/5 border border-blue-500/15">
                                                    <p className="text-xs text-blue-600 dark:text-blue-400">
                                                        <strong>Recomendación:</strong> {finding.recommendation}
                                                    </p>
                                                </div>
                                            )}
                                            {finding.evidence && (
                                                <div className="mt-2 p-2 rounded-lg bg-muted text-xs font-mono text-muted-foreground">
                                                    {finding.evidence}
                                                </div>
                                            )}
                                        </CardContent>
                                    </Card>
                                </motion.div>
                            )
                        })
                    )}
                </TabsContent>

                <TabsContent value="executive" className="mt-4">
                    <Card className="border border-border/80 shadow-md overflow-hidden">
                        <div className="bg-gradient-to-r from-blue-500/10 via-purple-500/10 to-transparent p-6 border-b border-border/60">
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-md">
                                    <ClipboardList className="w-5 h-5 text-white" />
                                </div>
                                <div>
                                    <h3 className="font-extrabold text-base text-foreground tracking-tight">Analisis Estrategico e Informe Ejecutivo</h3>
                                    <p className="text-xs text-muted-foreground mt-0.5">Perspectiva general de seguridad y mitigacion generada por Inteligencia Artificial.</p>
                                </div>
                            </div>
                        </div>
                        <CardContent className="p-6 space-y-4">
                            {report.executive_summary ? (
                                <>
                                    {parseExecutiveSections(report.executive_summary.content).map((section, idx) => {
                                        const style = getSectionStyle(section.title)
                                        return (
                                            <motion.div
                                                key={`sec-${idx}`}
                                                initial={{ opacity: 0, y: 16 }}
                                                animate={{ opacity: 1, y: 0 }}
                                                transition={{ delay: idx * 0.08, duration: 0.3 }}
                                            >
                                                <Card
                                                    className="overflow-hidden border-l-[3px] transition-shadow hover:shadow-md"
                                                    style={{ borderLeftColor: style.color }}
                                                >
                                                    <div className="bg-gradient-to-r px-5 py-3 border-b border-border/40" style={{ backgroundImage: `linear-gradient(to right, ${style.color}15, transparent)` }}>
                                                        <div className="flex items-center gap-2.5">
                                                            <span style={{ color: style.color }}>{style.icon}</span>
                                                            <h4 className="font-bold text-sm text-foreground/90">{section.title}</h4>
                                                        </div>
                                                    </div>
                                                    <CardContent className="p-5">
                                                        {renderContentWithTables(section.content)}
                                                    </CardContent>
                                                </Card>
                                            </motion.div>
                                        )
                                    })}
                                </>
                            ) : (
                                <div className="text-center py-14 text-muted-foreground">
                                    <Loader2 className="w-10 h-10 mx-auto mb-4 animate-spin text-blue-500" />
                                    <p className="font-semibold text-foreground">Elaborando el resumen estrategico...</p>
                                    <p className="text-sm mt-1">Nuestra IA esta estructurando y analizando tus hallazgos.</p>
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </TabsContent>
            </Tabs>

            {/* Metadata */}
            <Card>
                <CardContent className="p-4">
                    <div className="flex flex-wrap gap-x-5 gap-y-1 text-xs text-muted-foreground">
                        <span>Scan ID: <span className="font-mono text-foreground">#{report.scan_id}</span></span>
                        <span>Estado: <span className={`font-medium ${getStatusColor(report.scan_status)}`}>{getStatusLabel(report.scan_status)}</span></span>
                        <span>Fecha: {formatDate(report.scan_date)}</span>
                        {report.executive_summary && (
                            <span>IA: {report.executive_summary.ai_provider} · {report.executive_summary.token_usage} tokens</span>
                        )}
                    </div>
                </CardContent>
            </Card>
        </motion.div>
    )
}
