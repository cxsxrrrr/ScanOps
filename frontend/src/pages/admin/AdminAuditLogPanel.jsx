import { useState, useEffect } from 'react'
import { toast } from 'sonner'
import api from '../../lib/api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
    Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select'
import {
    ScrollText, Search, ChevronLeft, ChevronRight, Loader2,
    UserCog, Building2, CreditCard, Ban, ArrowRight,
} from 'lucide-react'

const ACTION_LABELS = {
    role_change: 'Cambio de rol',
    org_change: 'Cambio de organización',
    plan_change: 'Cambio de plan',
    block_change: 'Bloqueo/Desbloqueo',
}

const ACTION_ICONS = {
    role_change: UserCog,
    org_change: Building2,
    plan_change: CreditCard,
    block_change: Ban,
}

const ACTION_COLOR = {
    role_change: 'text-purple-500 bg-purple-500/10',
    org_change: 'text-blue-500 bg-blue-500/10',
    plan_change: 'text-amber-500 bg-amber-500/10',
    block_change: 'text-red-500 bg-red-500/10',
}

const PAGE_SIZE = 20

function formatDate(iso) {
    return new Date(iso).toLocaleString('es-VE', {
        day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit',
    })
}

export function AdminAuditLogPanel() {
    const [logs, setLogs] = useState([])
    const [count, setCount] = useState(0)
    const [loading, setLoading] = useState(true)
    const [search, setSearch] = useState('')
    const [actionFilter, setActionFilter] = useState('all')
    const [page, setPage] = useState(1)

    useEffect(() => { loadLogs() }, [search, actionFilter, page])

    async function loadLogs() {
        setLoading(true)
        try {
            const params = { page, page_size: PAGE_SIZE }
            if (search) params.search = search
            if (actionFilter !== 'all') params.action = actionFilter
            const res = await api.get('/admin/audit-logs/actions/', { params })
            setLogs(res.data.results)
            setCount(res.data.count)
        } catch (err) {
            toast.error('Error al cargar el registro de auditoría.')
        } finally {
            setLoading(false)
        }
    }

    const totalPages = Math.ceil(count / PAGE_SIZE) || 1

    function targetLabel(log) {
        return log.target_user_email || log.target_org_name || '—'
    }

    return (
        <Card>
            <CardHeader className="pb-3 flex flex-row items-center justify-between space-y-0">
                <CardTitle className="text-base flex items-center gap-2">
                    <ScrollText className="w-4 h-4 text-slate-500" /> Auditoría ({count})
                </CardTitle>
                <div className="flex items-center gap-2">
                    <div className="relative w-64">
                        <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                        <Input
                            placeholder="Buscar por admin, usuario u org..."
                            className="pl-8"
                            value={search}
                            onChange={(e) => { setSearch(e.target.value); setPage(1) }}
                        />
                    </div>
                    <Select value={actionFilter} onValueChange={(v) => { setActionFilter(v); setPage(1) }}>
                        <SelectTrigger className="w-48"><SelectValue /></SelectTrigger>
                        <SelectContent>
                            <SelectItem value="all">Todas las acciones</SelectItem>
                            <SelectItem value="role_change">Cambio de rol</SelectItem>
                            <SelectItem value="org_change">Cambio de organización</SelectItem>
                            <SelectItem value="plan_change">Cambio de plan</SelectItem>
                            <SelectItem value="block_change">Bloqueo/Desbloqueo</SelectItem>
                        </SelectContent>
                    </Select>
                </div>
            </CardHeader>
            <CardContent className="p-0">
                {loading ? (
                    <div className="py-8 flex justify-center">
                        <Loader2 className="w-6 h-6 animate-spin text-slate-400" />
                    </div>
                ) : logs.length === 0 ? (
                    <p className="p-8 text-center text-muted-foreground text-sm">
                        Sin acciones administrativas registradas todavía.
                    </p>
                ) : (
                    <div className="divide-y divide-border">
                        {logs.map((log) => {
                            const Icon = ACTION_ICONS[log.action] || ScrollText
                            return (
                                <div key={log.id} className="flex items-center gap-3 p-4 hover:bg-accent/50 transition-colors">
                                    <span className={`w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 ${ACTION_COLOR[log.action] || 'text-slate-500 bg-slate-500/10'}`}>
                                        <Icon className="w-4 h-4" />
                                    </span>
                                    <div className="min-w-0 flex-1">
                                        <div className="flex items-center gap-2 flex-wrap">
                                            <span className="font-medium text-sm">{log.performed_by_email || 'Sistema'}</span>
                                            <Badge variant="outline" className="text-[10px]">
                                                {ACTION_LABELS[log.action] || log.action}
                                            </Badge>
                                            <span className="text-xs text-muted-foreground">→ {targetLabel(log)}</span>
                                        </div>
                                        {(log.before_value || log.after_value) && (
                                            <div className="flex items-center gap-1.5 mt-1 text-xs text-muted-foreground">
                                                <span className="line-through opacity-70">{log.before_value || '(vacío)'}</span>
                                                <ArrowRight className="w-3 h-3" />
                                                <span className="font-medium text-foreground">{log.after_value || '(vacío)'}</span>
                                            </div>
                                        )}
                                    </div>
                                    <span className="text-xs text-muted-foreground flex-shrink-0">{formatDate(log.created_at)}</span>
                                </div>
                            )
                        })}
                    </div>
                )}

                {totalPages > 1 && (
                    <div className="flex items-center justify-between px-4 py-3 border-t">
                        <span className="text-sm text-muted-foreground">Página {page} de {totalPages}</span>
                        <div className="flex gap-2">
                            <Button variant="outline" size="sm" onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}>
                                <ChevronLeft className="w-4 h-4" />
                            </Button>
                            <Button variant="outline" size="sm" onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages}>
                                <ChevronRight className="w-4 h-4" />
                            </Button>
                        </div>
                    </div>
                )}
            </CardContent>
        </Card>
    )
}
