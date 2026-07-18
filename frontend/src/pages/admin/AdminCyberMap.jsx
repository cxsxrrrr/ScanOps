import { useState, useEffect, useRef } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Button } from '@/components/ui/button'
import { Search, Globe, MapPin, Activity, Target, User, List, Play, Pause, ChevronLeft, ChevronRight, FileText, Download, FileSpreadsheet } from 'lucide-react'
import api from '../../lib/api'
import GlobeGL from 'react-globe.gl'

// Cyberpunk 2077 palette
const CYBER_CYAN = '#00f0ff'
const CYBER_RED = '#ff2a6d'
const CYBER_YELLOW = '#fcee0a'

export function AdminCyberMap() {
    const [scans, setScans] = useState([])
    const [countries, setCountries] = useState([])
    const [loading, setLoading] = useState(true)
    const [search, setSearch] = useState('')
    const [statusFilter, setStatusFilter] = useState('all')
    const [timeFilter, setTimeFilter] = useState('general')
    const [autoRotate, setAutoRotate] = useState(true)
    const [page, setPage] = useState(1)
    const [pageSize, setPageSize] = useState(5)
    const [reportData, setReportData] = useState(null)
    const [reportLoading, setReportLoading] = useState(false)
    const [reportError, setReportError] = useState(null)
    const globeEl = useRef()

    useEffect(() => {
        loadMapData()
        loadReportSummary()
    }, [timeFilter])

    useEffect(() => {
        // Continent polygons for the raised-relief (Kaspersky style) landmasses
        fetch('/data/ne_110m_admin_0_countries.geojson')
            .then(res => res.json())
            .then(data => setCountries(data.features || []))
            .catch(err => console.error('Failed to load continents:', err))
    }, [])

    useEffect(() => {
        // Auto-rotate globe slightly
        if (globeEl.current) {
            globeEl.current.controls().autoRotate = autoRotate
            globeEl.current.controls().autoRotateSpeed = 0.5
        }
    }, [loading, autoRotate])

    useEffect(() => {
        // Dark teal ocean, visible but still on-theme (Cyberpunk night-city look)
        if (!loading && globeEl.current) {
            const material = globeEl.current.globeMaterial()
            material.color.set('#153c5f')
            material.emissive.set('#1a4d7a')
            material.specular.set(CYBER_CYAN)
            material.shininess = 30
        }
    }, [loading])

    useEffect(() => {
        setPage(1)
    }, [search, statusFilter, timeFilter])

    async function loadMapData() {
        setLoading(true)
        try {
            const res = await api.get(`/admin/cyber-map/?days=${timeFilter}`)
            setScans(res.data || [])
        } catch (err) {
            console.error('Failed to load cyber map:', err)
        } finally {
            setLoading(false)
        }
    }

    async function loadReportSummary() {
        setReportLoading(true)
        setReportError(null)
        try {
            const res = await api.get(`/admin/reports/summary/?days=${timeFilter}`)
            setReportData(res.data || null)
        } catch (err) {
            console.error('Failed to load report summary:', err)
            setReportError('No se pudo cargar el resumen del reporte.')
        } finally {
            setReportLoading(false)
        }
    }

    async function downloadReport(format) {
        try {
            const res = await api.get(`/admin/reports/export/?format=${format}&days=${timeFilter}`, {
                responseType: 'blob',
            })
            const contentDisposition = res.headers['content-disposition']
            let filename = `reporte_global_${timeFilter}.${format === 'excel' ? 'xlsx' : 'pdf'}`
            if (contentDisposition) {
                const match = contentDisposition.match(/filename="?([^";]+)"?/)
                if (match) filename = match[1]
            }
            const url = window.URL.createObjectURL(new Blob([res.data]))
            const link = document.createElement('a')
            link.href = url
            link.setAttribute('download', filename)
            document.body.appendChild(link)
            link.click()
            link.remove()
            window.URL.revokeObjectURL(url)
        } catch (err) {
            console.error('Failed to download report:', err)
            alert('No se pudo descargar el reporte.')
        }
    }

    const filteredScans = scans.filter(s => {
        const matchesSearch = s.user.toLowerCase().includes(search.toLowerCase()) ||
                              s.target_url.toLowerCase().includes(search.toLowerCase()) ||
                              s.origin_ip.includes(search) ||
                              s.target_ip.includes(search)
        const matchesStatus = statusFilter === 'all' || s.status === statusFilter
        return matchesSearch && matchesStatus
    })

    const totalPages = Math.max(1, Math.ceil(filteredScans.length / pageSize))
    const startIndex = (page - 1) * pageSize
    const endIndex = startIndex + pageSize
    const paginatedScans = filteredScans.slice(startIndex, endIndex)

    // Add a tiny bit of random jitter to coordinates so overlapping local tests don't hide each other
    const jitter = () => (Math.random() - 0.5) * 1.5;

    // Prepare arcs for 3D Globe
    const arcsData = filteredScans.map(scan => ({
        startLat: scan.origin_geo.lat + jitter(),
        startLng: scan.origin_geo.lng + jitter(),
        endLat: scan.target_geo.lat + jitter(),
        endLng: scan.target_geo.lng + jitter(),
        color: scan.status === 'error' ? [CYBER_RED, CYBER_RED] : [CYBER_CYAN, CYBER_CYAN],
        user: scan.user,
        target: scan.target_url,
        origin_ip: scan.origin_ip,
        target_ip: scan.target_ip
    })).filter(arc => arc.startLat && arc.endLat) // Ensure coordinates exist

    // Prepare points for 3D Globe (origins and targets)
    const pointsData = []
    filteredScans.forEach((scan, i) => {
        if (scan.origin_geo.lat) {
            pointsData.push({
                lat: scan.origin_geo.lat + jitter(),
                lng: scan.origin_geo.lng + jitter(),
                size: 0.4,
                color: CYBER_CYAN,
                label: `Origen: ${scan.user} (${scan.origin_ip})`,
                type: 'origin'
            })
        }
        if (scan.target_geo.lat) {
            pointsData.push({
                lat: scan.target_geo.lat + jitter(),
                lng: scan.target_geo.lng + jitter(),
                size: 0.4,
                color: scan.status === 'error' ? CYBER_RED : CYBER_YELLOW,
                label: `Destino: ${scan.target_url} (${scan.target_ip})`,
                type: 'target'
            })
        }
    })

    return (
        <div className="space-y-4 mt-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <h3 className="text-lg font-semibold flex items-center gap-2">
                    <Globe className="w-5 h-5 text-blue-500" /> Monitor de Amenazas Global
                </h3>
                
                {/* Global Filters */}
                <div className="flex flex-col sm:flex-row items-center gap-3">
                    <div className="relative w-full sm:w-64">
                        <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                        <Input
                            placeholder="Buscar IP, URL o Usuario..."
                            className="pl-8 h-9 text-sm w-full"
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                        />
                    </div>
                    <Select value={timeFilter} onValueChange={setTimeFilter}>
                        <SelectTrigger className="w-full sm:w-[150px] h-9">
                            <SelectValue placeholder="Tiempo" />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="general">General (Todos)</SelectItem>
                            <SelectItem value="1">Hoy</SelectItem>
                            <SelectItem value="7">Últimos 7 días</SelectItem>
                            <SelectItem value="30">Últimos 30 días</SelectItem>
                        </SelectContent>
                    </Select>
                    <Select value={statusFilter} onValueChange={setStatusFilter}>
                        <SelectTrigger className="w-full sm:w-[140px] h-9">
                            <SelectValue placeholder="Estado" />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="all">Cualquiera</SelectItem>
                            <SelectItem value="completed">Exitosos</SelectItem>
                            <SelectItem value="error">Con Error</SelectItem>
                            <SelectItem value="running">En Progreso</SelectItem>
                        </SelectContent>
                    </Select>
                </div>
            </div>

            <Tabs defaultValue="list" className="w-full">
                <TabsList className="w-full max-w-md mb-2 grid grid-cols-3">
                    <TabsTrigger value="list" className="flex items-center gap-2">
                        <List className="w-4 h-4" /> Registro
                    </TabsTrigger>
                    <TabsTrigger value="map" className="flex items-center gap-2">
                        <Globe className="w-4 h-4" /> Mapa 3D
                    </TabsTrigger>
                    <TabsTrigger value="report" className="flex items-center gap-2">
                        <FileText className="w-4 h-4" /> Reportes
                    </TabsTrigger>
                </TabsList>
                
                <TabsContent value="map" className="mt-2">
                    <Card className="overflow-hidden flex flex-col relative bg-[#05060f] h-[600px] border-cyan-500/20 shadow-[0_0_50px_rgba(0,240,255,0.07)]">
                        {loading ? (
                            <div className="flex-1 flex items-center justify-center h-full">
                                <Globe className="w-12 h-12 text-muted-foreground/30 animate-pulse" />
                            </div>
                        ) : (
                            <div className="flex-1 cursor-grab active:cursor-grabbing w-full h-full relative flex items-center justify-center">
                                <Button 
                                    variant="secondary" 
                                    size="sm" 
                                    className="absolute bottom-4 right-4 z-10 opacity-70 hover:opacity-100 backdrop-blur-md"
                                    onClick={() => setAutoRotate(!autoRotate)}
                                >
                                    {autoRotate ? <Pause className="w-4 h-4 mr-2" /> : <Play className="w-4 h-4 mr-2" />}
                                    {autoRotate ? 'Pausar Rotación' : 'Rotar Mundo'}
                                </Button>
                                <GlobeGL
                                    ref={globeEl}
                                    backgroundImageUrl="//unpkg.com/three-globe/example/img/night-sky.png"
                                    showAtmosphere={true}
                                    atmosphereColor={CYBER_CYAN}
                                    atmosphereAltitude={0.18}
                                    polygonsData={countries}
                                    polygonAltitude={0.03}
                                    polygonCapColor={() => 'rgba(220, 30, 80, 0.85)'}
                                    polygonSideColor={() => 'rgba(120, 10, 40, 0.9)'}
                                    polygonStrokeColor={() => CYBER_RED}
                                    polygonLabel={(d) => `<div style="padding:4px 10px;background:rgba(5,8,20,0.92);border:1px solid ${CYBER_CYAN};color:${CYBER_CYAN};font-family:monospace;font-size:11px;letter-spacing:2px;text-transform:uppercase;">${d.properties.ADMIN}</div>`}
                                    polygonsTransitionDuration={1000}
                                    arcsData={arcsData}
                                    arcColor="color"
                                    arcDashLength={0.4}
                                    arcDashGap={0.2}
                                    arcDashAnimateTime={1500}
                                    arcsTransitionDuration={1000}
                                    arcLabel={(d) => `Origen: ${d.origin_ip}\nDestino: ${d.target_url} (${d.target_ip})`}
                                    ringsData={pointsData}
                                    ringColor="color"
                                    ringMaxRadius={3}
                                    ringPropagationSpeed={1.5}
                                    ringRepeatPeriod={1200}
                                    ringAltitude={0.035}
                                    pointsData={pointsData}
                                    pointColor="color"
                                    pointAltitude={0.035}
                                    pointRadius="size"
                                    pointsMerge={false}
                                    pointLabel="label"
                                    width={typeof window !== 'undefined' ? window.innerWidth > 300 ? window.innerWidth - 320 : window.innerWidth : 800}
                                    height={600}
                                />
                            </div>
                        )}
                    </Card>
                </TabsContent>

                <TabsContent value="list" className="mt-2">
                    <Card className="h-[600px] flex flex-col overflow-hidden">
                        <CardHeader className="pb-3 border-b">
                            <CardTitle className="text-base flex items-center gap-2">
                                <Activity className="w-4 h-4 text-emerald-500" /> Registro de Actividad
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="flex-1 overflow-y-auto p-0">
                            <div className="divide-y divide-border">
                                {loading ? (
                                    <p className="p-8 text-center text-muted-foreground text-sm animate-pulse">Cargando monitor global...</p>
                                ) : filteredScans.length === 0 ? (
                                    <p className="p-8 text-center text-muted-foreground text-sm">No hay registros recientes o coincidencia.</p>
                                ) : (
                                    paginatedScans.map((scan) => (
                                        <div key={scan.id} className="p-4 hover:bg-accent/30 transition-colors text-sm">
                                            <div className="flex items-start justify-between">
                                                <div className="flex flex-col gap-1.5">
                                                    <div className="flex items-center gap-2 font-medium">
                                                        <User className="w-3.5 h-3.5 text-blue-500" /> {scan.user}
                                                    </div>
                                                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                                                        <MapPin className="w-3.5 h-3.5" /> 
                                                        Origen: <span className="text-foreground">{scan.origin_ip}</span> 
                                                        ({scan.origin_geo?.country || 'Desconocido'})
                                                    </div>
                                                </div>
                                                <div className="flex flex-col items-end gap-1.5 text-right">
                                                    <div className="flex items-center gap-2 font-medium">
                                                        {scan.target_url} <Target className="w-3.5 h-3.5 text-orange-500" />
                                                    </div>
                                                    <div className="flex items-center justify-end gap-2 text-xs text-muted-foreground">
                                                        Destino: <span className="text-foreground">{scan.target_ip}</span>
                                                        ({scan.target_geo?.country || 'Desconocido'})
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    ))
                                )}
                            </div>
                        </CardContent>
                        {filteredScans.length > 0 && (
                            <div className="border-t p-3 flex flex-col sm:flex-row items-center justify-between gap-3 bg-muted/30 shrink-0">
                                <div className="text-xs text-muted-foreground">
                                    Mostrando <span className="font-medium text-foreground">{startIndex + 1}</span>-<span className="font-medium text-foreground">{Math.min(endIndex, filteredScans.length)}</span> de <span className="font-medium text-foreground">{filteredScans.length}</span> registros
                                </div>
                                <div className="flex items-center gap-3">
                                    <Select value={String(pageSize)} onValueChange={(v) => { setPageSize(Number(v)); setPage(1) }}>
                                        <SelectTrigger className="h-8 w-[110px] text-xs">
                                            <SelectValue placeholder="Por página" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="5">5 / pág</SelectItem>
                                            <SelectItem value="10">10 / pág</SelectItem>
                                            <SelectItem value="25">25 / pág</SelectItem>
                                            <SelectItem value="50">50 / pág</SelectItem>
                                            <SelectItem value="100">100 / pág</SelectItem>
                                        </SelectContent>
                                    </Select>
                                    <div className="flex items-center gap-1">
                                        <Button
                                            variant="outline"
                                            size="icon"
                                            className="h-8 w-8"
                                            onClick={() => setPage(p => Math.max(1, p - 1))}
                                            disabled={page === 1}
                                        >
                                            <ChevronLeft className="w-4 h-4" />
                                        </Button>
                                        <span className="text-sm tabular-nums px-2 min-w-[90px] text-center">
                                            Página {page} de {totalPages}
                                        </span>
                                        <Button
                                            variant="outline"
                                            size="icon"
                                            className="h-8 w-8"
                                            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                                            disabled={page === totalPages}
                                        >
                                            <ChevronRight className="w-4 h-4" />
                                        </Button>
                                    </div>
                                </div>
                            </div>
                        )}
                    </Card>
                </TabsContent>

                <TabsContent value="report" className="mt-2">
                    <Card className="h-[600px] flex flex-col overflow-hidden">
                        <CardHeader className="pb-3 border-b">
                            <CardTitle className="text-base flex items-center gap-2">
                                <FileText className="w-4 h-4 text-cyan-500" /> Reporte Global
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
                            {reportLoading ? (
                                <p className="p-8 text-center text-muted-foreground text-sm animate-pulse">Generando reporte...</p>
                            ) : reportError ? (
                                <p className="p-8 text-center text-destructive text-sm">{reportError}</p>
                            ) : !reportData ? (
                                <p className="p-8 text-center text-muted-foreground text-sm">No hay datos para el período seleccionado.</p>
                            ) : (
                                <div className="space-y-4">
                                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                                        <div className="bg-muted/40 rounded-lg p-3 border">
                                            <p className="text-xs text-muted-foreground">Total escaneos</p>
                                            <p className="text-xl font-bold">{reportData.total_scans}</p>
                                        </div>
                                        <div className="bg-muted/40 rounded-lg p-3 border">
                                            <p className="text-xs text-muted-foreground">Completados</p>
                                            <p className="text-xl font-bold text-emerald-500">{reportData.status_counts?.completed || 0}</p>
                                        </div>
                                        <div className="bg-muted/40 rounded-lg p-3 border">
                                            <p className="text-xs text-muted-foreground">Con error</p>
                                            <p className="text-xl font-bold text-red-500">{reportData.status_counts?.error || 0}</p>
                                        </div>
                                        <div className="bg-muted/40 rounded-lg p-3 border">
                                            <p className="text-xs text-muted-foreground">En progreso</p>
                                            <p className="text-xl font-bold text-amber-500">{reportData.status_counts?.running || 0}</p>
                                        </div>
                                    </div>

                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        <div className="border rounded-lg p-3">
                                            <h4 className="text-sm font-semibold mb-2 flex items-center gap-2">
                                                <MapPin className="w-3.5 h-3.5 text-cyan-500" /> Países de Origen
                                            </h4>
                                            <ul className="space-y-1 text-sm">
                                                {reportData.top_origin_countries?.length ? reportData.top_origin_countries.map((item, i) => (
                                                    <li key={i} className="flex justify-between py-1 border-b last:border-0">
                                                        <span>{item.country}</span>
                                                        <span className="font-medium">{item.count}</span>
                                                    </li>
                                                )) : <li className="text-muted-foreground text-xs">Sin datos</li>}
                                            </ul>
                                        </div>
                                        <div className="border rounded-lg p-3">
                                            <h4 className="text-sm font-semibold mb-2 flex items-center gap-2">
                                                <Target className="w-3.5 h-3.5 text-purple-500" /> Países Auditados
                                            </h4>
                                            <ul className="space-y-1 text-sm">
                                                {reportData.top_target_countries?.length ? reportData.top_target_countries.map((item, i) => (
                                                    <li key={i} className="flex justify-between py-1 border-b last:border-0">
                                                        <span>{item.country}</span>
                                                        <span className="font-medium">{item.count}</span>
                                                    </li>
                                                )) : <li className="text-muted-foreground text-xs">Sin datos</li>}
                                            </ul>
                                        </div>
                                        <div className="border rounded-lg p-3">
                                            <h4 className="text-sm font-semibold mb-2 flex items-center gap-2">
                                                <User className="w-3.5 h-3.5 text-emerald-500" /> Usuarios con más peticiones
                                            </h4>
                                            <ul className="space-y-1 text-sm">
                                                {reportData.top_users?.length ? reportData.top_users.map((item, i) => (
                                                    <li key={i} className="flex justify-between py-1 border-b last:border-0">
                                                        <span className="truncate max-w-[200px]" title={item.user}>{item.user}</span>
                                                        <span className="font-medium">{item.count}</span>
                                                    </li>
                                                )) : <li className="text-muted-foreground text-xs">Sin datos</li>}
                                            </ul>
                                        </div>
                                        <div className="border rounded-lg p-3">
                                            <h4 className="text-sm font-semibold mb-2 flex items-center gap-2">
                                                <Globe className="w-3.5 h-3.5 text-orange-500" /> Rutas más auditadas
                                            </h4>
                                            <ul className="space-y-1 text-sm">
                                                {reportData.top_targets?.length ? reportData.top_targets.map((item, i) => (
                                                    <li key={i} className="flex justify-between py-1 border-b last:border-0">
                                                        <span className="truncate max-w-[200px]" title={item.url}>{item.url}</span>
                                                        <span className="font-medium">{item.count}</span>
                                                    </li>
                                                )) : <li className="text-muted-foreground text-xs">Sin datos</li>}
                                            </ul>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </CardContent>
                        <div className="border-t p-3 flex flex-col sm:flex-row items-center justify-between gap-3 bg-muted/30 shrink-0">
                            <p className="text-xs text-muted-foreground">
                                Generado: {reportData?.generated_at ? new Date(reportData.generated_at).toLocaleString('es-ES') : '-'}
                            </p>
                            <div className="flex items-center gap-2">
                                <Button
                                    variant="outline"
                                    size="sm"
                                    className="h-9"
                                    onClick={() => downloadReport('excel')}
                                    disabled={reportLoading || !reportData}
                                >
                                    <FileSpreadsheet className="w-4 h-4 mr-2" /> Excel
                                </Button>
                                <Button
                                    variant="outline"
                                    size="sm"
                                    className="h-9"
                                    onClick={() => downloadReport('pdf')}
                                    disabled={reportLoading || !reportData}
                                >
                                    <Download className="w-4 h-4 mr-2" /> PDF
                                </Button>
                            </div>
                        </div>
                    </Card>
                </TabsContent>
            </Tabs>
        </div>
    )
}
