import React from 'react'
import ReactDOM from 'react-dom/client'
import { ClerkProvider } from '@clerk/clerk-react'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import './index.css'

const CLERK_PUBLISHABLE_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY

if (!CLERK_PUBLISHABLE_KEY) {
    console.warn('Missing VITE_CLERK_PUBLISHABLE_KEY — Auth will not work.')
}

ReactDOM.createRoot(document.getElementById('root')).render(
    <React.StrictMode>
        <ClerkProvider
            publishableKey={CLERK_PUBLISHABLE_KEY || 'pk_test_placeholder'}
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
            <BrowserRouter>
                <App />
            </BrowserRouter>
        </ClerkProvider>
    </React.StrictMode>
)
