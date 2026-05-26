import React from 'react'
import ReactDOM from 'react-dom/client'
import { ClerkProvider } from '@clerk/clerk-react'
import { BrowserRouter } from 'react-router-dom'
import { Toaster } from '@/components/ui/sonner'
import App from './App'
import ErrorBoundary from './components/ErrorBoundary'
import { ThemeProvider, useTheme } from './contexts/ThemeContext'
import './index.css'

const CLERK_PUBLISHABLE_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY
const AUTH_ENABLED = Boolean(CLERK_PUBLISHABLE_KEY)

if (!CLERK_PUBLISHABLE_KEY) {
    console.warn('Missing VITE_CLERK_PUBLISHABLE_KEY — Vigia auth will not work.')
}

const darkClerkTheme = {
    variables: {
        colorPrimary: '#2a88ff',
        colorBackground: '#050c1a',
        colorText: '#e2eaf5',
        colorTextSecondary: '#7b8fa8',
        colorInputBackground: 'rgba(255,255,255,0.05)',
        colorInputText: '#e2eaf5',
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
            '!bg-white/5 !border-white/10 !text-foreground !rounded-xl !py-3 !px-4 !text-sm placeholder:!text-white/30 focus:!border-primary/50 focus:!ring-2 focus:!ring-primary/20 !transition-all',
        formFieldLabel: '!text-foreground !text-sm !font-medium !mb-1.5',
        formFieldRow: '!mb-4',
        socialButtonsBlockButton:
            '!bg-white/5 !border-white/10 hover:!bg-white/10 !text-foreground !rounded-xl !py-3 !transition-all !font-medium',
        socialButtonsBlockButtonText: '!text-sm !font-medium',
        dividerLine: '!bg-white/10',
        dividerText: '!text-white/40 !text-xs',
        dividerRow: '!my-5',
        footerActionLink: '!text-blue-400 hover:!text-blue-300 !font-medium',
        footer: '!bg-transparent',
        footerAction: '!bg-transparent',
        footerActionText: '!text-white/50 !text-sm',
        alert: '!bg-red-500/10 !border-red-500/20 !text-red-300 !rounded-xl',
        userButtonPopoverCard: '!bg-[#050c1a] !border !border-white/10 !shadow-2xl !rounded-xl',
        userButtonPopoverActions: '!bg-[#050c1a]',
        userButtonPopoverUserPreview: '!bg-[#050c1a]',
        userPreview: '!bg-[#050c1a]',
        userButtonPopoverHeader: '!bg-[#050c1a]',
        userButtonPopoverActionButton: '!text-slate-200 hover:!bg-white/5 !rounded-lg',
        userButtonPopoverActionButtonText: '!text-slate-200',
        userButtonPopoverActionButtonIcon: '!text-slate-400',
        userButtonPopoverFooter: '!hidden',
        userPreviewMainIdentifier: '!text-white !font-medium',
        userPreviewSecondaryIdentifier: '!text-slate-400 !text-sm',
    },
}

const lightClerkTheme = {
    variables: {
        colorPrimary: '#1d6fe8',
        colorBackground: '#f5f8fc',
        colorText: '#0d1524',
        colorTextSecondary: '#475569',
        colorInputBackground: '#f1f5f9',
        colorInputText: '#0d1524',
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
            '!bg-slate-50 !border-slate-200 !text-foreground !rounded-xl !py-3 !px-4 !text-sm placeholder:!text-slate-400 focus:!border-primary/50 focus:!ring-2 focus:!ring-primary/20 !transition-all',
        formFieldLabel: '!text-foreground !text-sm !font-medium !mb-1.5',
        formFieldRow: '!mb-4',
        socialButtonsBlockButton:
            '!bg-slate-50 !border-slate-200 hover:!bg-slate-100 !text-foreground !rounded-xl !py-3 !transition-all !font-medium',
        socialButtonsBlockButtonText: '!text-sm !font-medium',
        dividerLine: '!bg-slate-200',
        dividerText: '!text-slate-400 !text-xs',
        dividerRow: '!my-5',
        footerActionLink: '!text-blue-600 hover:!text-blue-500 !font-medium',
        footer: '!bg-transparent',
        footerAction: '!bg-transparent',
        footerActionText: '!text-slate-400 !text-sm',
        alert: '!bg-red-50 !border-red-200 !text-red-600 !rounded-xl',
        userButtonPopoverCard: '!bg-white !border !border-slate-200 !shadow-2xl !rounded-xl',
        userButtonPopoverActions: '!bg-white',
        userButtonPopoverUserPreview: '!bg-white',
        userPreview: '!bg-white',
        userButtonPopoverHeader: '!bg-white',
        userButtonPopoverActionButton: '!text-slate-800 hover:!bg-slate-100 !rounded-lg',
        userButtonPopoverActionButtonText: '!text-slate-800',
        userButtonPopoverActionButtonIcon: '!text-slate-500',
        userButtonPopoverFooter: '!hidden',
        userPreviewMainIdentifier: '!text-slate-900 !font-medium',
        userPreviewSecondaryIdentifier: '!text-slate-500 !text-sm',
    },
}

function ThemedApp({ authEnabled }) {
    const { isDark } = useTheme()

    const app = (
        <BrowserRouter>
            <App authEnabled={authEnabled} />
            <Toaster position="top-right" richColors closeButton />
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
        <ErrorBoundary>
            <ThemeProvider>
                <ThemedApp authEnabled={AUTH_ENABLED} />
            </ThemeProvider>
        </ErrorBoundary>
    </React.StrictMode>
)
