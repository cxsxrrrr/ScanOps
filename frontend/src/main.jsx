import React from 'react'
import ReactDOM from 'react-dom/client'
import { ClerkProvider } from '@clerk/clerk-react'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import './index.css'

const CLERK_PUBLISHABLE_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY
const AUTH_ENABLED = Boolean(CLERK_PUBLISHABLE_KEY)

if (!CLERK_PUBLISHABLE_KEY) {
    console.warn('Missing VITE_CLERK_PUBLISHABLE_KEY — Auth will not work.')
}

const app = (
    <BrowserRouter>
        <App authEnabled={AUTH_ENABLED} />
    </BrowserRouter>
)

ReactDOM.createRoot(document.getElementById('root')).render(
    <React.StrictMode>
        {AUTH_ENABLED ? (
            <ClerkProvider
                publishableKey={CLERK_PUBLISHABLE_KEY}
                appearance={{
                    variables: {
                        colorPrimary: '#2a88ff',
                        colorBackground: '#0f172a',
                        colorText: '#e2e8f0',
                        colorInputBackground: '#1e293b',
                        colorInputText: '#e2e8f0',
                        borderRadius: '0.75rem',
                    },
                    elements: {
                        card: 'bg-transparent shadow-none',
                        formButtonPrimary: 'gradient-primary hover:opacity-90',
                    },
                }}
            >
                {app}
            </ClerkProvider>
        ) : (
            app
        )}
    </React.StrictMode>
)
