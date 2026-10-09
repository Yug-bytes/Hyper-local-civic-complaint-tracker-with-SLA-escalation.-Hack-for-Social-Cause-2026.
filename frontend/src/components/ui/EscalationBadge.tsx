import React from 'react'
import { AlertTriangle, Flame } from 'lucide-react'
import { cn } from '../../lib/utils'
import { useI18n } from '../../lib/i18n'

interface EscalationBadgeProps {
  level: number
  className?: string
}

export const EscalationBadge: React.FC<EscalationBadgeProps> = ({ level, className }) => {
  const { t } = useI18n()

  if (level <= 0) return null

  if (level === 1) {
    return (
      <span
        className={cn(
          'inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-red-100 text-red-800 border border-red-300',
          className
        )}
      >
        <AlertTriangle className="w-3 h-3 mr-1" />
        {t('admin_escalation_level_1')}
      </span>
    )
  }

  return (
    <span
      className={cn(
        'inline-flex items-center px-2 py-0.5 rounded text-xs font-bold bg-red-800 text-white border border-red-900 animate-pulse',
        className
      )}
    >
      <Flame className="w-3 h-3 mr-1" />
      {t('admin_escalation_level_2')}
    </span>
  )
}
