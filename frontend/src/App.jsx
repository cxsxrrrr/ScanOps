import { Routes, Route, Navigate } from 'react-router-dom'
import { SignedIn, SignedOut } from '@clerk/clerk-react'
import DashboardLayout from './layouts/DashboardLayout'
import Login from './pages/Login'
import Register from './pages/Register'
import TermsAndConditions from './pages/TermsAndConditions'
import Dashboard from './pages/Dashboard'
import URLs from './pages/URLs'
import ScanHistory from './pages/ScanHistory'
import Report from './pages/Report'
import Profile from './pages/Profile'
import Settings from './pages/Settings'
import Plans from './pages/Plans'
import AdminDashboard from './pages/admin/AdminDashboard'

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

    return (
        <>
            {/* Unauthenticated routes */}
            <SignedOut>
                <Routes>
                    <Route path="/login" element={<Login />} />
                    <Route path="/register" element={<Register />} />
                    <Route path="/terms" element={<TermsAndConditions />} />
                    <Route path="*" element={<Navigate to="/login" replace />} />
                </Routes>
            </SignedOut>

            {/* Authenticated routes */}
            <SignedIn>
                <Routes>
                    <Route path="/" element={<DashboardLayout />}>
                        <Route index element={<Dashboard />} />
                        <Route path="urls" element={<URLs />} />
                        <Route path="scans" element={<ScanHistory />} />
                        <Route path="scans/:scanId/report" element={<Report />} />
                        <Route path="plans" element={<Plans />} />
                        <Route path="profile" element={<Profile />} />
                        <Route path="settings" element={<Settings />} />
                        <Route path="admin" element={<AdminDashboard />} />
                    </Route>
                    <Route path="/terms" element={<TermsAndConditions />} />
                    <Route path="/login" element={<Navigate to="/" replace />} />
                    <Route path="/register" element={<Navigate to="/" replace />} />
                    <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
            </SignedIn>
        </>
    )
}

export default App
