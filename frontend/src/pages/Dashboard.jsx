import { useState, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import { useUser } from '@clerk/clerk-react'
import { motion } from 'framer-motion'
import {
    AreaChart, Area, ResponsiveContainer,
    Tooltip as ReTooltip, XAxis, YAxis, CartesianGrid,
} from 'recharts'
import api from '../lib/api'
import { getStatusLabel } from '../lib/utils'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Skeleton } from '@/components/ui/skeleton'
import { Button } from '@/components/ui/button'
import { useTheme } from '../hooks/useTheme'
import {
    Globe, ScanSearch, AlertTriangle, Shield,
    ArrowRight, Sparkles, ShieldCheck,
    Crown, Zap, CheckCircle2, XCircle, Clock, Loader2,
} from 'lucide-react'

// ─── Constants ───────────────────────────────────────────────────────────────

const planConfig = {
    free:     { icon: Shield, gradient: 'from-slate-500 to-slate-600', badge: 'plan-badge-free',     limit: 1  },
    pro:      { icon: Zap,    gradient: 'from-purple-500 to-purple-600', badge: 'plan-badge-pro',    limit: 5  },
    ultimate: { icon: Crown,  gradient: 'from-amber-500 to-orange-500', badge: 'plan-badge-ultimate', limit: 10 },
}

// ─── Hooks ───────────────────────────────────────────────────────────────────

function useCountUp(target, duration = 1200) {
    const [value, setValue] = useState(0)
    const rafRef = useRef(null)

    useEffect(() => {
        if (!target) { setValue(0); return }
        const start = Date.now()
        const step = () => {
            const t = Math.min((Date.now() - start) / duration, 1)
            setValue(Math.round(target * (1 - (1 - t) ** 3)))
            if (t < 1) rafRef.current = requestAnimationFrame(step)
        }
        rafRef.current = requestAnimationFrame(step)
        return () => cancelAnimationFrame(rafRef.current)
    }, [target, duration])

    return value
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

function buildActivityData(scans) {
    const map = {}
    for (let i = 6; i >= 0; i--) {
        const d = new Date()
        d.setDate(d.getDate() - i)
        const iso = d.toISOString().split('T')[0]
        map[iso] = {
            date: d.toLocaleDateString('es', { weekday: 'short' }),
            scans: 0,
            findings: 0,
        }
    }
    scans.forEach(s => {
        if (!s.started_at) return
        const iso = s.started_at.split('T')[0]
        if (map[iso]) {
            map[iso].scans++
            map[iso].findings += (s.critical_count || 0) + (s.high_count || 0)
        }
    })
    return Object.values(map)
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function StatusIcon({ status }) {
    const cls = 'w-4 h-4 flex-shrink-0'
    if (status === 'completed') return <CheckCircle2 className={`${cls} text-emerald-500`} />
    if (status === 'running')   return <Loader2 className={`${cls} text-blue-500 animate-spin`} />
    if (status === 'error')     return <XCircle className={`${cls} text-red-500`} />
    return <Clock className={`${cls} text-amber-500`} />
}

function SecurityGauge({ score }) {
    const r    = 52
    const circ = 2 * Math.PI * r
    const offset = circ - (score / 100) * circ
    const color  = score >= 80 ? '#10b981' : score >= 60 ? '#f59e0b' : '#ef4444'
    const label  = score >= 80 ? 'Seguro' : score >= 60 ? 'Moderado' : 'En riesgo'

    return (
        <div className="flex flex-col items-center gap-2">
            <div className="relative">
                <svg width="128" height="128" viewBox="0 0 128 128" className="-rotate-90">
                    <circle cx="64" cy="64" r={r} fill="none" strokeWidth="9" className="stroke-muted/30" />
                    <circle
                        cx="64" cy="64" r={r} fill="none" strokeWidth="9"
                        stroke={color} strokeLinecap="round"
                        strokeDasharray={circ}
                        strokeDashoffset={offset}
                        style={{ filter: `drop-shadow(0 0 7px ${color}90)` }}
                    />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <span className="text-3xl font-black tabular-nums leading-none" style={{ color }}>{score}</span>
                    <span className="text-[11px] text-muted-foreground">/100</span>
                </div>
            </div>
            <div className="text-center">
                <p className="text-sm font-bold" style={{ color }}>{label}</p>
                <p className="text-xs text-muted-foreground">Puntuación de seguridad</p>
            </div>
        </div>
    )
}

// ─── Main component ───────────────────────────────────────────────────────────

export default function Dashboard() {
    const { user } = useUser()
    const { isDark } = useTheme()
    const [allScans, setAllScans] = useState([])
    const [orgData,  setOrgData]  = useState(null)
    const [loading,  setLoading]  = useState(true)

    useEffect(() => {
        const controller = new AbortController()
        load(controller.signal)
        return () => controller.abort()
    }, [])

    async function load(signal) {
        try {
            const [urlsRes, scansRes, orgRes] = await Promise.all([
                api.get('/urls/',               { signal }).catch(() => ({ data: [] })),
                api.get('/scans/list/',          { signal }).catch(() => ({ data: [] })),
                api.get('/auth/organization/',   { signal }).catch(() => ({ data: null })),
            ])
            const urls  = urlsRes.data.results  || urlsRes.data  || []
            const scans = scansRes.data.results || scansRes.data || []
            setAllScans(scans)
            setOrgData({ ...orgRes.data, totalUrls: urls.length })
        } catch (err) {
            if (err.code !== 'ERR_CANCELED') console.error('Dashboard load error:', err)
        } finally {
            setLoading(false)
        }
    }

    // ── Derived metrics ──────────────────────────────────────────────────────
    const totalUrls     = orgData?.totalUrls || 0
    const totalScans    = allScans.length
    const completed     = allScans.filter(s => s.status === 'completed')
    const criticalTotal = allScans.reduce((a, s) => a + (s.critical_count || 0), 0)
    const highTotal     = allScans.reduce((a, s) => a + (s.high_count    || 0), 0)
    const mediumTotal   = allScans.reduce((a, s) => a + (s.medium_count  || 0), 0)
    const lowTotal      = allScans.reduce((a, s) => a + (s.low_count     || 0), 0)
    const critHighTotal = criticalTotal + highTotal

    const penalty       = (criticalTotal * 15 + highTotal * 7 + mediumTotal * 2) / Math.max(completed.length, 1)
    const securityScore = allScans.length === 0 ? 100 : Math.max(Math.round(100 - Math.min(penalty, 100)), 0)

    const currentPlan  = orgData?.plan || 'free'
    const plan         = planConfig[currentPlan] || planConfig.free
    const urlsUsed     = orgData?.urls_used ?? totalUrls
    const urlLimit     = orgData?.url_limit  ?? plan.limit
    const usagePercent = Math.min((urlsUsed / urlLimit) * 100, 100)
    const recentScans  = allScans.slice(0, 6)
    const activityData = buildActivityData(allScans)

    const findingsData = [
        { name: 'Crítico', value: criticalTotal, color: '#ef4444' },
        { name: 'Alto',    value: highTotal,     color: '#f97316' },
        { name: 'Medio',   value: mediumTotal,   color: '#eab308' },
        { name: 'Bajo',    value: lowTotal,      color: '#60a5fa' },
    ].filter(d => d.value > 0)

    // ── Animated counters ────────────────────────────────────────────────────
    const cUrls     = useCountUp(totalUrls)
    const cScans    = useCountUp(totalScans)
    const cFindings = useCountUp(critHighTotal)
    const cDone     = useCountUp(completed.length)
    const cScore    = useCountUp(securityScore, 1400)

    // ── Recharts theme ───────────────────────────────────────────────────────
    const gridStroke   = isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.10)'
    const tickFill     = isDark ? 'rgba(148,163,184,0.65)' : 'rgba(30,41,59,0.80)'
    const tooltipStyle = {
        background:   isDark ? '#0b1526' : '#ffffff',
        border:       `1px solid ${isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.08)'}`,
        borderRadius: '10px',
        fontSize:     12,
        color:        isDark ? '#e2eaf5' : '#0d1524',
        boxShadow:    '0 8px 32px rgba(0,0,0,0.2)',
    }
    const areaOpacity  = isDark ? 0.45 : 0.28

    if (loading) return <DashboardSkeleton />

    const statusColor = securityScore >= 80 ? '#10b981' : securityScore >= 60 ? '#f59e0b' : '#ef4444'

    const kpiCards = [
        {
            label: 'URLs Registradas',
            value: cUrls,
            icon: Globe,
            iconColor: '#60a5fa',
            glow: 'rgba(59,130,246,0.13)',
            border: 'rgba(59,130,246,0.28)',
        },
        {
            label: 'Escaneos Totales',
            value: cScans,
            icon: ScanSearch,
            iconColor: '#c084fc',
            glow: 'rgba(168,85,247,0.13)',
            border: 'rgba(168,85,247,0.28)',
        },
        {
            label: 'Hallazgos Críticos/Altos',
            value: cFindings,
            icon: AlertTriangle,
            iconColor: critHighTotal > 0 ? '#f87171' : '#34d399',
            glow: critHighTotal > 0 ? 'rgba(239,68,68,0.13)' : 'rgba(16,185,129,0.13)',
            border: critHighTotal > 0 ? 'rgba(239,68,68,0.28)' : 'rgba(16,185,129,0.28)',
        },
        {
            label: 'Escaneos Completados',
            value: cDone,
            icon: ShieldCheck,
            iconColor: '#34d399',
            glow: 'rgba(16,185,129,0.13)',
            border: 'rgba(16,185,129,0.28)',
        },
    ]

    return (
        <div className="space-y-5">

            {/* ── Welcome ─────────────────────────────────────────────────── */}
            <motion.div
                initial={{ opacity: 0, y: -8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.35 }}
                className="flex items-start justify-between flex-wrap gap-3 pl-3 md:pl-0"
            >
                <div>
                    <h1 className="text-2xl font-extrabold tracking-tight">
                        Hola,{' '}
                        <span style={{ background: 'linear-gradient(90deg,#60a5fa,#c084fc)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                            {user?.firstName || 'Usuario'}
                        </span>{' '}
                        👋
                    </h1>
                    <p className="text-muted-foreground text-sm mt-1 whitespace-nowrap">
                        {new Date().toLocaleDateString('es', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
                    </p>
                </div>
                <div
                    className="flex items-center gap-2 px-4 py-2 rounded-full text-sm font-semibold"
                    style={{
                        background: `${statusColor}18`,
                        border: `1px solid ${statusColor}40`,
                        color: statusColor,
                    }}
                >
                    <span className="w-2 h-2 rounded-full animate-pulse" style={{ background: statusColor }} />
                    Sistema {securityScore >= 80 ? 'Seguro' : securityScore >= 60 ? 'Moderado' : 'En riesgo'}
                </div>
            </motion.div>

            {/* ── KPI Cards ───────────────────────────────────────────────── */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {kpiCards.map((card, i) => (
                    <motion.div
                        key={card.label}
                        initial={{ opacity: 0, y: 16, scale: 0.97 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        transition={{ delay: i * 0.06, duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
                    >
                        <div
                            className="rounded-2xl p-5 h-full transition-all duration-300 cursor-default"
                            style={{
                                background: isDark
                                    ? `radial-gradient(ellipse at top left, ${card.glow} 0%, transparent 65%), hsl(var(--card))`
                                    : 'hsl(var(--card))',
                                border: isDark
                                    ? `1px solid ${card.border}`
                                    : '1px solid hsl(var(--border))',
                                boxShadow: isDark ? '' : '0 1px 3px rgba(0,0,0,0.06), 0 4px 12px rgba(0,0,0,0.04)',
                            }}
                            onMouseEnter={e => {
                                e.currentTarget.style.boxShadow = isDark
                                    ? `0 8px 32px ${card.glow}`
                                    : '0 4px 20px rgba(0,0,0,0.10)'
                            }}
                            onMouseLeave={e => {
                                e.currentTarget.style.boxShadow = isDark
                                    ? ''
                                    : '0 1px 3px rgba(0,0,0,0.06), 0 4px 12px rgba(0,0,0,0.04)'
                            }}
                        >
                            <div className="flex items-center justify-between mb-4">
                                <div
                                    className="w-10 h-10 rounded-xl flex items-center justify-center"
                                    style={{ background: `${card.iconColor}20` }}
                                >
                                    <card.icon className="w-5 h-5" style={{ color: card.iconColor }} />
                                </div>
                            </div>
                            <div
                                className="text-4xl font-black tabular-nums leading-none mb-1.5"
                                style={{ color: card.iconColor }}
                            >
                                {card.value}
                            </div>
                            <p className="text-sm text-muted-foreground font-medium">{card.label}</p>
                        </div>
                    </motion.div>
                ))}
            </div>

            {/* ── Charts row ──────────────────────────────────────────────── */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">

                {/* Activity area chart */}
                <motion.div
                    className="lg:col-span-2"
                    initial={{ opacity: 0, y: 14 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.28, duration: 0.35 }}
                >
                    <Card className="h-full">
                        <CardHeader className="pb-2">
                            <div className="flex items-center justify-between">
                                <CardTitle className="text-base font-semibold">Actividad de Escaneos</CardTitle>
                                <span className="text-xs text-muted-foreground">Últimos 7 días</span>
                            </div>
                        </CardHeader>
                        <CardContent className="pt-0 pr-2">
                            <ResponsiveContainer width="100%" height={220}>
                                <AreaChart data={activityData} margin={{ top: 8, right: 8, left: -24, bottom: 0 }}>
                                    <defs>
                                        <linearGradient id="gradScans" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="0%"   stopColor="#6366f1" stopOpacity={areaOpacity} />
                                            <stop offset="100%" stopColor="#6366f1" stopOpacity={0} />
                                        </linearGradient>
                                        <linearGradient id="gradFindings" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="0%"   stopColor="#f87171" stopOpacity={areaOpacity * 0.8} />
                                            <stop offset="100%" stopColor="#f87171" stopOpacity={0} />
                                        </linearGradient>
                                    </defs>
                                    <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} vertical={false} />
                                    <XAxis
                                        dataKey="date"
                                        tick={{ fontSize: 11, fill: tickFill }}
                                        axisLine={false} tickLine={false}
                                    />
                                    <YAxis
                                        tick={{ fontSize: 11, fill: tickFill }}
                                        axisLine={false} tickLine={false}
                                        allowDecimals={false}
                                    />
                                    <ReTooltip
                                        contentStyle={tooltipStyle}
                                        cursor={{ stroke: isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.04)', strokeWidth: 1 }}
                                    />
                                    <Area
                                        type="monotone" dataKey="scans" name="Escaneos"
                                        stroke="#6366f1" strokeWidth={2.5}
                                        fill="url(#gradScans)"
                                        dot={{ fill: '#6366f1', r: 3, strokeWidth: 0 }}
                                        activeDot={{ r: 5, fill: '#6366f1', strokeWidth: 2, stroke: isDark ? '#0b1526' : '#fff' }}
                                    />
                                    <Area
                                        type="monotone" dataKey="findings" name="Hallazgos C+A"
                                        stroke="#f87171" strokeWidth={2}
                                        fill="url(#gradFindings)"
                                        dot={{ fill: '#f87171', r: 3, strokeWidth: 0 }}
                                        activeDot={{ r: 5, fill: '#f87171', strokeWidth: 2, stroke: isDark ? '#0b1526' : '#fff' }}
                                    />
                                </AreaChart>
                            </ResponsiveContainer>

                            {/* Legend */}
                            <div className="flex items-center gap-5 justify-center mt-2 pb-1">
                                {[
                                    { color: '#6366f1', label: 'Escaneos' },
                                    { color: '#f87171', label: 'Hallazgos C+A' },
                                ].map(l => (
                                    <div key={l.label} className="flex items-center gap-1.5 text-xs text-muted-foreground">
                                        <span className="w-2.5 h-2.5 rounded-full" style={{ background: l.color }} />
                                        {l.label}
                                    </div>
                                ))}
                            </div>
                        </CardContent>
                    </Card>
                </motion.div>

                {/* Security gauge + findings breakdown */}
                <motion.div
                    initial={{ opacity: 0, y: 14 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.34, duration: 0.35 }}
                >
                    <Card className="h-full">
                        <CardHeader className="pb-2">
                            <CardTitle className="text-base font-semibold">Estado de Seguridad</CardTitle>
                        </CardHeader>
                        <CardContent className="flex flex-col items-center gap-5 pt-2">
                            <SecurityGauge score={cScore} />

                            <div className="w-full space-y-2.5">
                                <p className="text-[10px] font-bold tracking-widest uppercase text-muted-foreground">
                                    Hallazgos totales
                                </p>
                                {findingsData.length > 0 ? findingsData.map(d => (
                                    <div key={d.name} className="flex items-center justify-between">
                                        <div className="flex items-center gap-2 text-sm">
                                            <span className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ background: d.color }} />
                                            <span className="text-muted-foreground">{d.name}</span>
                                        </div>
                                        <span className="text-sm font-bold tabular-nums" style={{ color: d.color }}>
                                            {d.value}
                                        </span>
                                    </div>
                                )) : (
                                    <p className="text-xs text-muted-foreground text-center py-2">
                                        Sin hallazgos detectados ✓
                                    </p>
                                )}
                            </div>
                        </CardContent>
                    </Card>
                </motion.div>
            </div>

            {/* ── Bottom row ──────────────────────────────────────────────── */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">

                {/* Recent scans */}
                <motion.div
                    className="lg:col-span-2"
                    initial={{ opacity: 0, y: 14 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.4, duration: 0.35 }}
                >
                    <Card>
                        <CardHeader className="pb-3">
                            <div className="flex items-center justify-between">
                                <CardTitle className="text-base font-semibold flex items-center gap-2">
                                    <ScanSearch className="w-4 h-4 text-purple-400" />
                                    Escaneos Recientes
                                </CardTitle>
                                <Button asChild variant="ghost" size="sm" className="h-7 text-xs gap-1 text-muted-foreground">
                                    <Link to="/scans">
                                        Ver todos <ArrowRight className="w-3 h-3" />
                                    </Link>
                                </Button>
                            </div>
                        </CardHeader>
                        <CardContent className="p-0">
                            {recentScans.length === 0 ? (
                                <div className="flex flex-col items-center justify-center py-14 text-muted-foreground">
                                    <ScanSearch className="w-10 h-10 mb-3 opacity-20" />
                                    <p className="text-sm font-medium">Sin escaneos aún</p>
                                    <p className="text-xs mt-1 opacity-70">Registra una URL para comenzar</p>
                                    <Button asChild size="sm" className="mt-4 gradient-primary text-white border-0">
                                        <Link to="/urls">
                                            <Globe className="w-3.5 h-3.5 mr-1.5" /> Nueva URL
                                        </Link>
                                    </Button>
                                </div>
                            ) : (
                                <div className="divide-y divide-border/50">
                                    {recentScans.map(scan => (
                                        <Link
                                            key={scan.id}
                                            to={`/scans/${scan.id}/report`}
                                            className="flex items-center gap-3 px-5 py-3.5 hover:bg-accent/50 transition-colors group"
                                        >
                                            <StatusIcon status={scan.status} />
                                            <div className="flex-1 min-w-0">
                                                <p className="text-sm font-medium truncate">{scan.url}</p>
                                                <p className="text-xs text-muted-foreground mt-0.5">
                                                    {getStatusLabel(scan.status)}
                                                    {scan.started_at && (
                                                        <>
                                                            {' · '}
                                                            {new Date(scan.started_at).toLocaleDateString('es', {
                                                                month: 'short', day: 'numeric',
                                                                hour: '2-digit', minute: '2-digit',
                                                            })}
                                                        </>
                                                    )}
                                                </p>
                                            </div>
                                            <div className="flex items-center gap-1.5 flex-shrink-0">
                                                {scan.critical_count > 0 && (
                                                    <span className="severity-critical px-2 py-0.5 rounded text-[10px] font-bold border">
                                                        {scan.critical_count}C
                                                    </span>
                                                )}
                                                {scan.high_count > 0 && (
                                                    <span className="severity-high px-2 py-0.5 rounded text-[10px] font-bold border">
                                                        {scan.high_count}H
                                                    </span>
                                                )}
                                                {scan.medium_count > 0 && (
                                                    <span className="severity-medium px-2 py-0.5 rounded text-[10px] font-bold border">
                                                        {scan.medium_count}M
                                                    </span>
                                                )}
                                                {!scan.critical_count && !scan.high_count && !scan.medium_count && scan.status === 'completed' && (
                                                    <span className="text-emerald-500 text-[10px] font-semibold">Limpio ✓</span>
                                                )}
                                                <ArrowRight className="w-3.5 h-3.5 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                                            </div>
                                        </Link>
                                    ))}
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </motion.div>

                {/* Right column */}
                <div className="space-y-4">

                    {/* Plan card */}
                    <motion.div
                        initial={{ opacity: 0, y: 14 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.46, duration: 0.35 }}
                    >
                        <Card>
                            <CardHeader className="pb-3">
                                <CardTitle className="text-base font-semibold flex items-center gap-2">
                                    <Sparkles className="w-4 h-4 text-amber-400" /> Tu Plan
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="flex items-center gap-3">
                                    <div className={`w-11 h-11 rounded-xl bg-gradient-to-br ${plan.gradient} flex items-center justify-center shadow-lg`}>
                                        <plan.icon className="w-5 h-5 text-white" />
                                    </div>
                                    <div>
                                        <p className="font-bold capitalize">{currentPlan}</p>
                                        <span className={`${plan.badge} px-2 py-0.5 rounded text-[10px] font-bold`}>
                                            {currentPlan.toUpperCase()}
                                        </span>
                                    </div>
                                </div>
                                <div className="space-y-1.5">
                                    <div className="flex justify-between text-xs">
                                        <span className="text-muted-foreground">URLs usadas</span>
                                        <span className="font-semibold">{urlsUsed} / {urlLimit}</span>
                                    </div>
                                    <Progress value={usagePercent} className="h-1.5" />
                                </div>
                                {usagePercent >= 80 && usagePercent < 100 && (
                                    <p className="text-xs text-amber-500 flex items-center gap-1">
                                        <AlertTriangle className="w-3 h-3" /> Casi en el límite
                                    </p>
                                )}
                                {usagePercent >= 100 && (
                                    <p className="text-xs text-red-500 flex items-center gap-1">
                                        <AlertTriangle className="w-3 h-3" /> Límite alcanzado
                                    </p>
                                )}
                                {currentPlan !== 'ultimate' && (
                                    <Button asChild size="sm" className="w-full gradient-primary text-white border-0">
                                        <Link to="/plans">
                                            <Sparkles className="w-3.5 h-3.5 mr-1.5" /> Mejorar plan
                                        </Link>
                                    </Button>
                                )}
                            </CardContent>
                        </Card>
                    </motion.div>

                    {/* Quick actions */}
                    <motion.div
                        initial={{ opacity: 0, y: 14 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.52, duration: 0.35 }}
                    >
                        <Card>
                            <CardHeader className="pb-2">
                                <CardTitle className="text-base font-semibold">Acciones Rápidas</CardTitle>
                            </CardHeader>
                            <CardContent className="p-3 pt-0 space-y-1">
                                {[
                                    { to: '/urls',  icon: Globe,      label: 'Nueva URL',   sub: 'Registrar sitio web',    color: '#60a5fa', bg: 'rgba(59,130,246,0.1)'  },
                                    { to: '/scans', icon: ScanSearch, label: 'Escaneos',    sub: 'Ver historial completo', color: '#c084fc', bg: 'rgba(168,85,247,0.1)' },
                                    { to: '/plans', icon: Sparkles,   label: 'Planes',      sub: 'Gestionar suscripción',  color: '#fbbf24', bg: 'rgba(245,158,11,0.1)'  },
                                ].map(({ to, icon: Icon, label, sub, color, bg }) => (
                                    <Link
                                        key={to}
                                        to={to}
                                        className="flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all group"
                                        onMouseEnter={e => { e.currentTarget.style.background = bg }}
                                        onMouseLeave={e => { e.currentTarget.style.background = '' }}
                                    >
                                        <div
                                            className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
                                            style={{ background: bg }}
                                        >
                                            <Icon className="w-4 h-4" style={{ color }} />
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <p className="text-sm font-medium leading-none">{label}</p>
                                            <p className="text-xs text-muted-foreground mt-0.5">{sub}</p>
                                        </div>
                                        <ArrowRight className="w-3.5 h-3.5 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0" />
                                    </Link>
                                ))}
                            </CardContent>
                        </Card>
                    </motion.div>
                </div>
            </div>
        </div>
    )
}

// ─── Skeleton ─────────────────────────────────────────────────────────────────

function DashboardSkeleton() {
    return (
        <div className="space-y-5">
            <div className="flex items-start justify-between">
                <div>
                    <Skeleton className="h-8 w-52 mb-1.5" />
                    <Skeleton className="h-4 w-64" />
                </div>
                <Skeleton className="h-9 w-36 rounded-full" />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {[0, 1, 2, 3].map(i => (
                    <div key={i} className="rounded-2xl border p-5 bg-card">
                        <Skeleton className="w-10 h-10 rounded-xl mb-4" />
                        <Skeleton className="h-10 w-16 mb-2" />
                        <Skeleton className="h-4 w-36" />
                    </div>
                ))}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                <Card className="lg:col-span-2">
                    <CardContent className="p-5">
                        <div className="flex justify-between mb-4">
                            <Skeleton className="h-5 w-44" />
                            <Skeleton className="h-4 w-24" />
                        </div>
                        <Skeleton className="h-[220px] w-full rounded-xl" />
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="p-5 flex flex-col items-center gap-4">
                        <Skeleton className="h-5 w-32 self-start" />
                        <Skeleton className="w-32 h-32 rounded-full" />
                        <div className="w-full space-y-2.5">
                            {[0, 1, 2, 3].map(i => (
                                <div key={i} className="flex justify-between">
                                    <Skeleton className="h-4 w-20" />
                                    <Skeleton className="h-4 w-8" />
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                <Card className="lg:col-span-2">
                    <CardContent className="p-0">
                        <div className="flex justify-between items-center p-5 border-b">
                            <Skeleton className="h-5 w-44" />
                            <Skeleton className="h-7 w-20" />
                        </div>
                        {[0, 1, 2, 3, 4].map(i => (
                            <div key={i} className="flex items-center gap-3 px-5 py-3.5">
                                <Skeleton className="w-4 h-4 rounded-full" />
                                <div className="flex-1">
                                    <Skeleton className="h-4 w-full mb-1.5" />
                                    <Skeleton className="h-3 w-28" />
                                </div>
                            </div>
                        ))}
                    </CardContent>
                </Card>
                <div className="space-y-4">
                    <Card>
                        <CardContent className="p-5 space-y-3">
                            <Skeleton className="h-5 w-24" />
                            <div className="flex gap-3">
                                <Skeleton className="w-11 h-11 rounded-xl" />
                                <div className="space-y-2">
                                    <Skeleton className="h-5 w-20" />
                                    <Skeleton className="h-4 w-16" />
                                </div>
                            </div>
                            <Skeleton className="h-1.5 w-full" />
                        </CardContent>
                    </Card>
                    <Card>
                        <CardContent className="p-3 space-y-1">
                            {[0, 1, 2].map(i => (
                                <div key={i} className="flex items-center gap-3 p-2.5">
                                    <Skeleton className="w-8 h-8 rounded-lg" />
                                    <div className="flex-1 space-y-1.5">
                                        <Skeleton className="h-4 w-24" />
                                        <Skeleton className="h-3 w-32" />
                                    </div>
                                </div>
                            ))}
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    )
}
