import React, { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Building2, Globe, Menu, X, ShieldCheck, BarChart3, PlusCircle, Search } from 'lucide-react'
import { useI18n } from '../lib/i18n'
import { cn } from '../lib/utils'

export const Header: React.FC = () => {
  const { language, setLanguage, t } = useI18n()
  const location = useLocation()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  const navLinks = [
    { to: '/', label: t('nav_home'), icon: <Building2 className="w-4 h-4 mr-1.5" /> },
    { to: '/file', label: t('file_complaint'), icon: <PlusCircle className="w-4 h-4 mr-1.5" /> },
    { to: '/track', label: t('check_status'), icon: <Search className="w-4 h-4 mr-1.5" /> },
    { to: '/dashboard', label: t('page_dashboard'), icon: <BarChart3 className="w-4 h-4 mr-1.5" /> },
    { to: '/admin', label: t('page_admin'), icon: <ShieldCheck className="w-4 h-4 mr-1.5" /> },
  ]

  const toggleLanguage = () => {
    setLanguage(language === 'en' ? 'hi' : 'en')
  }

  return (
    <header className="bg-white border-b border-line sticky top-0 z-50 shadow-xs">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand & Project Info */}
          <Link to="/" className="flex items-center space-x-3 group">
            <div className="w-10 h-10 rounded-lg bg-civic text-white flex items-center justify-center shadow-sm group-hover:bg-civic-hover transition-colors">
              <Building2 className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-ink leading-tight">
                {t('app_title')}
              </h1>
              <p className="text-xs text-gray-500 hidden sm:block">
                {t('app_description')}
              </p>
            </div>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center space-x-1 lg:space-x-2">
            {navLinks.map((link) => {
              const isActive = location.pathname === link.to
              return (
                <Link
                  key={link.to}
                  to={link.to}
                  className={cn(
                    'inline-flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-civic-light text-civic font-semibold'
                      : 'text-gray-600 hover:text-ink hover:bg-gray-100'
                  )}
                >
                  {link.icon}
                  {link.label}
                </Link>
              )
            })}
          </nav>

          {/* Actions: Language Toggle & Mobile Hamburger */}
          <div className="flex items-center space-x-2">
            <button
              onClick={toggleLanguage}
              className="inline-flex items-center px-2.5 py-1.5 border border-line rounded-md text-xs font-semibold text-gray-700 bg-paper hover:bg-gray-100 transition-colors shadow-2xs"
              title="Toggle English / हिंदी"
              aria-label="Change language"
            >
              <Globe className="w-3.5 h-3.5 mr-1.5 text-civic" />
              <span>{language === 'en' ? 'हिंदी' : 'English'}</span>
            </button>

            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden p-2 rounded-md text-gray-600 hover:text-ink hover:bg-gray-100"
              aria-label="Toggle navigation menu"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>

        {/* Mobile Dropdown Navigation */}
        {mobileMenuOpen && (
          <div className="md:hidden border-t border-line py-2 space-y-1">
            {navLinks.map((link) => {
              const isActive = location.pathname === link.to
              return (
                <Link
                  key={link.to}
                  to={link.to}
                  onClick={() => setMobileMenuOpen(false)}
                  className={cn(
                    'flex items-center px-3 py-2 rounded-md text-base font-medium',
                    isActive
                      ? 'bg-civic-light text-civic font-semibold'
                      : 'text-gray-700 hover:bg-gray-100'
                  )}
                >
                  {link.icon}
                  {link.label}
                </Link>
              )
            })}
          </div>
        )}
      </div>
    </header>
  )
}
