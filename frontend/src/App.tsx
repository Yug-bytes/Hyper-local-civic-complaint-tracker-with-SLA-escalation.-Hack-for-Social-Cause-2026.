import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { I18nProvider } from './lib/i18n'
import { Layout } from './components/Layout'
import { LandingPage } from './pages/LandingPage'
import { CitizenPage } from './pages/CitizenPage'
import { TrackPage } from './pages/TrackPage'
import { DashboardPage } from './pages/DashboardPage'
import { AdminPage } from './pages/AdminPage'

export const App: React.FC = () => {
  return (
    <I18nProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<LandingPage />} />
            <Route path="file" element={<CitizenPage />} />
            <Route path="complaint" element={<Navigate to="/file" replace />} />
            <Route path="citizen" element={<Navigate to="/file" replace />} />
            <Route path="track" element={<TrackPage />} />
            <Route path="dashboard" element={<DashboardPage />} />
            <Route path="admin" element={<AdminPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </I18nProvider>
  )
}

export default App
