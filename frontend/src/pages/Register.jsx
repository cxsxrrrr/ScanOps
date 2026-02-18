import { SignUp } from '@clerk/clerk-react'
import { Link } from 'react-router-dom'
import { ShieldCheck, ArrowLeft } from 'lucide-react'

export default function Register() {
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
                    <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
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
                                socialButtonsBlockButton: 'glass border-white/20 hover:bg-white/10 text-foreground',
                                formButtonPrimary: 'gradient-primary border-0 hover:opacity-90 transition-opacity',
                                formFieldInput: 'bg-white/5 border-white/10 text-foreground placeholder:text-muted-foreground',
                                formFieldLabel: 'text-foreground',
                                dividerLine: 'bg-white/10',
                                dividerText: 'text-muted-foreground',
                                footerActionLink: 'text-blue-400 hover:text-blue-300',
                            },
                        }}
                    />
                </div>

                <p className="text-center mt-6 text-sm text-muted-foreground">
                    <Link to="/login" className="text-blue-400 hover:text-blue-300 font-medium inline-flex items-center gap-1">
                        <ArrowLeft className="w-3 h-3" /> Volver al inicio de sesión
                    </Link>
                </p>
            </div>
        </div>
    )
}
