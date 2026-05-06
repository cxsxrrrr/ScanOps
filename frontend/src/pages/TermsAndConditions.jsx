import { useState } from 'react'
import { Link } from 'react-router-dom'
import {
    ShieldCheck, ArrowLeft, ScrollText, Scale, Lock,
    AlertTriangle, Database, Globe, FileText, ChevronDown,
    ChevronRight,
} from 'lucide-react'

const sections = [
    {
        id: 'uso-aceptable',
        icon: Globe,
        title: '1. Uso Aceptable',
        content: `Vigia es una herramienta de ciberseguridad diseñada exclusivamente para el análisis legítimo de seguridad web. Al utilizar este servicio, usted acepta y se compromete a:

• **Escanear únicamente dominios de su propiedad** o dominios para los cuales tenga autorización expresa y documentada del propietario.
• **No utilizar Vigia para actividades ilegales**, incluyendo pero no limitado a: acceso no autorizado a sistemas, ataques de denegación de servicio, exfiltración de datos, o cualquier forma de hacking malicioso.
• **No utilizar los resultados de los escaneos** para explotar vulnerabilidades encontradas en sistemas de terceros.
• **Informar responsablemente** cualquier vulnerabilidad descubierta al propietario legítimo del dominio afectado.

Cualquier uso que viole las leyes locales, nacionales o internacionales de ciberseguridad, incluyendo la Ley de Delitos Informáticos y legislación equivalente en su jurisdicción, resultará en la terminación inmediata de su cuenta y podrá derivar en acciones legales.`,
    },
    {
        id: 'limitacion-responsabilidad',
        icon: Scale,
        title: '2. Limitación de Responsabilidad',
        content: `Vigia proporciona sus servicios de escaneo de seguridad "tal cual" y "según disponibilidad". En la máxima medida permitida por la ley:

• **No garantizamos** que nuestros escaneos detecten todas las vulnerabilidades existentes en un sitio web. La ausencia de hallazgos no implica que un sistema sea completamente seguro.
• **No somos responsables** de daños directos, indirectos, incidentales, consecuentes o punitivos que resulten del uso o la incapacidad de uso de nuestros servicios.
• **No somos responsables** de interrupciones, caídas o degradación del rendimiento de los sitios web escaneados durante o después del proceso de escaneo.
• **El usuario asume toda la responsabilidad** de las acciones tomadas basándose en los resultados de los escaneos.
• **Vigia no será responsable** por el uso indebido de la información proporcionada en los reportes de seguridad.

Nuestra responsabilidad total no excederá el monto pagado por el usuario en los últimos 12 meses de servicio.`,
    },
    {
        id: 'privacidad-datos',
        icon: Lock,
        title: '3. Privacidad y Protección de Datos',
        content: `Nos comprometemos a proteger la privacidad de sus datos de acuerdo con los más altos estándares de la industria:

• **Datos de escaneo**: Los resultados de los escaneos, incluyendo vulnerabilidades encontradas, son almacenados de manera encriptada y accesibles únicamente por los usuarios autorizados de su organización.
• **Datos personales**: Recopilamos únicamente la información necesaria para proveer el servicio: email, nombre y datos de la organización.
• **No compartimos** sus datos de escaneo ni resultados con terceros, a menos que sea requerido por orden judicial.
• **Encriptación**: Todos los datos en tránsito están protegidos mediante TLS 1.3 y los datos en reposo están encriptados con AES-256.
• **Acceso interno**: El acceso a los datos de los usuarios está restringido al personal técnico autorizado y se registra en logs de auditoría.`,
    },
    {
        id: 'retencion-datos',
        icon: Database,
        title: '4. Almacenamiento y Retención de Datos',
        content: `Los datos generados por los escaneos son almacenados bajo las siguientes políticas:

• **Resultados de escaneo**: Se almacenan por un período máximo de 12 meses desde la fecha del escaneo.
• **Reportes generados por IA**: Los resúmenes ejecutivos se generan en tiempo real y se almacenan junto con el escaneo asociado.
• **Eliminación de datos**: Puede solicitar la eliminación de todos sus datos en cualquier momento contactando a nuestro equipo de soporte.
• **Cancelación de cuenta**: Al cancelar su cuenta, todos sus datos serán eliminados permanentemente dentro de los 30 días siguientes.
• **Backups**: Los respaldos de seguridad se mantienen por un máximo de 90 días y se eliminan automáticamente después.`,
    },
    {
        id: 'uso-prohibido',
        icon: AlertTriangle,
        title: '5. Uso Prohibido y Sanciones',
        content: `Queda estrictamente prohibido utilizar Vigia para:

• **Escanear dominios sin autorización**: Esto constituye un delito en la mayoría de las jurisdicciones y puede resultar en responsabilidad penal.
• **Realizar ataques**: Usar los hallazgos de seguridad para atacar, comprometer o dañar sistemas informáticos.
• **Competencia desleal**: Usar los resultados para obtener ventaja competitiva ilegal o difamar a competidores.
• **Reventa de datos**: Vender, compartir o publicar los resultados de escaneos sin autorización.
• **Evasión de controles**: Intentar eludir las restricciones del plan contratado o manipular el sistema de facturación.
• **Ingeniería inversa**: Descompilar, desensamblar o realizar ingeniería inversa del motor de escaneo.

**Consecuencias**: Las violaciones de estos términos resultarán en la suspensión o cancelación inmediata de la cuenta, sin derecho a reembolso, y podrán derivar en acciones legales civiles y/o penales.`,
    },
    {
        id: 'planes-facturacion',
        icon: FileText,
        title: '6. Planes, Facturación y SLA',
        content: `Vigia ofrece tres niveles de servicio:

• **Plan Free ($0/mes)**: 1 URL registrada, escaneos básicos, soporte por email.
• **Plan Pro ($10/mes)**: Hasta 5 URLs registradas, escaneos avanzados, reportes con IA, soporte prioritario.
• **Plan Ultimate ($20/mes)**: Hasta 10 URLs registradas, todos los checks disponibles, reportes ejecutivos con IA, soporte premium 24/7.

**Facturación**: Los planes de pago se facturan mensualmente. Los cambios de plan se aplican inmediatamente.
**Downgrade**: Al bajar de plan, si el número de URLs registradas excede el límite del nuevo plan, las URLs excedentes quedarán bloqueadas hasta que el usuario las elimine o actualice su plan.
**Reembolsos**: No se realizan reembolsos por períodos parciales de servicio.
**SLA**: Garantizamos un uptime del 99.5% para los servicios de escaneo. Los tiempos de inactividad programados se comunicarán con al menos 24 horas de antelación.`,
    },
    {
        id: 'propiedad-intelectual',
        icon: ScrollText,
        title: '7. Propiedad Intelectual',
        content: `• **Motor de escaneo**: El motor de escaneo de Vigia, sus algoritmos y metodologías son propiedad exclusiva de Vigia.
• **Reportes**: Los reportes generados son propiedad del usuario contratante y pueden ser utilizados internamente sin restricción.
• **Marca**: El nombre Vigia, su logo y diseño visual son marcas registradas. No pueden ser reproducidos sin autorización.
• **Retroalimentación**: Cualquier sugerencia o mejora enviada por los usuarios podrá ser incorporada al producto sin obligación de compensación.`,
    },
    {
        id: 'jurisdiccion',
        icon: Scale,
        title: '8. Jurisdicción y Legislación Aplicable',
        content: `• Estos términos se rigen por las leyes de la República Bolivariana de Venezuela y la legislación internacional aplicable en materia de ciberseguridad.
• Cualquier disputa será resuelta en primera instancia mediante mediación y, de no alcanzarse un acuerdo, ante los tribunales competentes.
• El usuario reconoce que es responsable de cumplir con las leyes de ciberseguridad de su jurisdicción antes de utilizar los servicios de escaneo.
• En caso de conflicto entre estos términos y la legislación local, prevalecerá la normativa más estricta.`,
    },
]

export default function TermsAndConditions() {
    const [expandedSection, setExpandedSection] = useState(null)
    const [expandAll, setExpandAll] = useState(false)

    const toggleSection = (id) => {
        setExpandedSection(expandedSection === id ? null : id)
    }

    const handleExpandAll = () => {
        setExpandAll(!expandAll)
        setExpandedSection(null)
    }

    const isSectionExpanded = (id) => expandAll || expandedSection === id

    return (
        <div className="min-h-screen gradient-bg">
            {/* Hero */}
            <div className="relative overflow-hidden border-b border-border">
                <div className="absolute w-72 h-72 bg-blue-500/10 rounded-full blur-3xl top-10 left-10 animate-float" />
                <div className="absolute w-96 h-96 bg-purple-500/8 rounded-full blur-3xl bottom-0 right-20 animate-float-slow" />

                <div className="relative z-10 max-w-4xl mx-auto px-6 py-16 text-center">
                    <Link
                        to="/register"
                        className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-8 transition-colors"
                    >
                        <ArrowLeft className="w-3 h-3" /> Volver al registro
                    </Link>
                    <div className="w-16 h-16 rounded-2xl gradient-primary flex items-center justify-center mx-auto mb-6 shadow-xl shadow-blue-500/30">
                        <ScrollText className="w-8 h-8 text-white" />
                    </div>
                    <h1 className="text-4xl font-extrabold bg-gradient-to-r from-blue-400 via-purple-400 to-cyan-400 bg-clip-text text-transparent mb-4">
                        Términos y Condiciones
                    </h1>
                    <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
                        Al utilizar Vigia, usted acepta estos términos que regulan
                        el uso responsable de nuestra plataforma de ciberseguridad.
                    </p>
                    <p className="text-xs text-muted-foreground mt-4">
                        Última actualización: Marzo 2026
                    </p>
                </div>
            </div>

            {/* Content */}
            <div className="max-w-4xl mx-auto px-6 py-12">
                {/* Expand all toggle */}
                <div className="flex justify-end mb-6">
                    <button
                        onClick={handleExpandAll}
                        className="text-sm text-muted-foreground hover:text-foreground transition-colors flex items-center gap-1"
                    >
                        {expandAll ? 'Colapsar todo' : 'Expandir todo'}
                    </button>
                </div>

                {/* Sections */}
                <div className="space-y-3">
                    {sections.map((section) => {
                        const isOpen = isSectionExpanded(section.id)
                        return (
                            <div
                                key={section.id}
                                className={`glass-card rounded-xl overflow-hidden transition-all duration-300 ${
                                    isOpen ? 'glow-blue' : ''
                                }`}
                            >
                                <button
                                    onClick={() => toggleSection(section.id)}
                                    className="w-full flex items-center gap-4 p-5 hover:bg-foreground/5 transition-colors text-left"
                                    id={`terms-section-${section.id}`}
                                >
                                    <div className="w-10 h-10 rounded-lg gradient-primary flex items-center justify-center flex-shrink-0">
                                        <section.icon className="w-5 h-5 text-white" />
                                    </div>
                                    <span className="flex-1 font-semibold text-lg">
                                        {section.title}
                                    </span>
                                    {isOpen ? (
                                        <ChevronDown className="w-5 h-5 text-muted-foreground transition-transform" />
                                    ) : (
                                        <ChevronRight className="w-5 h-5 text-muted-foreground transition-transform" />
                                    )}
                                </button>
                                {isOpen && (
                                    <div className="px-5 pb-5 pt-0 animate-fade-in">
                                        <div className="pl-14 text-sm text-muted-foreground leading-relaxed whitespace-pre-line">
                                            {section.content.split(/(\*\*.*?\*\*)/).map((part, i) => {
                                                if (part.startsWith('**') && part.endsWith('**')) {
                                                    return (
                                                        <strong key={i} className="text-foreground font-medium">
                                                            {part.slice(2, -2)}
                                                        </strong>
                                                    )
                                                }
                                                return <span key={i}>{part}</span>
                                            })}
                                        </div>
                                    </div>
                                )}
                            </div>
                        )
                    })}
                </div>

                {/* Footer */}
                <div className="mt-12 glass-card rounded-xl p-6 text-center">
                    <ShieldCheck className="w-8 h-8 text-blue-400 mx-auto mb-3" />
                    <p className="text-sm text-muted-foreground">
                        Al crear una cuenta en Vigia, confirmas que has leído, comprendido y aceptas
                        estos Términos y Condiciones en su totalidad.
                    </p>
                    <Link
                        to="/register"
                        className="inline-flex items-center gap-2 mt-4 px-6 py-2.5 rounded-lg gradient-primary text-white font-medium text-sm hover:opacity-90 transition-opacity"
                    >
                        Crear cuenta
                    </Link>
                </div>
            </div>
        </div>
    )
}
