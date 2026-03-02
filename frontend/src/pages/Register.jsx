import { SignUp } from '@clerk/clerk-react'
import { Link } from 'react-router-dom'
import { ShieldCheck, ArrowLeft } from 'lucide-react'
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

export default function Register() {
    const { isDark } = useTheme()

    return (
        <div className="min-h-screen flex justify-center items-center gradient-bg p-6 sm:p-8 relative overflow-hidden">
            {/* Background orbs */}
            <div className="absolute w-72 h-72 bg-purple-500/20 rounded-full blur-3xl top-10 right-20 animate-pulse" />
            <div className="absolute w-96 h-96 bg-blue-500/15 rounded-full blur-3xl bottom-10 left-20 animate-pulse" style={{ animationDelay: '1.5s' }} />

            <div className="relative z-10 w-full max-w-[420px]">
                <div className="text-center mb-8">
                    <div className="w-14 h-14 rounded-xl gradient-primary flex items-center justify-center mx-auto mb-4 shadow-lg shadow-blue-500/25">
                        <ShieldCheck className="w-7 h-7 text-white" />
                    </div>
                    <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-500 to-purple-500 bg-clip-text text-transparent">
                        Crear Cuenta
                    </h1>
                    <p className="text-muted-foreground text-sm mt-2">
                        Protege tus sitios web con inteligencia artificial
                    </p>
                </div>

                <div className="glass-strong rounded-2xl p-6 sm:p-8 login-card-enter overflow-hidden">
                    <SignUp
                        routing="hash"
                        signInUrl="/login"
                        appearance={clerkAppearance(isDark)}
                    />
                </div>

                <p className="text-center mt-6 text-sm text-muted-foreground">
                    <Link
                        to="/login"
                        className="text-blue-500 hover:text-blue-400 font-semibold inline-flex items-center gap-1 transition-colors"
                    >
                        <ArrowLeft className="w-3 h-3" /> Volver al inicio de sesión
                    </Link>
                </p>
            </div>
        </div>
    )
}

