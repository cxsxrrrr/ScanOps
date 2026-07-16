import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { XCircle } from 'lucide-react'

export default function PaymentCancel() {
    return (
        <div className="flex items-center justify-center min-h-[60vh]">
            <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.3 }}
            >
                <Card className="max-w-md w-full text-center">
                    <CardContent className="pt-10 pb-10 flex flex-col items-center">
                        <div className="w-20 h-20 bg-red-100 dark:bg-red-900/30 rounded-full flex items-center justify-center mb-6">
                            <XCircle className="w-10 h-10 text-red-600 dark:text-red-400" />
                        </div>
                        <h1 className="text-2xl font-bold mb-2">Pago cancelado</h1>
                        <p className="text-muted-foreground mb-8">
                            El proceso de pago ha sido cancelado y no se ha realizado ningún cargo en tu tarjeta. Puedes intentarlo de nuevo cuando desees.
                        </p>
                        <Button asChild variant="outline" className="w-full mb-3">
                            <Link to="/settings/plans">Volver a los planes</Link>
                        </Button>
                        <Button asChild variant="ghost" className="w-full">
                            <Link to="/dashboard">Ir al Dashboard</Link>
                        </Button>
                    </CardContent>
                </Card>
            </motion.div>
        </div>
    )
}
