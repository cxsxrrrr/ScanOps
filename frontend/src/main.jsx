import React from 'react'
import ReactDOM from 'react-dom/client'
import { ClerkProvider } from '@clerk/clerk-react'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import './index.css'

const CLERK_PUBLISHABLE_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY
const AUTH_ENABLED = Boolean(CLERK_PUBLISHABLE_KEY)

if (!CLERK_PUBLISHABLE_KEY) {
    console.warn('Missing VITE_CLERK_PUBLISHABLE_KEY — ScanOps auth will not work.')
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
                        colorTextSecondary: '#94a3b8',
                        colorInputBackground: 'rgba(255,255,255,0.05)',
                        colorInputText: '#e2e8f0',
                        colorDanger: '#ef4444',
                        borderRadius: '0.75rem',
                        spacingUnit: '1rem',
                        fontFamily: 'Inter, sans-serif',
                        fontSize: '0.9375rem',
                    },
                    elements: {
                        // --- Sign In / Sign Up card ---
                        card: 'bg-transparent shadow-none !p-5',
                        formButtonPrimary:
                            'gradient-primary border-0 hover:opacity-90 transition-opacity !py-3 !text-sm !font-semibold !shadow-lg !shadow-blue-500/20 !rounded-xl',
                        formFieldInput:
                            '!bg-white/5 !border-white/10 !text-foreground !rounded-xl !py-3 !px-4 !text-sm placeholder:!text-white/30 focus:!border-blue-500/50 focus:!ring-2 focus:!ring-blue-500/20 !transition-all',
                        formFieldLabel: '!text-foreground !text-sm !font-medium !mb-1.5',
                        formFieldRow: '!mb-4',
                        socialButtonsBlockButton:
                            '!bg-white/5 !border-white/10 hover:!bg-white/10 !text-foreground !rounded-xl !py-3 !transition-all !font-medium',
                        socialButtonsBlockButtonText: '!text-sm !font-medium',
                        socialButtonsProviderIcon: '!filter-none',
                        dividerLine: '!bg-white/10',
                        dividerText: '!text-white/30 !text-xs',
                        dividerRow: '!my-5',
                        footerActionLink: '!text-blue-400 hover:!text-blue-300 !font-medium',
                        identityPreviewEditButton: '!text-blue-400',
                        identityPreviewText: '!text-foreground',
                        formHeaderTitle: '!text-foreground !text-xl !font-bold',
                        formHeaderSubtitle: '!text-white/50 !text-sm',
                        otpCodeFieldInput: '!bg-white/5 !border-white/10 !text-foreground !rounded-lg',
                        formResendCodeLink: '!text-blue-400',
                        alert: '!bg-red-500/10 !border-red-500/20 !text-red-300 !rounded-xl',
                        alertText: '!text-sm',
                        footer: '!bg-transparent',
                        footerAction: '!bg-transparent',
                        footerActionText: '!text-white/40 !text-sm',
                        // --- UserButton popover (logout menu) ---
                        userButtonPopoverCard: '!bg-[#0f172a] !border !border-white/10 !shadow-2xl !shadow-black/50 !rounded-xl',
                        userButtonPopoverActionButton: '!text-foreground hover:!bg-white/10 !rounded-lg',
                        userButtonPopoverActionButtonText: '!text-foreground !text-sm',
                        userButtonPopoverActionButtonIcon: '!text-foreground',
                        userButtonPopoverFooter: '!hidden',
                        userPreviewMainIdentifier: '!text-foreground !font-medium',
                        userPreviewSecondaryIdentifier: '!text-white/50 !text-sm',
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
