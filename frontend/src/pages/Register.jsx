import { SignUp } from '@clerk/clerk-react'
import { Link } from 'react-router-dom'
import { ShieldCheck, ArrowLeft } from 'lucide-react'
import { useTheme } from '../hooks/useTheme'

export default function Register() {
    const { isDark } = useTheme()

    return (
        <div className="min-h-screen flex justify-center items-center gradient-bg p-8 relative overflow-hidden">
            {/* Background orbs */}
            <div className="absolute w-72 h-72 bg-purple-500/20 rounded-full blur-3xl top-10 right-20 animate-pulse" />
            <div className="absolute w-96 h-96 bg-blue-500/15 rounded-full blur-3xl bottom-10 left-20 animate-pulse" style={{ animationDelay: '1.5s' }} />

            <div className="relative z-10 w-full max-w-md">
                <div className="text-center mb-8">
                    <div className="w-14 h-14 rounded-xl gradient-primary flex items-center justify-center mx-auto mb-4 shadow-lg shadow-blue-500/30">
                        <ShieldCheck className="w-7 h-7 text-white" />
                    </div>
                    <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-500 to-purple-500 bg-clip-text text-transparent">
                        Crear Cuenta
                    </h1>
                    <p className="text-muted-foreground mt-2">
                        Protege tus sitios web con inteligencia artificial
                    </p>
                </div>

                <div className="glass-strong rounded-2xl p-8">
                    <SignUp
                        routing="hash"
                        signInUrl="/login"
                        appearance={{
                            elements: {
                                rootBox: 'w-full',
                                card: 'bg-transparent shadow-none p-0 w-full',
                                headerTitle: 'hidden',
                                headerSubtitle: 'hidden',
                                socialButtonsBlockButton: isDark
                                    ? 'glass border-white/20 hover:bg-white/10 text-foreground'
                                    : 'bg-white border border-gray-300 hover:bg-gray-50 text-gray-800 shadow-sm',
                                formButtonPrimary: 'gradient-primary border-0 hover:opacity-90 transition-opacity',
                                formFieldInput: isDark
                                    ? 'bg-white/5 border-white/10 text-foreground placeholder:text-muted-foreground focus:border-blue-500 focus:ring-1 focus:ring-blue-500'
                                    : 'bg-white border border-gray-300 text-gray-900 placeholder:text-gray-400 shadow-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20',
                                formFieldLabel: isDark ? 'text-foreground' : 'text-gray-700 font-medium',
                                dividerLine: isDark ? 'bg-white/10' : 'bg-gray-300',
                                dividerText: 'text-muted-foreground',
                                footerActionLink: 'text-blue-500 hover:text-blue-400',
                                formFieldInputShowPasswordButton: isDark ? 'text-white/50 hover:text-white/80' : 'text-gray-500 hover:text-gray-700',
                            },
                        }}
                    />
                </div>

                <p className="text-center mt-6 text-sm text-muted-foreground">
                    <Link to="/login" className="text-blue-500 hover:text-blue-400 font-medium inline-flex items-center gap-1">
                        <ArrowLeft className="w-3 h-3" /> Volver al inicio de sesión
                    </Link>
                </p>
            </div>
        </div>
    )
}
