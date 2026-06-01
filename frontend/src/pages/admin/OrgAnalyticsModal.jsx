import { useState, useEffect } from 'react'
import {
    Dialog, DialogContent, DialogHeader,
    DialogTitle, DialogDescription,
} from '@/components/ui/dialog'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Loader2, AlertTriangle, ShieldCheck, Activity, Users, Globe } from 'lucide-react'
import api from '../../lib/api'
import { toast } from 'sonner'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'

export function OrgAnalyticsModal({ orgId, open, onOpenChange }) {
    const [data, setData] = useState(null)
    const [loading, setLoading] = useState(false)

    useEffect(() => {
        if (orgId && open) {
            loadAnalytics()
        } else {
            setData(null)
        }
    }, [orgId, open])

    async function loadAnalytics() {
        setLoading(true)
        try {
            const res = await api.get(`/admin/analytics/organizations/${orgId}/`)
            setData(res.data)
        } catch (err) {
            toast.error('Error al cargar análisis de la empresa')
            onOpenChange(false)
        } finally {
            setLoading(false)
        }
    }

    // Chart formatting
    const chartData = data?.recent_scans?.map(scan => ({
        date: new Date(scan.started_at).toLocaleDateString('es-VE', { month: 'short', day: 'numeric' }),
        findings: scan.findings_count,
        status: scan.status
    })) || []

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto custom-scrollbar">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2 text-2xl">
                        <Activity className="w-6 h-6 text-purple-500" /> 
                        {data?.organization?.name || 'Cargando...'}
                    </DialogTitle>
                    <DialogDescription>
                        Análisis detallado de seguridad y comportamiento
                    </DialogDescription>
                </DialogHeader>
                
                {loading || !data ? (
                    <div className="flex justify-center items-center py-20">
                        <Loader2 className="w-10 h-10 animate-spin text-primary" />
                    </div>
                ) : (
                    <div className="space-y-6 mt-4">
                        
                        {/* KPI Cards */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            <Card className="bg-destructive/5 border-destructive/20">
                                <CardContent className="p-4 flex flex-col items-center justify-center text-center">
                                    <AlertTriangle className="w-8 h-8 text-destructive mb-2" />
                                    <span className="text-3xl font-bold text-destructive">{data.total_findings.CRITICAL}</span>
                                    <span className="text-xs text-muted-foreground uppercase font-semibold">Críticos (Últ. Scan)</span>
                                </CardContent>
                            </Card>
                            <Card className="bg-orange-500/5 border-orange-500/20">
                                <CardContent className="p-4 flex flex-col items-center justify-center text-center">
                                    <AlertTriangle className="w-8 h-8 text-orange-500 mb-2" />
                                    <span className="text-3xl font-bold text-orange-500">{data.total_findings.HIGH}</span>
                                    <span className="text-xs text-muted-foreground uppercase font-semibold">Altos (Últ. Scan)</span>
                                </CardContent>
                            </Card>
                            <Card>
                                <CardContent className="p-4 flex flex-col items-center justify-center text-center">
                                    <Globe className="w-8 h-8 text-blue-500 mb-2" />
                                    <span className="text-3xl font-bold text-blue-500">{data.urls.length}</span>
                                    <span className="text-xs text-muted-foreground uppercase font-semibold">URLs Activas</span>
                                </CardContent>
                            </Card>
                            <Card>
                                <CardContent className="p-4 flex flex-col items-center justify-center text-center">
                                    <Users className="w-8 h-8 text-emerald-500 mb-2" />
                                    <span className="text-3xl font-bold text-emerald-500">{data.users.length}</span>
                                    <span className="text-xs text-muted-foreground uppercase font-semibold">Usuarios Registrados</span>
                                </CardContent>
                            </Card>
                        </div>

                        {/* Chart */}
                        <Card>
                            <CardHeader className="pb-2">
                                <CardTitle className="text-sm">Tendencia de Hallazgos (Histórico Global)</CardTitle>
                            </CardHeader>
                            <CardContent className="h-64">
                                {chartData.length > 0 ? (
                                    <ResponsiveContainer width="100%" height="100%">
                                        <LineChart data={chartData}>
                                            <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                                            <XAxis dataKey="date" fontSize={12} tickMargin={10} />
                                            <YAxis fontSize={12} allowDecimals={false} />
                                            <Tooltip 
                                                contentStyle={{ backgroundColor: 'rgba(0,0,0,0.8)', border: 'none', borderRadius: '8px', color: 'white' }}
                                                itemStyle={{ color: '#ec4899' }}
                                            />
                                            <Line type="monotone" dataKey="findings" name="Hallazgos" stroke="#ec4899" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 6 }} />
                                        </LineChart>
                                    </ResponsiveContainer>
                                ) : (
                                    <div className="h-full flex items-center justify-center text-muted-foreground text-sm">
                                        No hay escaneos suficientes para graficar.
                                    </div>
                                )}
                            </CardContent>
                        </Card>

                        {/* Two column layout for URLs and Users */}
                        <div className="grid md:grid-cols-2 gap-4">
                            <Card>
                                <CardHeader className="pb-2">
                                    <CardTitle className="text-sm">Estado de las URLs</CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <div className="space-y-3 max-h-64 overflow-y-auto pr-2 custom-scrollbar">
                                        {data.urls.length === 0 ? <p className="text-xs text-muted-foreground">Sin URLs</p> : null}
                                        {data.urls.map(url => (
                                            <div key={url.id} className="flex flex-col p-3 bg-muted/30 rounded-lg text-sm border">
                                                <div className="flex justify-between items-start mb-2">
                                                    <span className="font-medium truncate max-w-[200px]" title={url.url}>{url.url}</span>
                                                    <Badge variant={url.status === 'active' ? 'default' : 'secondary'}>{url.status}</Badge>
                                                </div>
                                                <div className="flex gap-2 text-xs">
                                                    <Badge variant="destructive" className="px-1.5 py-0">C: {url.critical}</Badge>
                                                    <Badge variant="warning" className="bg-orange-500 hover:bg-orange-600 px-1.5 py-0 text-white">A: {url.high}</Badge>
                                                    <Badge variant="secondary" className="px-1.5 py-0">M: {url.medium}</Badge>
                                                </div>
                                                <span className="text-[10px] text-muted-foreground mt-2">
                                                    Último scan: {url.last_scan_date ? new Date(url.last_scan_date).toLocaleString() : 'Nunca'}
                                                </span>
                                            </div>
                                        ))}
                                    </div>
                                </CardContent>
                            </Card>

                            <Card>
                                <CardHeader className="pb-2">
                                    <CardTitle className="text-sm">Usuarios del Equipo</CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <div className="space-y-3 max-h-64 overflow-y-auto pr-2 custom-scrollbar">
                                        {data.users.length === 0 ? <p className="text-xs text-muted-foreground">Sin usuarios</p> : null}
                                        {data.users.map(user => (
                                            <div key={user.id} className="flex justify-between items-center p-3 bg-muted/30 rounded-lg text-sm border">
                                                <div className="flex flex-col">
                                                    <span className="font-medium">{user.email}</span>
                                                    <span className="text-[10px] text-muted-foreground">
                                                        Último login: {user.last_login ? new Date(user.last_login).toLocaleDateString() : 'Desconocido'}
                                                    </span>
                                                </div>
                                                <Badge variant={user.role === 'admin' ? 'destructive' : 'secondary'}>
                                                    {user.role}
                                                </Badge>
                                            </div>
                                        ))}
                                    </div>
                                </CardContent>
                            </Card>
                        </div>
                    </div>
                )}
            </DialogContent>
        </Dialog>
    )
}
