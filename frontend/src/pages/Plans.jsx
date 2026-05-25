import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useUser } from '@clerk/clerk-react'
import api from '../lib/api'
import {
    Sparkles, Check, Crown, Zap, Shield, Globe,
    ScanSearch, FileText, Brain, Headphones, ArrowRight,
    Loader2, ShieldCheck,
} from 'lucide-react'

const plans = [
    {
        key: 'free',
        name: 'Free',
        price: 0,
        icon: Shield,
        gradient: 'from-gray-500 to-gray-600',
        badgeClass: 'plan-badge-free',
        glowClass: '',
        borderClass: 'border-border',
        features: [
            { text: '1 URL registrada', icon: Globe },
            { text: 'Escaneos básicos', icon: ScanSearch },
            { text: 'Reportes técnicos', icon: FileText },
            { text: 'Soporte por email', icon: Headphones },
        ],
        cta: 'Plan actual',
    },
    {
        key: 'pro',
        name: 'Pro',
        price: 10,
        icon: Zap,
        gradient: 'from-purple-500 to-purple-600',
        badgeClass: 'plan-badge-pro',
        glowClass: 'glow-purple',
        borderClass: 'border-purple-500/30',
        popular: true,
        features: [
            { text: '5 URLs registradas', icon: Globe },
            { text: 'Escaneos avanzados', icon: ScanSearch },
            { text: 'Reportes con IA', icon: Brain },
            { text: 'Reportes ejecutivos', icon: FileText },
            { text: 'Soporte prioritario', icon: Headphones },
        ],
        cta: 'Actualizar a Pro',
    },
    {
        key: 'ultimate',
        name: 'Ultimate',
        price: 20,
        icon: Crown,
        gradient: 'from-amber-500 to-orange-500',
        badgeClass: 'plan-badge-ultimate',
        glowClass: 'glow-amber',
        borderClass: 'border-amber-500/30',
        features: [
            { text: '10 URLs registradas', icon: Globe },
            { text: 'Todos los checks', icon: ScanSearch },
            { text: 'Reportes con IA avanzada', icon: Brain },
            { text: 'Reportes ejecutivos premium', icon: FileText },
            { text: 'Soporte premium 24/7', icon: Headphones },
            { text: 'Acceso anticipado a features', icon: Sparkles },
        ],
        cta: 'Actualizar a Ultimate',
    },
]

export default function Plans() {
    const { user } = useUser()
    const [orgData, setOrgData] = useState(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => { loadOrgData() }, [])

    async function loadOrgData() {
        try {
            const res = await api.get('/auth/organization/')
            setOrgData(res.data)
        } catch (err) {
            console.error('Failed to load org data:', err)
        } finally {
            setLoading(false)
        }
    }

    const currentPlan = orgData?.plan || 'free'

    return (
        <div className="space-y-8">
            {/* Header */}
            <div className="text-center">
                <div className="w-14 h-14 rounded-xl gradient-primary flex items-center justify-center mx-auto mb-4 shadow-lg shadow-blue-500/30">
                    <Sparkles className="w-7 h-7 text-white" />
                </div>
                <h1 className="text-3xl font-extrabold">
                    <span className="bg-gradient-to-r from-blue-400 via-purple-400 to-amber-400 bg-clip-text text-transparent">
                        Elige tu Plan
                    </span>
                </h1>
                <p className="text-muted-foreground mt-2 max-w-lg mx-auto">
                    Protege tus sitios web con el plan que mejor se adapte a tu negocio.
                    Actualiza en cualquier momento.
                </p>
            </div>

            {/* Plan cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto">
                {plans.map((plan, index) => {
                    const isCurrent = plan.key === currentPlan
                    const isUpgrade = plans.findIndex(p => p.key === currentPlan) < index

                    return (
                        <div
                            key={plan.key}
                            className={`relative glass-card rounded-2xl p-6 flex flex-col transition-all duration-300 hover:scale-[1.02] ${
                                plan.popular ? `${plan.glowClass} ${plan.borderClass}` : ''
                            } ${isCurrent ? 'ring-2 ring-blue-500/50' : ''}`}
                        >
                            {/* Popular badge */}
                            {plan.popular && (
                                <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                                    <span className="px-4 py-1 rounded-full text-xs font-bold gradient-pro text-white shadow-lg shadow-purple-500/25">
                                        Más Popular
                                    </span>
                                </div>
                            )}

                            {/* Current badge */}
                            {isCurrent && (
                                <div className="absolute -top-3 right-4">
                                    <span className="px-3 py-1 rounded-full text-xs font-bold gradient-primary text-white shadow-lg shadow-blue-500/25">
                                        Tu Plan
                                    </span>
                                </div>
                            )}

                            {/* Plan icon & name */}
                            <div className="flex items-center gap-3 mb-4 mt-2">
                                <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${plan.gradient} flex items-center justify-center shadow-lg`}>
                                    <plan.icon className="w-6 h-6 text-white" />
                                </div>
                                <div>
                                    <h3 className="text-xl font-bold">{plan.name}</h3>
                                    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${plan.badgeClass}`}>
                                        {plan.key.toUpperCase()}
                                    </span>
                                </div>
                            </div>

                            {/* Price */}
                            <div className="mb-6">
                                <div className="flex items-baseline gap-1">
                                    <span className="text-4xl font-extrabold">
                                        ${plan.price}
                                    </span>
                                    <span className="text-sm text-muted-foreground">/mes</span>
                                </div>
                            </div>

                            {/* Features */}
                            <div className="flex-1 space-y-3 mb-6">
                                {plan.features.map((feature) => (
                                    <div key={feature.text} className="flex items-center gap-3">
                                        <div className={`w-5 h-5 rounded-full bg-gradient-to-br ${plan.gradient} flex items-center justify-center flex-shrink-0`}>
                                            <Check className="w-3 h-3 text-white" />
                                        </div>
                                        <span className="text-sm text-muted-foreground">{feature.text}</span>
                                    </div>
                                ))}
                            </div>

                            {/* CTA */}
                            <button
                                disabled={isCurrent}
                                className={`w-full py-3 rounded-xl font-semibold text-sm flex items-center justify-center gap-2 transition-all duration-200 ${
                                    isCurrent
                                        ? 'bg-foreground/5 text-muted-foreground cursor-not-allowed border border-border'
                                        : isUpgrade
                                            ? `bg-gradient-to-r ${plan.gradient} text-white hover:opacity-90 shadow-lg`
                                            : 'glass hover:bg-foreground/10 text-foreground'
                                }`}
                            >
                                {isCurrent ? (
                                    <>
                                        <ShieldCheck className="w-4 h-4" />
                                        Plan Actual
                                    </>
                                ) : isUpgrade ? (
                                    <>
                                        <Sparkles className="w-4 h-4" />
                                        {plan.cta}
                                    </>
                                ) : (
                                    'Cambiar plan'
                                )}
                            </button>
                        </div>
                    )
                })}
            </div>

            {/* FAQ / Note */}
            <div className="max-w-2xl mx-auto text-center">
                <div className="glass-card rounded-xl p-6">
                    <h3 className="font-semibold mb-2">¿Necesitas más URLs?</h3>
                    <p className="text-sm text-muted-foreground">
                        Si necesitas monitorear más de 10 URLs, contáctanos para un
                        plan empresarial personalizado.
                    </p>
                </div>
            </div>
        </div>
    )
}
