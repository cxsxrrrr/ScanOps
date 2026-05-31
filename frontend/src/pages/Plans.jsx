import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import api from '../lib/api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { Skeleton } from '@/components/ui/skeleton'
import {
    Sparkles, Check, Crown, Zap, Shield, Globe,
    ScanSearch, FileText, Brain, Headphones, ShieldCheck,
} from 'lucide-react'

const plans = [
    {
        key: 'free', name: 'Free', price: 0, icon: Shield,
        gradient: 'from-slate-500 to-slate-600',
        badgeClass: 'plan-badge-free',
        features: [
            { text: '1 URL registrada',    icon: Globe },
            { text: 'Escaneos básicos',     icon: ScanSearch },
            { text: 'Reportes técnicos',    icon: FileText },
            { text: 'Soporte por email',    icon: Headphones },
        ],
        cta: 'Plan actual',
    },
    {
        key: 'pro', name: 'Pro', price: 10, icon: Zap,
        gradient: 'from-purple-500 to-purple-600',
        badgeClass: 'plan-badge-pro',
        popular: true,
        glow: 'glow-purple',
        features: [
            { text: '5 URLs registradas',   icon: Globe },
            { text: 'Escaneos avanzados',   icon: ScanSearch },
            { text: 'Reportes con IA',      icon: Brain },
            { text: 'Reportes ejecutivos',  icon: FileText },
            { text: 'Soporte prioritario',  icon: Headphones },
        ],
        cta: 'Actualizar a Pro',
    },
    {
        key: 'ultimate', name: 'Ultimate', price: 20, icon: Crown,
        gradient: 'from-amber-500 to-orange-500',
        badgeClass: 'plan-badge-ultimate',
        glow: 'glow-amber',
        features: [
            { text: '10 URLs registradas',      icon: Globe },
            { text: 'Todos los checks',          icon: ScanSearch },
            { text: 'IA avanzada',               icon: Brain },
            { text: 'Reportes premium',          icon: FileText },
            { text: 'Soporte 24/7',              icon: Headphones },
            { text: 'Acceso anticipado',         icon: Sparkles },
        ],
        cta: 'Actualizar a Ultimate',
    },
]

export default function Plans() {
    const [orgData,  setOrgData]  = useState(null)
    const [loading,  setLoading]  = useState(true)
    const [processingPayment, setProcessingPayment] = useState(false)

    useEffect(() => {
        const controller = new AbortController()
        loadOrgData(controller.signal)
        return () => controller.abort()
    }, [])

    async function loadOrgData(signal) {
        try {
            const res = await api.get('/auth/organization/', { signal })
            setOrgData(res.data)
        } catch (err) {
            if (err.code === 'ERR_CANCELED') return
            console.error('Failed to load org data:', err)
        } finally {
            setLoading(false)
        }
    }

    const handleUpgrade = async (planKey) => {
        setProcessingPayment(true)
        try {
            const res = await api.post('/auth/payments/create-checkout-session/', { plan: planKey })
            if (res.data.url) {
                window.location.href = res.data.url
            }
        } catch (error) {
            console.error('Error creating checkout session:', error)
            alert('Hubo un error al iniciar el proceso de pago. Inténtalo de nuevo.')
            setProcessingPayment(false)
        }
    }

    const currentPlan = orgData?.plan || 'free'

    if (loading) return (
        <div className="space-y-8">
            <div className="text-center"><Skeleton className="h-10 w-48 mx-auto mb-3" /><Skeleton className="h-4 w-72 mx-auto" /></div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto">
                {[1,2,3].map(i => <Card key={i}><CardContent className="p-6 space-y-4"><Skeleton className="h-32 w-full rounded-xl" /></CardContent></Card>)}
            </div>
        </div>
    )

    return (
        <div className="space-y-8">
            {/* Header */}
            <div className="text-center">
                <div className="w-14 h-14 rounded-2xl gradient-primary flex items-center justify-center mx-auto mb-4 shadow-lg shadow-blue-500/25">
                    <Sparkles className="w-7 h-7 text-white" />
                </div>
                <h1 className="text-3xl font-extrabold tracking-tight">
                    <span className="bg-gradient-to-r from-blue-600 via-purple-600 to-amber-600 dark:from-blue-500 dark:via-purple-500 dark:to-amber-400 bg-clip-text text-transparent">
                        Elige tu Plan
                    </span>
                </h1>
                <p className="text-muted-foreground mt-2 max-w-lg mx-auto text-sm">
                    Protege tus sitios web con el plan que mejor se adapte a tu negocio.
                </p>
            </div>

            {/* Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto">
                {plans.map((plan, i) => {
                    const isCurrent = plan.key === currentPlan
                    const isUpgrade = plans.findIndex(p => p.key === currentPlan) < i
                    return (
                        <motion.div
                            key={plan.key}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: i * 0.1, duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
                        >
                            <Card className={`relative flex flex-col h-full transition-all duration-300 hover:-translate-y-1 hover:shadow-lg ${
                                plan.popular ? `border-purple-500/30 ${plan.glow}` : ''
                            } ${isCurrent ? 'ring-2 ring-primary/40' : ''}`}
                            >
                                {plan.popular && (
                                    <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                                        <span className="px-4 py-1 rounded-full text-xs font-bold bg-gradient-to-r from-purple-500 to-purple-700 text-white shadow-md shadow-purple-500/20">
                                            Más Popular
                                        </span>
                                    </div>
                                )}
                                {isCurrent && (
                                    <div className="absolute -top-3 right-4">
                                        <span className="px-3 py-1 rounded-full text-xs font-bold gradient-primary text-white shadow-md shadow-blue-500/20">
                                            Tu Plan
                                        </span>
                                    </div>
                                )}

                                <CardHeader className="pb-3 pt-7">
                                    <div className="flex items-center gap-3 mb-4">
                                        <div className={`w-11 h-11 rounded-xl bg-gradient-to-br ${plan.gradient} flex items-center justify-center shadow-md`}>
                                            <plan.icon className="w-5 h-5 text-white" />
                                        </div>
                                        <div>
                                            <CardTitle className="text-lg">{plan.name}</CardTitle>
                                            <span className={`${plan.badgeClass} px-2 py-0.5 rounded-full text-[10px] font-bold`}>
                                                {plan.key.toUpperCase()}
                                            </span>
                                        </div>
                                    </div>
                                    <div className="flex items-baseline gap-1">
                                        <span className="text-4xl font-extrabold tabular-nums">${plan.price}</span>
                                        <span className="text-sm text-muted-foreground">/mes</span>
                                    </div>
                                </CardHeader>

                                <CardContent className="flex-1 flex flex-col space-y-4">
                                    <Separator />
                                    <div className="space-y-2.5 flex-1">
                                        {plan.features.map(({ text, icon: Icon }) => (
                                            <div key={text} className="flex items-center gap-2.5">
                                                <div className={`w-5 h-5 rounded-full bg-gradient-to-br ${plan.gradient} flex items-center justify-center flex-shrink-0`}>
                                                    <Check className="w-3 h-3 text-white" />
                                                </div>
                                                <span className="text-sm text-muted-foreground">{text}</span>
                                            </div>
                                        ))}
                                    </div>

                                    <Button
                                        disabled={isCurrent || processingPayment}
                                        onClick={() => !isCurrent && handleUpgrade(plan.key)}
                                        className={`w-full mt-auto ${
                                            isCurrent ? '' :
                                            isUpgrade ? `bg-gradient-to-r ${plan.gradient} hover:opacity-90 border-0 text-white` :
                                            'variant-outline'
                                        }`}
                                        variant={isCurrent ? 'secondary' : isUpgrade ? 'default' : 'outline'}
                                    >
                                        {isCurrent ? (
                                            <><ShieldCheck className="w-4 h-4" /> Plan Actual</>
                                        ) : processingPayment && isUpgrade ? (
                                            <><span className="animate-spin mr-2">⚪</span> Procesando...</>
                                        ) : isUpgrade ? (
                                            <><Sparkles className="w-4 h-4" /> {plan.cta}</>
                                        ) : (
                                            'Cambiar plan'
                                        )}
                                    </Button>
                                </CardContent>
                            </Card>
                        </motion.div>
                    )
                })}
            </div>

            {/* Footer note */}
            <div className="max-w-2xl mx-auto">
                <Card>
                    <CardContent className="py-5 text-center">
                        <p className="font-semibold text-sm mb-1">¿Necesitas más URLs?</p>
                        <p className="text-xs text-muted-foreground">
                            Para más de 10 URLs, contáctanos para un plan empresarial personalizado.
                        </p>
                    </CardContent>
                </Card>
            </div>
        </div>
    )
}
