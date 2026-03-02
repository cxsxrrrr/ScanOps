import { SignIn } from '@clerk/clerk-react'
import { Link } from 'react-router-dom'
import { ShieldCheck, ArrowRight } from 'lucide-react'
import { useTheme } from '../hooks/useTheme'

/* ── Shared Clerk appearance tokens ── */
const clerkAppearance = (isDark) => ({
    elements: {
        rootBox: 'w-full',
        card: 'bg-transparent shadow-none p-0 w-full',
        headerTitle: 'hidden',
        headerSubtitle: 'hidden',

        /* Social buttons */
        socialButtonsBlockButton: isDark
            ? 'glass border-white/20 text-foreground'
            : 'bg-white border border-gray-200 text-gray-700 shadow-sm',
        socialButtonsBlockButtonText: 'font-medium',

        /* Primary CTA */
        formButtonPrimary:
            'gradient-primary border-0 shadow-lg shadow-blue-500/25',

        /* Inputs */
        formFieldInput: isDark
            ? 'bg-white/5 border-white/10 text-foreground placeholder:text-muted-foreground focus:border-blue-500 focus:ring-1 focus:ring-blue-500/40'
            : 'bg-gray-50 border border-gray-200 text-gray-900 placeholder:text-gray-400 focus:bg-white focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20',

        /* Labels */
        formFieldLabel: isDark
            ? 'text-foreground font-semibold'
            : 'text-gray-700 font-semibold',

        /* Divider */
        dividerLine: isDark ? 'bg-white/10' : 'bg-gray-200',
        dividerText: 'text-muted-foreground',

        /* Footer links */
        footerActionLink: 'text-blue-500 hover:text-blue-400 font-semibold',
        footerActionText: isDark ? 'text-muted-foreground' : 'text-gray-500',

        /* Identity preview (email step) */
        identityPreview: isDark
            ? 'bg-white/5 border-white/10'
            : 'bg-gray-50 border border-gray-200',
        identityPreviewEditButton: 'text-blue-500 hover:text-blue-400',

        /* Password toggle */
        formFieldInputShowPasswordButton: isDark
            ? 'text-white/50 hover:text-white/80'
            : 'text-gray-400 hover:text-gray-600',

        /* Alert / error messages */
        alert: isDark
            ? 'bg-red-500/10 border-red-500/20 text-red-400'
            : 'bg-red-50 border border-red-200 text-red-600',

        /* Form field error */
        formFieldErrorText: 'text-red-500 text-xs mt-1',
    },
})

export default function Login() {
    const { isDark } = useTheme()

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
                    <h1 className="text-4xl font-extrabold mb-4 bg-gradient-to-r from-blue-500 via-purple-500 to-cyan-500 bg-clip-text text-transparent">
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
                                <div className="text-2xl font-bold text-blue-500">{stat.num}</div>
                                <div className="text-xs text-muted-foreground mt-1">{stat.label}</div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Right panel — login form */}
            <div className="flex-1 flex flex-col justify-center items-center p-6 sm:p-8">
                {/* Mobile branding */}
                <div className="lg:hidden mb-8 text-center">
                    <div className="w-14 h-14 rounded-xl gradient-primary flex items-center justify-center mx-auto mb-4 shadow-lg shadow-blue-500/25">
                        <ShieldCheck className="w-7 h-7 text-white" />
                    </div>
                    <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-500 to-purple-500 bg-clip-text text-transparent">
                        AuditWeb
                    </h1>
                </div>

                <div className="w-full max-w-[420px]">
                    <div className="glass-strong rounded-2xl p-6 sm:p-8 login-card-enter overflow-hidden">
                        <h2 className="text-2xl font-bold text-center mb-1">Bienvenido</h2>
                        <p className="text-muted-foreground text-center text-sm mb-6">
                            Inicia sesión para acceder a tu panel
                        </p>

                        <SignIn
                            routing="hash"
                            signUpUrl="/register"
                            appearance={clerkAppearance(isDark)}
                        />
                    </div>

                    <p className="text-center mt-6 text-sm text-muted-foreground">
                        ¿No tienes cuenta?{' '}
                        <Link
                            to="/register"
                            className="text-blue-500 hover:text-blue-400 font-semibold inline-flex items-center gap-1 transition-colors"
                        >
                            Regístrate <ArrowRight className="w-3 h-3" />
                        </Link>
                    </p>
                </div>
            </div>
        </div>
    )
}

