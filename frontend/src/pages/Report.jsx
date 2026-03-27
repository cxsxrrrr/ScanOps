import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import api from '../lib/api'
import { formatDate, getSeverityColor, getSeverityLabel, getStatusColor, getStatusLabel } from '../lib/utils'
import {
    FileText, Download, ArrowLeft, Loader2, ShieldAlert,
    ShieldCheck, BarChart3, AlertTriangle, Info, Shield,
} from 'lucide-react'

export default function Report() {
    const { scanId } = useParams()
    const [report, setReport] = useState(null)
    const [loading, setLoading] = useState(true)
    const [activeTab, setActiveTab] = useState('technical')
    const [downloading, setDownloading] = useState(false)

    useEffect(() => { loadReport() }, [scanId])

    async function loadReport() {
        try {
            const res = await api.get(`/reports/${scanId}/`)
            setReport(res.data)
        } catch (err) {
            console.error('Failed to load report:', err)
            const detail = err?.response?.data?.detail
            if (detail) alert(detail)
        } finally {
            setLoading(false)
        }
    }

    async function handleDownload(format, extension = format) {
        setDownloading(true)
        try {
            const res = await api.get(`/reports/${scanId}/?download=1&format=${format}`, {
                responseType: 'blob',
            })
            const url = window.URL.createObjectURL(new Blob([res.data]))
            const link = document.createElement('a')
            link.href = url
            link.setAttribute('download', `reporte_scan_${scanId}.${extension}`)
            document.body.appendChild(link)
            link.click()
            link.remove()
            window.URL.revokeObjectURL(url)
        } catch (err) {
            const detail = err?.response?.data?.detail
            alert(detail || 'Error al descargar el reporte.')
        } finally {
            setDownloading(false)
        }
    }

    if (loading) {
        return (
            <div className="flex items-center justify-center py-20">
                <Loader2 className="w-8 h-8 animate-spin text-blue-400" />
            </div>
        )
    }

    if (!report) {
        return (
            <div className="text-center py-20 text-muted-foreground">
                <ShieldAlert className="w-12 h-12 mx-auto mb-3 opacity-30" />
                <p>Reporte no encontrado.</p>
                <Link to="/scans" className="text-blue-400 hover:text-blue-300 text-sm mt-2 inline-block">
                    ← Volver a escaneos
                </Link>
            </div>
        )
    }

    const severityIcon = (severity) => {
        switch (severity) {
            case 'CRITICAL': return <AlertTriangle className="w-4 h-4 text-fuchsia-400" />
            case 'HIGH': return <AlertTriangle className="w-4 h-4 text-red-400" />
            case 'MEDIUM': return <ShieldAlert className="w-4 h-4 text-amber-400" />
            case 'LOW': return <Shield className="w-4 h-4 text-blue-400" />
            default: return <Info className="w-4 h-4 text-gray-400" />
        }
    }

    return (
        <div className="space-y-6 animate-fade-in max-w-5xl mx-auto">
            {/* Header */}
            <div className="flex items-center justify-between flex-wrap gap-4">
                <div>
                    <Link
                        to="/scans"
                        className="text-sm text-muted-foreground hover:text-foreground flex items-center gap-1 mb-2"
                    >
                        <ArrowLeft className="w-3 h-3" /> Volver a escaneos
                    </Link>
                    <h1 className="text-2xl font-bold flex items-center gap-2">
                        <FileText className="w-6 h-6 text-blue-400" />
                        Reporte de Auditoría
                    </h1>
                    <p className="text-sm text-muted-foreground mt-1">{report.url}</p>
                </div>
                <div className="flex gap-2">
                    <button
                        onClick={() => handleDownload('excel', 'xlsx')}
                        disabled={downloading}
                        className="px-4 py-2 rounded-lg glass hover:bg-white/10 transition-colors text-sm font-medium flex items-center gap-2"
                    >
                        <Download className="w-4 h-4" /> Excel
                    </button>
                    <button
                        onClick={() => handleDownload('pdf')}
                        disabled={downloading}
                        className="px-4 py-2 rounded-lg gradient-primary text-white text-sm font-medium flex items-center gap-2 hover:opacity-90"
                    >
                        <Download className="w-4 h-4" /> PDF
                    </button>
                </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
                {[
                    { label: 'Total', value: report.stats.total, color: 'text-foreground' },
                    { label: 'Crítico', value: report.stats.critical || 0, color: 'text-fuchsia-400' },
                    { label: 'Alto', value: report.stats.high, color: 'text-red-400' },
                    { label: 'Medio', value: report.stats.medium, color: 'text-amber-400' },
                    { label: 'Bajo', value: report.stats.low, color: 'text-blue-400' },
                ].map((s) => (
                    <div key={s.label} className="glass rounded-xl p-4 text-center">
                        <div className={`text-2xl font-bold ${s.color}`}>{s.value}</div>
                        <div className="text-xs text-muted-foreground mt-1">{s.label}</div>
                    </div>
                ))}
            </div>

            {/* Tabs */}
            <div className="flex gap-1 glass rounded-xl p-1">
                <button
                    onClick={() => setActiveTab('technical')}
                    className={`flex-1 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors
            ${activeTab === 'technical' ? 'gradient-primary text-white' : 'hover:bg-white/5'}`}
                >
                    🔍 Reporte Técnico
                </button>
                <button
                    onClick={() => setActiveTab('executive')}
                    className={`flex-1 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors
            ${activeTab === 'executive' ? 'gradient-primary text-white' : 'hover:bg-white/5'}`}
                >
                    📋 Resumen Ejecutivo
                </button>
            </div>

            {/* Tab content */}
            {activeTab === 'technical' ? (
                <div className="space-y-3">
                    {report.findings.length === 0 ? (
                        <div className="glass rounded-xl p-8 text-center">
                            <ShieldCheck className="w-12 h-12 mx-auto mb-3 text-emerald-400" />
                            <p className="font-medium text-emerald-400">¡Sin hallazgos!</p>
                            <p className="text-sm text-muted-foreground mt-1">
                                No se encontraron vulnerabilidades en este escaneo.
                            </p>
                        </div>
                    ) : (
                        report.findings.map((finding) => (
                            <div
                                key={finding.id}
                                className="glass rounded-xl p-5 border-l-4 hover:bg-white/5 transition-colors"
                                style={{
                                    borderLeftColor:
                                        finding.severity === 'CRITICAL' ? '#d946ef' :
                                            finding.severity === 'HIGH' ? '#ef4444' :
                                                finding.severity === 'MEDIUM' ? '#f59e0b' :
                                                    finding.severity === 'LOW' ? '#3b82f6' : '#6b7280',
                                }}
                            >
                                <div className="flex items-start justify-between gap-3">
                                    <div className="flex items-center gap-2">
                                        {severityIcon(finding.severity)}
                                        <h3 className="font-semibold">{finding.title}</h3>
                                    </div>
                                    <span className={`${getSeverityColor(finding.severity)} px-2.5 py-0.5 rounded-full text-xs font-medium flex-shrink-0`}>
                                        {getSeverityLabel(finding.severity)}
                                    </span>
                                </div>
                                <p className="text-sm text-muted-foreground mt-2">{finding.description}</p>
                                {finding.recommendation && (
                                    <div className="mt-3 p-3 rounded-lg bg-blue-500/5 border border-blue-500/10">
                                        <p className="text-sm text-blue-300">
                                            <strong>Recomendación:</strong> {finding.recommendation}
                                        </p>
                                    </div>
                                )}
                                {finding.evidence && (
                                    <div className="mt-2 p-2 rounded bg-white/5 text-xs font-mono text-muted-foreground">
                                        {finding.evidence}
                                    </div>
                                )}
                            </div>
                        ))
                    )}
                </div>
            ) : (
                <div className="glass rounded-xl p-6">
                    {report.executive_summary ? (
                        <div
                            className="prose prose-invert prose-sm max-w-none"
                            dangerouslySetInnerHTML={{
                                __html: report.executive_summary.content
                                    .replace(/\n/g, '<br>')
                                    .replace(/## /g, '<h2 class="text-lg font-bold mt-4 mb-2">')
                                    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                            }}
                        />
                    ) : (
                        <div className="text-center py-8 text-muted-foreground">
                            <BarChart3 className="w-12 h-12 mx-auto mb-3 opacity-30" />
                            <p>Resumen ejecutivo en generación...</p>
                            <p className="text-sm mt-1">La IA está procesando los resultados.</p>
                        </div>
                    )}
                </div>
            )}

            {/* Metadata */}
            <div className="glass rounded-xl p-4 text-xs text-muted-foreground flex flex-wrap gap-4">
                <span>Scan ID: #{report.scan_id}</span>
                <span>Estado: {getStatusLabel(report.scan_status)}</span>
                <span>Fecha: {formatDate(report.scan_date)}</span>
                {report.executive_summary && (
                    <span>IA: {report.executive_summary.ai_provider} ({report.executive_summary.token_usage} tokens)</span>
                )}
            </div>
        </div>
    )
}
