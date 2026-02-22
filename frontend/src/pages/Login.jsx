import { SignIn } from '@clerk/clerk-react'
import { Link } from 'react-router-dom'
import { ShieldCheck, ArrowRight } from 'lucide-react'

export default function Login() {
    return (
        <div className="min-h-screen flex gradient-bg">
            {/* Left panel — branding */}
            <div className="hidden lg:flex lg:w-1/2 flex-col justify-center items-center p-12 relative overflow-hidden">
                {/* Animated background orbs */}
                <div className="absolute w-72 h-72 bg-blue-500/20 rounded-full blur-3xl top-20 left-10 animate-pulse" />
                <div className="absolute w-96 h-96 bg-purple-500/15 rounded-full blur-3xl bottom-20 right-10 animate-pulse" style={{ animationDelay: '1s' }} />

                <div className="relative z-10 max-w-lg text-center">
                    <div className="w-20 h-20 rounded-2xl gradient-primary flex items-center justify-center mx-auto mb-8 shadow-xl shadow-blue-500/30">
                        <ShieldCheck className="w-10 h-10 text-white" />
                    </div>
                    <h1 className="text-4xl font-extrabold mb-4 bg-gradient-to-r from-blue-400 via-purple-400 to-cyan-400 bg-clip-text text-transparent">
                        Auditoría Web Automatizada
                    </h1>
                    <p className="text-lg text-muted-foreground mb-8">
                        Protege tu negocio con escaneos de seguridad inteligentes, reportes con IA y monitoreo continuo.
                    </p>
                    <div className="grid grid-cols-3 gap-4 text-center">
                        {[
                            { num: '7+', label: 'Checks de seguridad' },
                            { num: 'IA', label: 'Reportes inteligentes' },
                            { num: '24/7', label: 'Monitoreo continuo' },
                        ].map((stat) => (
                            <div key={stat.label} className="glass rounded-xl p-4">
                                <div className="text-2xl font-bold text-blue-400">{stat.num}</div>
                                <div className="text-xs text-muted-foreground mt-1">{stat.label}</div>
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
                        AuditWeb
                    </h1>
                </div>

                <div className="w-full max-w-md">
                    <div className="glass-strong rounded-2xl p-8">
                        <h2 className="text-2xl font-bold text-center mb-2">Bienvenido</h2>
                        <p className="text-muted-foreground text-center mb-6">
                            Inicia sesión para acceder a tu panel
                        </p>
                        <SignIn
                            routing="hash"
                            signUpUrl="/register"
                            appearance={{
                                elements: {
                                    rootBox: 'w-full',
                                    card: 'bg-transparent shadow-none p-0 w-full',
                                    headerTitle: 'hidden',
                                    headerSubtitle: 'hidden',
                                    socialButtonsBlockButton: 'glass border-white/20 hover:bg-white/10 text-foreground',
                                    formButtonPrimary: 'gradient-primary border-0 hover:opacity-90 transition-opacity',
                                    formFieldInput: 'bg-white/5 border-white/10 text-foreground placeholder:text-muted-foreground',
                                    formFieldLabel: 'text-foreground',
                                    dividerLine: 'bg-white/10',
                                    dividerText: 'text-muted-foreground',
                                    footerActionLink: 'text-blue-400 hover:text-blue-300',
                                    identityPreviewEditButton: 'text-blue-400',
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
                </div>
            </div>
        </div>
    )
}
