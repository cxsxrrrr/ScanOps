import { SignIn } from '@clerk/clerk-react'
import { Link } from 'react-router-dom'
import { ShieldCheck, ArrowRight, Scan, Zap, Brain, Lock, ScrollText } from 'lucide-react'

export default function Login() {
    return (
        <div className="min-h-screen flex gradient-bg">
            {/* Left panel — branding */}
            <div className="hidden lg:flex lg:w-1/2 flex-col justify-center items-center p-12 relative overflow-hidden">
                {/* Animated background orbs */}
                <div className="absolute w-72 h-72 bg-blue-500/20 rounded-full blur-3xl top-20 left-10 animate-float" />
                <div className="absolute w-96 h-96 bg-purple-500/15 rounded-full blur-3xl bottom-20 right-10 animate-float-slow" />
                <div className="absolute w-64 h-64 bg-cyan-500/10 rounded-full blur-3xl top-1/2 left-1/2 animate-float-delayed" />

                {/* Grid pattern overlay */}
                <div className="absolute inset-0 opacity-[0.03]"
                    style={{
                        backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='1'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
                    }}
                />

                <div className="relative z-10 max-w-lg text-center">
                    <div className="w-20 h-20 rounded-2xl gradient-primary flex items-center justify-center mx-auto mb-8 shadow-xl shadow-blue-500/30 animate-pulse-glow">
                        <ShieldCheck className="w-10 h-10 text-white" />
                    </div>
                    <h1 className="text-4xl font-extrabold mb-4 bg-gradient-to-r from-blue-400 via-purple-400 to-cyan-400 bg-clip-text text-transparent animate-gradient-text bg-[length:200%_auto]">
                        ScanOps
                    </h1>
                    <p className="text-xl text-foreground/80 font-medium mb-2">
                        Ciberseguridad Inteligente para PYMES
                    </p>
                    <p className="text-muted-foreground mb-10">
                        Escanea, analiza y protege tus sitios web con tecnología de inteligencia artificial.
                    </p>

                    <div className="grid grid-cols-2 gap-4">
                        {[
                            { icon: Scan, label: 'Escaneos Automatizados', desc: 'Detecta vulnerabilidades en minutos' },
                            { icon: Brain, label: 'Reportes con IA', desc: 'Análisis ejecutivos generados por IA' },
                            { icon: Zap, label: 'Monitoreo Continuo', desc: 'Protección 24/7 de tus activos' },
                            { icon: Lock, label: '7+ Checks de Seguridad', desc: 'Headers, SSL, Cookies y más' },
                        ].map((feature) => (
                            <div key={feature.label} className="glass-card rounded-xl p-4 text-left hover:scale-[1.02] transition-transform">
                                <feature.icon className="w-6 h-6 text-blue-400 mb-2" />
                                <div className="text-sm font-semibold">{feature.label}</div>
                                <div className="text-xs text-muted-foreground mt-0.5">{feature.desc}</div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Right panel — login form */}
            <div className="flex-1 flex flex-col justify-center items-center p-8">
                <div className="lg:hidden mb-8 text-center">
                    <div className="w-14 h-14 rounded-xl gradient-primary flex items-center justify-center mx-auto mb-4">
                        <ShieldCheck className="w-7 h-7 text-white" />
                    </div>
                    <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                        ScanOps
                    </h1>
                </div>

                <div className="w-full max-w-lg">
                    <div className="glass-strong rounded-2xl p-10">
                        <h2 className="text-2xl font-bold text-center mb-2">Bienvenido de vuelta</h2>
                        <p className="text-muted-foreground text-center mb-8 text-sm">
                            Inicia sesión para acceder a tu panel de seguridad
                        </p>
                        <SignIn
                            routing="hash"
                            signUpUrl="/register"
                            appearance={{
                                elements: {
                                    rootBox: 'w-full',
                                    card: 'bg-transparent shadow-none p-0 w-full [&>div]:space-y-4',
                                    headerTitle: 'hidden',
                                    headerSubtitle: 'hidden',
                                    footer: '!mt-6 !pt-4 !border-t !border-white/5',
                                },
                            }}
                        />
                    </div>

                    <p className="text-center mt-6 text-sm text-muted-foreground">
                        ¿No tienes cuenta?{' '}
                        <Link to="/register" className="text-blue-400 hover:text-blue-300 font-medium inline-flex items-center gap-1">
                            Regístrate <ArrowRight className="w-3 h-3" />
                        </Link>
                    </p>

                    {/* Terms link */}
                    <p className="text-center mt-3 text-xs text-muted-foreground">
                        <Link to="/terms" className="hover:text-foreground transition-colors inline-flex items-center gap-1">
                            <ScrollText className="w-3 h-3" />
                            Términos y Condiciones
                        </Link>
                    </p>
                </div>
            </div>
        </div>
    )
}
