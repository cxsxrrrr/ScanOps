import { Routes, Route, Navigate } from 'react-router-dom'
import { SignedIn, SignedOut } from '@clerk/clerk-react'
import DashboardLayout from './layouts/DashboardLayout'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import URLs from './pages/URLs'
import ScanHistory from './pages/ScanHistory'
import Report from './pages/Report'
import Profile from './pages/Profile'
import Settings from './pages/Settings'
import AdminDashboard from './pages/admin/AdminDashboard'

function App() {
    return (
        <>
            {/* Unauthenticated routes */}
            <SignedOut>
                <Routes>
                    <Route path="/login" element={<Login />} />
                    <Route path="/register" element={<Register />} />
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
                        <Route path="profile" element={<Profile />} />
                        <Route path="settings" element={<Settings />} />
                        <Route path="admin" element={<AdminDashboard />} />
                    </Route>
                    <Route path="/login" element={<Navigate to="/" replace />} />
                    <Route path="/register" element={<Navigate to="/" replace />} />
                    <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
            </SignedIn>
        </>
    )
}

export default App
