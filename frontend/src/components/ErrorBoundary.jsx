import { Component } from 'react'
import { ShieldAlert, RefreshCw, Home } from 'lucide-react'
import { Button } from '@/components/ui/button'

export default class ErrorBoundary extends Component {
    constructor(props) {
        super(props)
        this.state = { hasError: false, error: null }
    }

    static getDerivedStateFromError(error) {
        return { hasError: true, error }
    }

    componentDidCatch(error, info) {
        console.error('[ErrorBoundary]', error, info)
    }

    render() {
        if (!this.state.hasError) return this.props.children

        return (
            <div className="min-h-screen gradient-bg flex items-center justify-center p-6">
                <div className="max-w-md w-full glass-card rounded-2xl p-8 text-center space-y-5 border border-red-500/20">
                    <div className="w-16 h-16 rounded-2xl bg-red-500/10 flex items-center justify-center mx-auto">
                        <ShieldAlert className="w-8 h-8 text-red-400" />
                    </div>
                    <div>
                        <h1 className="text-xl font-bold mb-2">Algo salió mal</h1>
                        <p className="text-sm text-muted-foreground">
                            Ocurrió un error inesperado en la aplicación. Intenta recargar la página.
                        </p>
                    </div>
                    {this.state.error && (
                        <div className="p-3 rounded-lg bg-red-500/5 border border-red-500/15 text-left">
                            <p className="text-xs font-mono text-red-400 break-all">
                                {this.state.error.message}
                            </p>
                        </div>
                    )}
                    <div className="flex gap-3">
                        <Button
                            variant="outline"
                            className="flex-1"
                            onClick={() => window.location.href = '/'}
                        >
                            <Home className="w-4 h-4" /> Ir al inicio
                        </Button>
                        <Button
                            className="flex-1"
                            onClick={() => window.location.reload()}
                        >
                            <RefreshCw className="w-4 h-4" /> Recargar
                        </Button>
                    </div>
                </div>
            </div>
        )
    }
}
