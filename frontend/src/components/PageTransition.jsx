import { motion } from 'framer-motion'

const variants = {
    hidden:  { opacity: 0, y: 12 },
    visible: { opacity: 1, y: 0,  transition: { duration: 0.28, ease: [0.16, 1, 0.3, 1] } },
    exit:    { opacity: 0, y: -6, transition: { duration: 0.18, ease: 'easeIn' } },
}

export default function PageTransition({ children }) {
    return (
        <motion.div
            variants={variants}
            initial="hidden"
            animate="visible"
            exit="exit"
        >
            {children}
        </motion.div>
    )
}
