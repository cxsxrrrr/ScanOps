import { SignIn } from '@clerk/clerk-react'
import { Link } from 'react-router-dom'
import { ShieldCheck, FileText } from 'lucide-react'
import { useTheme } from '../hooks/useTheme'
import { useState } from 'react'
import TermsModal from '../components/TermsModal'

/* ── Shared Clerk appearance tokens ── */
const clerkAppearance = (isDark) => ({
    elements: {
        rootBox: 'w-full',
        card: 'bg-transparent shadow-none p-0 w-full',
        headerTitle: 'hidden',
        headerSubtitle: 'hidden',

        /* Social buttons */
        socialButtonsBlockButton: isDark
            ? 'bg-white/5 border border-white/10 text-foreground hover:bg-white/10 transition-all font-medium py-3'
            : 'bg-white border border-gray-200 text-gray-900 hover:bg-gray-50 transition-all font-medium py-3',
        socialButtonsBlockButtonText: 'font-medium',

        /* Primary CTA */
        formButtonPrimary: isDark
            ? 'bg-white text-black hover:bg-gray-200 border-0 shadow-none font-semibold transition-colors py-3'
            : 'bg-black text-white hover:bg-gray-800 border-0 shadow-none font-semibold transition-colors py-3',

        /* Inputs */
        formFieldInput: isDark
            ? 'bg-transparent border-white/10 text-foreground placeholder:text-muted-foreground focus:border-white focus:ring-0 transition-colors py-3'
            : 'bg-transparent border-gray-300 text-gray-900 placeholder:text-gray-400 focus:border-black focus:ring-0 transition-colors py-3',

        /* Labels */
        formFieldLabel: isDark
            ? 'text-foreground font-medium'
            : 'text-gray-900 font-medium',

        /* Divider */
        dividerLine: isDark ? 'bg-white/10' : 'bg-gray-200',
        dividerText: isDark ? 'text-muted-foreground' : 'text-gray-500',

        /* Footer links */
        footerActionLink: 'text-primary hover:text-primary/80 font-medium transition-colors',
        footerActionText: isDark ? 'text-muted-foreground' : 'text-gray-500',

        /* Identity preview (email step) */
        identityPreview: isDark
            ? 'bg-white/5 border-white/10'
            : 'bg-gray-50 border border-gray-200',
        identityPreviewEditButton: 'text-primary hover:text-primary/80',

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
    const [isModalOpen, setIsModalOpen] = useState(false)
    const [termsAccepted, setTermsAccepted] = useState(false)

    return (
        <div className="min-h-screen flex w-full">
            {/* Left panel — login form */}
            <div className={`flex-1 lg:w-1/2 flex flex-col justify-center items-center p-8 relative ${isDark ? 'bg-[#0a0a0a]' : 'bg-white'}`}>
                {/* Language / Theme toggle placeholder (Optional top right alignment in left panel) */}
                <div className="absolute top-8 right-8 hidden sm:block">
                    {/* Could place a language switcher here like in the image */}
                </div>

                <div className="w-full max-w-[400px]">
                    {/* Logo */}
                    <div className="flex items-center gap-2 mb-10">
                        <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
                            <ShieldCheck className="w-5 h-5 text-white" />
                        </div>
                        <span className="text-xl font-bold tracking-tight">AuditWeb</span>
                    </div>

                    {/* Welcome Text */}
                    <h1 className="text-3xl font-semibold mb-2">Bienvenido!</h1>
                    <p className="text-muted-foreground mb-8 text-sm">
                        Inicia sesión en AuditWeb para continuar.
                    </p>

                    {/* Clerk SignIn Component with Verification Overlay */}
                    <div className="mb-6 relative">
                        {!termsAccepted && (
                            <div className="absolute inset-0 z-10 bg-background/40 backdrop-blur-[3px] rounded-xl flex flex-col items-center justify-center border border-white/5">
                                <div className="bg-card border border-border p-6 rounded-xl shadow-2xl text-center max-w-[85%] animate-in zoom-in-95 duration-300">
                                    <div className="w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-3">
                                        <FileText className="w-6 h-6 text-primary" />
                                    </div>
                                    <h3 className="text-base font-semibold text-foreground mb-2">Términos y Condiciones</h3>
                                    <p className="text-xs text-muted-foreground mb-4 leading-relaxed">
                                        Por favor, lee y acepta nuestros términos de servicio y políticas de privacidad para acceder a la plataforma.
                                    </p>
                                    <button
                                        onClick={() => setIsModalOpen(true)}
                                        className="w-full bg-primary text-white text-sm font-medium px-4 py-2.5 rounded-lg hover:bg-primary/90 transition-all shadow-lg shadow-primary/25"
                                    >
                                        Revisar y Aceptar
                                    </button>
                                </div>
                            </div>
                        )}

                        <div className={`transition-all duration-500 ${!termsAccepted ? 'opacity-30 pointer-events-none select-none blur-[2px]' : ''}`}>
                            <SignIn
                                routing="hash"
                                signUpUrl="/register"
                                appearance={clerkAppearance(isDark)}
                            />
                        </div>
                    </div>

                    {/* Terms and conditions text */}
                    <div className="mt-8 text-center border-t border-border pt-6">
                        <p className="text-xs text-muted-foreground leading-relaxed">
                            Al iniciar sesión o crear una cuenta, confirmas que has leído y aceptado nuestros{' '}
                            <button onClick={() => setIsModalOpen(true)} className="underline hover:text-foreground transition-colors">
                                Términos y Condiciones
                            </button>{' '}
                            y nuestra{' '}
                            <button onClick={() => setIsModalOpen(true)} className="underline hover:text-foreground transition-colors">
                                Política de Privacidad
                            </button>.
                        </p>
                    </div>
                </div>
            </div>

            {/* Right panel — visual/branding */}
            <div className="hidden lg:flex lg:w-1/2 bg-[#09090b] text-white flex-col justify-center relative overflow-hidden">
                {/* Background glow effects */}
                <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-primary/20 rounded-full blur-[100px] pointer-events-none" />
                <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-purple-500/20 rounded-full blur-[100px] pointer-events-none" />

                <div className="relative z-10 w-full max-w-lg mx-auto px-12 flex flex-col items-center">
                    {/* Text block resembling the image */}
                    <div className="text-center mb-12">
                        <h2 className="text-4xl sm:text-5xl font-medium tracking-tight leading-[1.1] mb-6">
                            +10,000 auditorías.<br />
                            <span className="text-white/60">Reportes con IA.</span>
                        </h2>

                        {/* Join Now Badge */}
                        <div className="inline-flex items-center gap-2 bg-gradient-to-r from-purple-500/20 to-primary/20 border border-purple-500/30 px-4 py-2 rounded-full backdrop-blur-md">
                            <span className="text-sm font-medium text-purple-200">Únete ahora</span>
                            <div className="w-1.5 h-1.5 rounded-full bg-purple-400 animate-pulse"></div>
                        </div>
                    </div>

                    {/* 3D-like graphic block resembling the image */}
                    <div className="relative w-72 h-72">
                        {/* Orbit rings */}
                        <div className="absolute inset-[-20%] border border-white/5 rounded-[100%] rotate-x-65 rotate-z-45"></div>
                        <div className="absolute inset-[-40%] border border-white/5 rounded-[100%] rotate-x-65 rotate-z-45"></div>

                        {/* Center cube/shield representation */}
                        <div className="absolute inset-0 flex items-center justify-center">
                            <div className="relative w-40 h-56 bg-gradient-to-b from-white/10 to-transparent border border-white/10 rounded-2xl backdrop-blur-xl flex flex-col items-center justify-center shadow-2xl shadow-primary/20 overflow-hidden transform -rotate-6 transition-transform hover:rotate-0 duration-500">
                                <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-white/50 to-transparent"></div>
                                <ShieldCheck className="w-16 h-16 text-primary mb-4 opacity-90" />
                                <div className="h-2 w-16 bg-white/10 rounded-full mb-2"></div>
                                <div className="h-2 w-10 bg-white/10 rounded-full"></div>

                                {/* Scanning line animation */}
                                <div className="absolute top-0 left-0 w-full h-1 bg-primary/50 blur-[2px] scan-pulse"></div>
                            </div>
                        </div>

                        {/* Decorator dots */}
                        <div className="absolute top-[10%] left-[20%] w-2 h-2 bg-primary rounded-full shadow-[0_0_10px_rgba(59,130,246,0.8)]"></div>
                        <div className="absolute bottom-[20%] right-[10%] w-2 h-2 bg-purple-500 rounded-full shadow-[0_0_10px_rgba(168,85,247,0.8)]"></div>
                    </div>
                </div>
            </div>

            <TermsModal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                onAccept={() => {
                    setTermsAccepted(true)
                    setIsModalOpen(false)
                }}
            />
        </div>
    )
}
