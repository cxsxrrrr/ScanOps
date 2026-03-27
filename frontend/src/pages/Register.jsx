import { useState } from 'react'
import { SignUp } from '@clerk/clerk-react'
import { Link } from 'react-router-dom'
import { ShieldCheck, ArrowLeft, ScrollText, Check } from 'lucide-react'

export default function Register() {
    const [termsAccepted, setTermsAccepted] = useState(false)

    return (
        <div className="min-h-screen flex justify-center items-center gradient-bg p-8 relative overflow-hidden">
            {/* Background orbs */}
            <div className="absolute w-72 h-72 bg-purple-500/20 rounded-full blur-3xl top-10 right-20 animate-float" />
            <div className="absolute w-96 h-96 bg-blue-500/15 rounded-full blur-3xl bottom-10 left-20 animate-float-slow" />
            <div className="absolute w-64 h-64 bg-cyan-500/10 rounded-full blur-3xl top-1/2 left-1/2 -translate-x-1/2 animate-float-delayed" />

            <div className="relative z-10 w-full max-w-lg">
                <div className="text-center mb-8">
                    <div className="w-14 h-14 rounded-xl gradient-primary flex items-center justify-center mx-auto mb-4 shadow-lg shadow-blue-500/30">
                        <ShieldCheck className="w-7 h-7 text-white" />
                    </div>
                    <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                        Crear Cuenta en ScanOps
                    </h1>
                    <p className="text-muted-foreground mt-2">
                        Protege tus sitios web con escaneos de seguridad inteligentes
                    </p>
                </div>

                {/* Terms and Conditions checkbox */}
                <div className="glass-card rounded-xl p-4 mb-4">
                    <label
                        htmlFor="terms-checkbox"
                        className="flex items-start gap-3 cursor-pointer group"
                    >
                        <div className="pt-0.5">
                            <button
                                type="button"
                                id="terms-checkbox"
                                role="checkbox"
                                aria-checked={termsAccepted}
                                onClick={() => setTermsAccepted(!termsAccepted)}
                                className={`w-5 h-5 rounded flex items-center justify-center border transition-all duration-200 flex-shrink-0 ${
                                    termsAccepted
                                        ? 'gradient-primary border-transparent shadow-lg shadow-blue-500/25'
                                        : 'border-white/20 bg-white/5 hover:border-white/40'
                                }`}
                            >
                                {termsAccepted && <Check className="w-3 h-3 text-white" />}
                            </button>
                        </div>
                        <div className="text-sm">
                            <span className="text-muted-foreground">
                                He leído y acepto los{' '}
                            </span>
                            <Link
                                to="/terms"
                                className="text-blue-400 hover:text-blue-300 font-medium underline underline-offset-2"
                                onClick={(e) => e.stopPropagation()}
                            >
                                Términos y Condiciones
                            </Link>
                            <span className="text-muted-foreground">
                                {' '}de uso de ScanOps, incluyendo las políticas de uso
                                responsable de la herramienta de ciberseguridad.
                            </span>
                        </div>
                    </label>
                </div>

                {/* Clerk SignUp form - blocked if terms not accepted */}
                <div className="relative">
                    {!termsAccepted && (
                        <div className="absolute inset-0 z-20 rounded-2xl bg-black/40 backdrop-blur-[2px] flex items-center justify-center cursor-not-allowed">
                            <div className="glass-strong rounded-xl px-5 py-3 flex items-center gap-3 shadow-2xl">
                                <ScrollText className="w-5 h-5 text-amber-400" />
                                <span className="text-sm font-medium text-foreground">
                                    Acepta los términos para continuar
                                </span>
                            </div>
                        </div>
                    )}
                    <div className={`glass-strong rounded-2xl p-10 transition-opacity duration-300 ${
                        !termsAccepted ? 'opacity-60' : ''
                    }`}>
                        <SignUp
                            routing="hash"
                            signInUrl="/login"
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
