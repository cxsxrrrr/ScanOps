import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { CheckCircle } from 'lucide-react'

export default function PaymentSuccess() {
    return (
        <div className="flex items-center justify-center min-h-[60vh]">
            <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.3 }}
            >
                <Card className="max-w-md w-full text-center">
                    <CardContent className="pt-10 pb-10 flex flex-col items-center">
                        <div className="w-20 h-20 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center mb-6">
                            <CheckCircle className="w-10 h-10 text-green-600 dark:text-green-400" />
                        </div>
                        <h1 className="text-2xl font-bold mb-2">¡Pago exitoso!</h1>
                        <p className="text-muted-foreground mb-8">
                            Tu suscripción ha sido actualizada correctamente. Ya puedes disfrutar de todos los beneficios de tu nuevo plan.
                        </p>
                        <Button asChild className="w-full">
                            <Link to="/dashboard">Ir al Dashboard</Link>
                        </Button>
                    </CardContent>
                </Card>
            </motion.div>
        </div>
    )
}
