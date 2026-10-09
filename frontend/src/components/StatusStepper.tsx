import React from 'react'
import { Check, Clock, PlayCircle, Send, CheckCircle2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useI18n, STATUS_STRING_KEYS } from '@/lib/i18n'

interface StatusStepperProps {
  currentStatus: string
  className?: string
}

const STAGES = [
  { key: 'submitted', icon: Send, stringKey: STATUS_STRING_KEYS.submitted },
  { key: 'assigned', icon: Clock, stringKey: STATUS_STRING_KEYS.assigned },
  { key: 'in_progress', icon: PlayCircle, stringKey: STATUS_STRING_KEYS.in_progress },
  { key: 'resolved', icon: CheckCircle2, stringKey: STATUS_STRING_KEYS.resolved },
]

export const StatusStepper: React.FC<StatusStepperProps> = ({ currentStatus, className }) => {
  const { t } = useI18n()
  const normalized = currentStatus.toLowerCase()

  const currentIndex = STAGES.findIndex((s) => s.key === normalized)
  const activeIndex = currentIndex >= 0 ? currentIndex : 0

  return (
    <div className={cn('w-full py-4', className)}>
      <div className="relative flex items-center justify-between">
        {/* Background track line */}
        <div className="absolute left-6 right-6 top-1/2 -translate-y-1/2 h-1 bg-line -z-0" />

        {/* Active progress fill line */}
        <div
          className="absolute left-6 top-1/2 -translate-y-1/2 h-1 bg-civic -z-0 transition-all duration-500"
          style={{
            width: `${(activeIndex / (STAGES.length - 1)) * 100}%`,
            maxWidth: 'calc(100% - 3rem)',
          }}
        />

        {STAGES.map((stage, idx) => {
          const isCompleted = idx < activeIndex
          const isCurrent = idx === activeIndex
          const Icon = stage.icon

          return (
            <div key={stage.key} className="flex flex-col items-center relative z-10">
              <div
                className={cn(
                  'w-10 h-10 rounded-full flex items-center justify-center transition-all duration-300 shadow-xs border-2',
                  isCompleted && 'bg-civic border-civic text-white',
                  isCurrent && 'bg-white border-civic text-civic ring-4 ring-civic-light scale-110 font-bold',
                  idx > activeIndex && 'bg-white border-line text-gray-400'
                )}
              >
                {isCompleted ? <Check className="w-5 h-5 stroke-[2.5]" /> : <Icon className="w-5 h-5" />}
              </div>

              <span
                className={cn(
                  'mt-2 text-xs text-center font-medium max-w-[80px] sm:max-w-none transition-colors leading-tight',
                  isCurrent && 'text-civic font-bold',
                  isCompleted && 'text-ink font-semibold',
                  idx > activeIndex && 'text-gray-400'
                )}
              >
                {t(stage.stringKey)}
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
