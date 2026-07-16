import { useState } from 'react'
import { X, ShieldCheck } from 'lucide-react'

export default function TermsModal({ isOpen, onClose, onAccept }) {
    const [isChecked, setIsChecked] = useState(false)

    if (!isOpen) return null

    const handleAccept = () => {
        if (isChecked) {
            onAccept()
            onClose()
        }
    }

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-in fade-in duration-200">
            <div className="bg-background border border-border w-full max-w-2xl max-h-[90vh] rounded-2xl shadow-2xl flex flex-col overflow-hidden relative">

                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b border-border bg-card">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                            <ShieldCheck className="w-6 h-6 text-primary" />
                        </div>
                        <h2 className="text-xl font-bold text-foreground">Términos y Condiciones</h2>
                    </div>
                    <button
                        onClick={onClose}
                        className="text-muted-foreground hover:text-foreground transition-colors p-2 rounded-full hover:bg-muted"
                    >
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-6 text-sm text-muted-foreground space-y-4 custom-scrollbar">
                    <h3 className="text-foreground font-semibold text-base">1. Introducción</h3>
                    <p>
                        Bienvenido a AuditWeb. Al acceder y utilizar nuestros servicios de auditoría web automatizada,
                        usted acepta estar sujeto a los siguientes términos y condiciones. Lea detenidamente este documento
                        antes de utilizar nuestra plataforma.
                    </p>

                    <h3 className="text-foreground font-semibold text-base">2. Uso del Servicio</h3>
                    <p>
                        Nuestra plataforma ofrece herramientas de análisis y escaneo de vulnerabilidades mediante inteligencia
                        artificial. Usted se compromete a usar estos servicios únicamente en aplicaciones web y dominios sobre
                        los cuales tenga propiedad o autorización explícita para auditar.
                    </p>

                    <h3 className="text-foreground font-semibold text-base">3. Privacidad y Datos</h3>
                    <p>
                        Recopilamos información estrictamente necesaria para la prestación del servicio. Sus datos de
                        escaneo y reportes son confidenciales y están protegidos mediante cifrado de extremo a extremo.
                        No compartiremos su información con terceros sin su consentimiento previo.
                    </p>

                    <h3 className="text-foreground font-semibold text-base">4. Limitación de Responsabilidad</h3>
                    <p>
                        Los reportes generados por AuditWeb son orientativos. Aunque utilizamos tecnología de vanguardia y AI
                        para detectar vulnerabilidades, no garantizamos que nuestros escaneos identifiquen el 100% de las
                        fallas de seguridad. Usted es responsable de la protección integral de su infraestructura.
                    </p>

                    <h3 className="text-foreground font-semibold text-base">5. Modificaciones</h3>
                    <p>
                        Nos reservamos el derecho de modificar estos términos en cualquier momento. Le notificaremos sobre
                        cambios significativos a través de su correo electrónico o un aviso destacado en nuestra plataforma.
                    </p>

                    <hr className="border-border my-6" />

                    <p className="text-xs">
                        Última actualización: {new Date().toLocaleDateString('es-ES')}
                    </p>
                </div>

                {/* Footer / Actions */}
                <div className="p-6 border-t border-border bg-card">
                    <label className="flex items-start gap-3 cursor-pointer group mb-6">
                        <div className="mt-0.5 relative flex items-center justify-center">
                            <input
                                type="checkbox"
                                className="peer appearance-none w-5 h-5 border-2 border-muted-foreground rounded bg-transparent checked:bg-primary checked:border-primary transition-all cursor-pointer"
                                checked={isChecked}
                                onChange={(e) => setIsChecked(e.target.checked)}
                            />
                            <div className="absolute text-white pointer-events-none opacity-0 peer-checked:opacity-100 transition-opacity">
                                <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                                    <polyline points="20 6 9 17 4 12"></polyline>
                                </svg>
                            </div>
                        </div>
                        <span className="text-sm text-foreground select-none group-hover:text-primary transition-colors">
                            He leído, entiendo y acepto los Términos y Condiciones, así como la Política de Privacidad de AuditWeb.
                        </span>
                    </label>

                    <div className="flex gap-3 justify-end">
                        <button
                            onClick={onClose}
                            className="px-5 py-2.5 rounded-lg font-medium text-foreground bg-secondary hover:bg-secondary/80 transition-colors"
                        >
                            Cancelar
                        </button>
                        <button
                            onClick={handleAccept}
                            disabled={!isChecked}
                            className="px-5 py-2.5 rounded-lg font-medium text-white bg-primary hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                        >
                            Aceptar y Continuar
                        </button>
                    </div>
                </div>

            </div>
        </div>
    )
}
