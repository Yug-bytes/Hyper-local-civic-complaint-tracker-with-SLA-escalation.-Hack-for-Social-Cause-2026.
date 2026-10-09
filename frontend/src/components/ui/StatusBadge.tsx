import React from 'react'
import { Clock, CheckCircle2, AlertCircle, PlayCircle, Send } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useI18n, STATUS_STRING_KEYS } from '@/lib/i18n'

interface StatusBadgeProps {
  status: string
  isOverdue?: boolean
  className?: string
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, isOverdue = false, className }) => {
  const { t } = useI18n()
  const normalized = status.toLowerCase()

  const config: Record<
    string,
    { labelKey: string; bg: string; text: string; icon: React.ReactNode }
  > = {
    submitted: {
      labelKey: STATUS_STRING_KEYS.submitted,
      bg: 'bg-status-submitted',
      text: 'text-white',
      icon: <Send className="w-3.5 h-3.5 mr-1" />,
    },
    assigned: {
      labelKey: STATUS_STRING_KEYS.assigned,
      bg: 'bg-status-assigned',
      text: 'text-white',
      icon: <Clock className="w-3.5 h-3.5 mr-1" />,
    },
    in_progress: {
      labelKey: STATUS_STRING_KEYS.in_progress,
      bg: 'bg-status-progress',
      text: 'text-white',
      icon: <PlayCircle className="w-3.5 h-3.5 mr-1" />,
    },
    resolved: {
      labelKey: STATUS_STRING_KEYS.resolved,
      bg: 'bg-status-resolved',
      text: 'text-white',
      icon: <CheckCircle2 className="w-3.5 h-3.5 mr-1" />,
    },
  }

  const current = config[normalized] || {
    labelKey: status,
    bg: 'bg-gray-500',
    text: 'text-white',
    icon: <Clock className="w-3.5 h-3.5 mr-1" />,
  }

  return (
    <div className="inline-flex items-center gap-1.5 flex-wrap">
      <span
        className={cn(
          'inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold tracking-wide shadow-sm',
          current.bg,
          current.text,
          className
        )}
      >
        {current.icon}
        <span>{t(current.labelKey)}</span>
      </span>

      {isOverdue && normalized !== 'resolved' && (
        <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold tracking-wide bg-status-overdue text-white shadow-sm animate-pulse">
          <AlertCircle className="w-3.5 h-3.5 mr-1" />
          <span>{t('overdue')}</span>
        </span>
      )}
    </div>
  )
}
