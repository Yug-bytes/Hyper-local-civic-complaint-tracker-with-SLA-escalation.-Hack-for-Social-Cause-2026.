import React from 'react'
import { Shield } from 'lucide-react'
import { useI18n } from '../lib/i18n'

export const Footer: React.FC = () => {
  const { t } = useI18n()

  return (
    <footer className="bg-white border-t border-line mt-auto py-6">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-xs text-gray-500">
        <div className="flex items-center justify-center space-x-1.5 mb-2">
          <Shield className="w-4 h-4 text-civic" />
          <span className="font-semibold text-ink">{t('app_title')}</span>
        </div>
        <p className="max-w-md mx-auto">{t('app_description')}</p>
        <p className="mt-2 text-gray-400">
          Hyper-Local Civic Accountability & SLA Escalation Architecture
        </p>
      </div>
    </footer>
  )
}
