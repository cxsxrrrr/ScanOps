import { Suspense, lazy } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { SignedIn, SignedOut } from '@clerk/clerk-react'
import { useApiSetup } from './hooks/useApi'
import DashboardLayout from './layouts/DashboardLayout'
import Login from './pages/Login'
import Register from './pages/Register'
import TermsAndConditions from './pages/TermsAndConditions'
import Dashboard from './pages/Dashboard'
import URLs from './pages/URLs'
import ScanHistory from './pages/ScanHistory'
import Profile from './pages/Profile'
import Settings from './pages/Settings'
import JoinTeam from './pages/JoinTeam'

// Lazy-loaded: heavier or less-frequently-visited routes don't need to be
// in the initial bundle — split into their own chunks, fetched on demand.
const Report = lazy(() => import('./pages/Report'))
const Plans = lazy(() => import('./pages/Plans'))
const PaymentSuccess = lazy(() => import('./pages/PaymentSuccess'))
const PaymentCancel = lazy(() => import('./pages/PaymentCancel'))
const AdminDashboard = lazy(() => import('./pages/admin/AdminDashboard'))

function RouteFallback() {
    return (
        <div className="flex items-center justify-center h-64">
            <div className="w-6 h-6 border-2 border-primary/30 border-t-primary rounded-full animate-spin" />
        </div>
    )
}

// Separated so useApiSetup is never called conditionally (Rules of Hooks)
function AuthenticatedApp() {
    useApiSetup()
    return (
        <>
            <SignedOut>
                <Routes>
                    <Route path="/login" element={<Login />} />
                    <Route path="/register" element={<Register />} />
                    <Route path="/terms" element={<TermsAndConditions />} />
                    <Route path="/invite/:token" element={<JoinTeam />} />
                    <Route path="*" element={<Navigate to="/login" replace />} />
                </Routes>
            </SignedOut>

            <SignedIn>
                <Routes>
                    <Route path="/" element={<DashboardLayout />}>
                        <Route index element={<Dashboard />} />
                        <Route path="urls" element={<URLs />} />
                        <Route path="scans" element={<ScanHistory />} />
                        <Route path="scans/:scanId/report" element={
                            <Suspense fallback={<RouteFallback />}><Report /></Suspense>
                        } />
                        <Route path="plans" element={
                            <Suspense fallback={<RouteFallback />}><Plans /></Suspense>
                        } />
                        <Route path="payments/success" element={
                            <Suspense fallback={<RouteFallback />}><PaymentSuccess /></Suspense>
                        } />
                        <Route path="payments/cancel" element={
                            <Suspense fallback={<RouteFallback />}><PaymentCancel /></Suspense>
                        } />
                        <Route path="profile" element={<Profile />} />
                        <Route path="settings" element={<Settings />} />
                        <Route path="admin" element={
                            <Suspense fallback={<RouteFallback />}><AdminDashboard /></Suspense>
                        } />
                    </Route>
                    <Route path="/invite/:token" element={<JoinTeam />} />
                    <Route path="/terms" element={<TermsAndConditions />} />
                    <Route path="/login" element={<Navigate to="/" replace />} />
                    <Route path="/register" element={<Navigate to="/" replace />} />
                    <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
            </SignedIn>
        </>
    )
}

function App({ authEnabled = true }) {
    if (!authEnabled) {
        return (
            <div className="min-h-screen gradient-bg flex items-center justify-center p-6">
                <div className="max-w-xl w-full glass-strong rounded-2xl p-8 text-center">
                    <h1 className="text-2xl font-bold mb-3">Frontend loaded</h1>
                    <p className="text-muted-foreground mb-4">
                        Authentication is disabled because <strong>VITE_CLERK_PUBLISHABLE_KEY</strong> is missing.
                    </p>
                    <p className="text-sm text-muted-foreground">
                        Add this key in your <strong>.env</strong> file and restart <strong>npm run dev</strong> to enable login/register pages.
                    </p>
                </div>
            </div>
        )
    }
    return <AuthenticatedApp />
}

export default App
