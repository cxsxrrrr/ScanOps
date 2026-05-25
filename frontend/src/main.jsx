import React from 'react'
import ReactDOM from 'react-dom/client'
import { ClerkProvider } from '@clerk/clerk-react'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import { useTheme } from './hooks/useTheme'
import './index.css'

const CLERK_PUBLISHABLE_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY
const AUTH_ENABLED = Boolean(CLERK_PUBLISHABLE_KEY)

if (!CLERK_PUBLISHABLE_KEY) {
    console.warn('Missing VITE_CLERK_PUBLISHABLE_KEY — Vigia auth will not work.')
}

const darkClerkTheme = {
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
        card: 'bg-transparent shadow-none !p-5',
        formButtonPrimary:
            'gradient-primary border-0 hover:opacity-90 transition-opacity !py-3 !text-sm !font-semibold !shadow-lg !shadow-blue-500/20 !rounded-xl',
        formFieldInput:
            '!bg-foreground/5 !border-border !text-foreground !rounded-xl !py-3 !px-4 !text-sm placeholder:!text-muted-foreground focus:!border-primary/50 focus:!ring-2 focus:!ring-primary/20 !transition-all',
        formFieldLabel: '!text-foreground !text-sm !font-medium !mb-1.5',
        formFieldRow: '!mb-4',
        socialButtonsBlockButton:
            '!bg-foreground/5 !border-border hover:!bg-foreground/10 !text-foreground !rounded-xl !py-3 !transition-all !font-medium',
        socialButtonsBlockButtonText: '!text-sm !font-medium',
        socialButtonsProviderIcon: '!filter-none',
        dividerLine: '!bg-border',
        dividerText: '!text-muted-foreground !text-xs',
        dividerRow: '!my-5',
        footerActionLink: '!text-blue-400 hover:!text-blue-300 !font-medium',
        identityPreviewEditButton: '!text-blue-400',
        identityPreviewText: '!text-foreground',
        formHeaderTitle: '!text-foreground !text-xl !font-bold',
        formHeaderSubtitle: '!text-muted-foreground !text-sm',
        otpCodeFieldInput: '!bg-foreground/5 !border-border !text-foreground !rounded-lg',
        formResendCodeLink: '!text-blue-400',
        alert: '!bg-red-500/10 !border-red-500/20 !text-red-300 !rounded-xl',
        alertText: '!text-sm',
        footer: '!bg-transparent',
        footerAction: '!bg-transparent',
        footerActionText: '!text-muted-foreground !text-sm',
        userButtonPopoverCard: '!bg-popover !border !border-border !shadow-2xl !rounded-xl',
        userButtonPopoverActionButton: '!text-foreground hover:!bg-foreground/5 !rounded-lg',
        userButtonPopoverActionButtonText: '!text-foreground !text-sm',
        userButtonPopoverActionButtonIcon: '!text-foreground',
        userButtonPopoverFooter: '!hidden',
        userPreviewMainIdentifier: '!text-foreground !font-medium',
        userPreviewSecondaryIdentifier: '!text-muted-foreground !text-sm',
    },
}

const lightClerkTheme = {
    variables: {
        colorPrimary: '#2a88ff',
        colorBackground: '#f8fafc',
        colorText: '#0f172a',
        colorTextSecondary: '#475569',
        colorInputBackground: '#f1f5f9',
        colorInputText: '#0f172a',
        colorDanger: '#ef4444',
        borderRadius: '0.75rem',
        spacingUnit: '1rem',
        fontFamily: 'Inter, sans-serif',
        fontSize: '0.9375rem',
    },
    elements: {
        card: 'bg-transparent shadow-none !p-5',
        formButtonPrimary:
            'gradient-primary border-0 hover:opacity-90 transition-opacity !py-3 !text-sm !font-semibold !shadow-lg !shadow-blue-500/20 !rounded-xl',
        formFieldInput:
            '!bg-muted !border-border !text-foreground !rounded-xl !py-3 !px-4 !text-sm placeholder:!text-muted-foreground focus:!border-primary/50 focus:!ring-2 focus:!ring-primary/20 !transition-all',
        formFieldLabel: '!text-foreground !text-sm !font-medium !mb-1.5',
        formFieldRow: '!mb-4',
        socialButtonsBlockButton:
            '!bg-muted !border-border hover:!bg-accent !text-foreground !rounded-xl !py-3 !transition-all !font-medium',
        socialButtonsBlockButtonText: '!text-sm !font-medium',
        socialButtonsProviderIcon: '!filter-none',
        dividerLine: '!bg-border',
        dividerText: '!text-muted-foreground !text-xs',
        dividerRow: '!my-5',
        footerActionLink: '!text-blue-600 hover:!text-blue-500 !font-medium',
        identityPreviewEditButton: '!text-blue-600',
        identityPreviewText: '!text-foreground',
        formHeaderTitle: '!text-foreground !text-xl !font-bold',
        formHeaderSubtitle: '!text-muted-foreground !text-sm',
        otpCodeFieldInput: '!bg-muted !border-border !text-foreground !rounded-lg',
        formResendCodeLink: '!text-blue-600',
        alert: '!bg-red-50 !border-red-200 !text-red-600 !rounded-xl',
        alertText: '!text-sm',
        footer: '!bg-transparent',
        footerAction: '!bg-transparent',
        footerActionText: '!text-muted-foreground !text-sm',
        userButtonPopoverCard: '!bg-popover !border !border-border !shadow-2xl !rounded-xl',
        userButtonPopoverActionButton: '!text-foreground hover:!bg-accent !rounded-lg',
        userButtonPopoverActionButtonText: '!text-foreground !text-sm',
        userButtonPopoverActionButtonIcon: '!text-foreground',
        userButtonPopoverFooter: '!hidden',
        userPreviewMainIdentifier: '!text-foreground !font-medium',
        userPreviewSecondaryIdentifier: '!text-muted-foreground !text-sm',
    },
}

function ThemedApp({ authEnabled }) {
    const { isDark } = useTheme()

    const app = (
        <BrowserRouter>
            <App authEnabled={authEnabled} />
        </BrowserRouter>
    )

    if (!authEnabled) return app

    return (
        <ClerkProvider
            publishableKey={CLERK_PUBLISHABLE_KEY}
            appearance={isDark ? darkClerkTheme : lightClerkTheme}
        >
            {app}
        </ClerkProvider>
    )
}

ReactDOM.createRoot(document.getElementById('root')).render(
    <React.StrictMode>
        <ThemedApp authEnabled={AUTH_ENABLED} />
    </React.StrictMode>
)