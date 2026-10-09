import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { BarChart3, HelpCircle, ChevronDown, ChevronUp, RefreshCw, AlertTriangle, CheckCircle2, Clock } from 'lucide-react'
import { useI18n, CATEGORY_STRING_KEYS } from '../lib/i18n'
import { api, type DepartmentMetric } from '../lib/api'

export const DashboardPage: React.FC = () => {
  const { t } = useI18n()
  const [metrics, setMetrics] = useState<DepartmentMetric[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showExplainer, setShowExplainer] = useState(false)
  const [lastUpdated, setLastUpdated] = useState<Date>(() => new Date())

  const fetchMetrics = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await api.getPublicMetrics()
      setMetrics(data)
      setLastUpdated(new Date())
    } catch (err: unknown) {
      const apiErr = err as { message?: string }
      setError(apiErr.message || 'Failed to load public metrics')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchMetrics()
  }, [])

  // Aggregate totals
  const totalFiled = metrics.reduce((acc, curr) => acc + (curr.total || 0), 0)
  const totalResolved = metrics.reduce((acc, curr) => acc + (curr.resolved || 0), 0)
  const totalOpen = metrics.reduce((acc, curr) => acc + (curr.open ?? (curr.total - curr.resolved)), 0)
  const totalOverdue = metrics.reduce((acc, curr) => acc + (curr.overdue || 0), 0)

  // Leaderboard ranking: sorted by resolution rate desc, then lowest avg resolution hours
  const rankedDepts = [...metrics].sort((a, b) => {
    const rateA = a.total > 0 ? a.resolved / a.total : 0
    const rateB = b.total > 0 ? b.resolved / b.total : 0
    if (rateB !== rateA) return rateB - rateA
    const hoursA = a.avg_resolution_hours || 999
    const hoursB = b.avg_resolution_hours || 999
    return hoursA - hoursB
  })

  // Max count for chart scaling
  const maxCategoryTotal = Math.max(...metrics.map(m => m.total), 1)
  const maxAvgHours = Math.max(...metrics.map(m => m.avg_resolution_hours || 0), 1)
  const hasResolvedAny = metrics.some(m => (m.resolved || 0) > 0)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-line">
        <div>
          <div className="flex items-center space-x-2">
            <BarChart3 className="w-6 h-6 text-civic" />
            <h1 className="text-2xl font-bold text-ink">{t('dashboard_title')}</h1>
          </div>
          <p className="text-sm text-gray-600 mt-1">{t('dashboard_subtitle')}</p>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-xs text-gray-500 bg-paper px-2.5 py-1 rounded-full border border-line">
            {t('dashboard_updated_at')}: {lastUpdated.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
          <button
            onClick={fetchMetrics}
            disabled={loading}
            className="p-1.5 text-gray-500 hover:text-civic hover:bg-gray-100 rounded-lg transition-colors"
            title="Refresh"
            aria-label="Refresh"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Intro Prompt */}
      <div className="p-4 bg-civic-light border border-blue-200 rounded-xl flex items-center gap-3">
        <div className="w-9 h-9 rounded-lg bg-civic/10 text-civic flex items-center justify-center shrink-0">
          <HelpCircle className="w-5 h-5" />
        </div>
        <p className="text-sm font-semibold text-civic">{t('dashboard_intro')}</p>
      </div>

      {/* Expandable Explainer */}
      <div className="border border-line rounded-xl bg-white overflow-hidden shadow-xs">
        <button
          onClick={() => setShowExplainer(!showExplainer)}
          className="w-full px-4 py-3 text-left font-medium text-sm text-ink flex items-center justify-between hover:bg-gray-50 transition-colors"
        >
          <span className="flex items-center gap-2">
            <HelpCircle className="w-4 h-4 text-civic" />
            {t('dashboard_explainer_title')}
          </span>
          {showExplainer ? (
            <ChevronUp className="w-4 h-4 text-gray-400" />
          ) : (
            <ChevronDown className="w-4 h-4 text-gray-400" />
          )}
        </button>
        {showExplainer && (
          <div className="px-4 pb-4 pt-1 text-xs text-gray-600 leading-relaxed border-t border-line/60 bg-paper/40">
            {t('dashboard_explainer_body')}
          </div>
        )}
      </div>

      {/* Error state */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm flex items-center justify-between">
          <span>{error}</span>
          <button
            onClick={fetchMetrics}
            className="text-xs font-semibold text-red-800 underline hover:no-underline"
          >
            Try Again
          </button>
        </div>
      )}

      {/* Loading Skeleton */}
      {loading && !metrics.length && (
        <div className="space-y-4 animate-pulse">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="h-24 bg-gray-200 rounded-xl" />
            ))}
          </div>
          <div className="h-48 bg-gray-200 rounded-xl" />
        </div>
      )}

      {/* Empty State */}
      {!loading && totalFiled === 0 && (
        <div className="bg-white p-10 rounded-xl border border-line shadow-xs text-center space-y-4">
          <div className="w-12 h-12 bg-gray-100 text-gray-400 rounded-full mx-auto flex items-center justify-center">
            <BarChart3 className="w-6 h-6" />
          </div>
          <h3 className="text-base font-semibold text-ink">{t('empty_chart_message')}</h3>
          <p className="text-xs text-gray-500 max-w-sm mx-auto">
            Be the first to report an issue and hold local municipal authorities accountable.
          </p>
          <Link
            to="/"
            className="inline-block bg-civic text-white px-5 py-2 rounded-lg text-sm font-medium hover:bg-civic/90 transition-colors"
          >
            {t('file_complaint')}
          </Link>
        </div>
      )}

      {/* Main Content when data exists */}
      {totalFiled > 0 && (
        <>
          {/* 4 Summary Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="bg-white p-4 rounded-xl border border-line shadow-xs">
              <span className="text-xs font-medium text-gray-500">{t('dashboard_total_filed')}</span>
              <div className="text-2xl font-extrabold text-ink mt-1">{totalFiled}</div>
            </div>

            <div className="bg-white p-4 rounded-xl border border-line shadow-xs">
              <span className="text-xs font-medium text-gray-500">{t('dashboard_open')}</span>
              <div className="text-2xl font-extrabold text-status-assigned mt-1">{totalOpen}</div>
            </div>

            <div className="bg-white p-4 rounded-xl border border-line shadow-xs">
              <span className="text-xs font-medium text-gray-500">{t('dashboard_resolved')}</span>
              <div className="text-2xl font-extrabold text-status-resolved mt-1">{totalResolved}</div>
            </div>

            <div className={`p-4 rounded-xl border shadow-xs ${totalOverdue > 0 ? 'bg-red-50/50 border-red-200' : 'bg-white border-line'}`}>
              <div className="flex items-center justify-between">
                <span className={`text-xs font-medium ${totalOverdue > 0 ? 'text-status-overdue font-semibold' : 'text-gray-500'}`}>
                  {t('dashboard_overdue')}
                </span>
                {totalOverdue > 0 && <AlertTriangle className="w-3.5 h-3.5 text-status-overdue" />}
              </div>
              <div className={`text-2xl font-extrabold mt-1 ${totalOverdue > 0 ? 'text-status-overdue' : 'text-gray-400'}`}>
                {totalOverdue}
              </div>
            </div>
          </div>

          {/* Department Performance Leaderboard Table */}
          <div className="bg-white rounded-xl border border-line shadow-xs overflow-hidden">
            <div className="p-4 border-b border-line bg-paper/30">
              <h2 className="text-base font-bold text-ink">{t('dashboard_dept_breakdown')}</h2>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm border-collapse">
                <thead>
                  <tr className="border-b border-line text-xs font-semibold text-gray-500 uppercase tracking-wider bg-paper/60">
                    <th className="py-3 px-4 w-12">{t('dashboard_rank')}</th>
                    <th className="py-3 px-4">{t('category')}</th>
                    <th className="py-3 px-4 text-center">{t('dashboard_total_filed')}</th>
                    <th className="py-3 px-4">{t('dashboard_resolved')}</th>
                    <th className="py-3 px-4 text-center">{t('dashboard_open')}</th>
                    <th className="py-3 px-4 text-center">{t('dashboard_overdue')}</th>
                    <th className="py-3 px-4 text-right">{t('dashboard_chart_resolution_time')}</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-line/60">
                  {rankedDepts.map((d, index) => {
                    const catKey = CATEGORY_STRING_KEYS[d.category] || d.category
                    const catLabel = t(catKey)
                    const rate = d.total > 0 ? Math.round((d.resolved / d.total) * 100) : 0
                    const openCount = d.open ?? (d.total - d.resolved)

                    return (
                      <tr key={d.category} className="hover:bg-gray-50/70 transition-colors">
                        <td className="py-3.5 px-4 font-bold text-gray-400 text-xs">
                          #{index + 1}
                        </td>
                        <td className="py-3.5 px-4">
                          <div className="font-semibold text-ink">{catLabel}</div>
                          {d.sla_days && (
                            <div className="text-[11px] text-gray-500">SLA: {d.sla_days} days</div>
                          )}
                        </td>
                        <td className="py-3.5 px-4 text-center font-medium text-ink">
                          {d.total}
                        </td>
                        <td className="py-3.5 px-4">
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-status-resolved">{d.resolved}</span>
                            <span className="text-xs text-gray-400">({rate}%)</span>
                          </div>
                          {/* Mini Progress Bar */}
                          <div className="w-24 bg-gray-100 rounded-full h-1.5 mt-1 overflow-hidden">
                            <div
                              className="bg-status-resolved h-full rounded-full"
                              style={{ width: `${rate}%` }}
                            />
                          </div>
                        </td>
                        <td className="py-3.5 px-4 text-center text-status-assigned font-medium">
                          {openCount}
                        </td>
                        <td className="py-3.5 px-4 text-center">
                          {d.overdue > 0 ? (
                            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-red-100 text-status-overdue">
                              {d.overdue}
                            </span>
                          ) : (
                            <span className="text-gray-400">0</span>
                          )}
                        </td>
                        <td className="py-3.5 px-4 text-right font-medium text-ink">
                          {d.resolved > 0 ? (
                            <span>{d.avg_resolution_hours} <span className="text-xs text-gray-500 font-normal">{t('admin_hours')}</span></span>
                          ) : (
                            <span className="text-gray-400">—</span>
                          )}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Charts Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Chart 1: Open vs Resolved Stacked Bar */}
            <div className="bg-white p-5 rounded-xl border border-line shadow-xs space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="font-bold text-sm text-ink">{t('dashboard_chart_status_breakdown')}</h3>
                <div className="flex items-center gap-3 text-xs">
                  <span className="flex items-center gap-1.5">
                    <span className="w-3 h-3 rounded-xs bg-status-resolved inline-block" />
                    {t('dashboard_resolved')}
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className="w-3 h-3 rounded-xs bg-status-assigned inline-block" />
                    {t('dashboard_open')}
                  </span>
                </div>
              </div>

              <div className="space-y-3 pt-2">
                {metrics.map(d => {
                  const catKey = CATEGORY_STRING_KEYS[d.category] || d.category
                  const resolvedPct = d.total > 0 ? (d.resolved / maxCategoryTotal) * 100 : 0
                  const openCount = d.open ?? (d.total - d.resolved)
                  const openPct = d.total > 0 ? (openCount / maxCategoryTotal) * 100 : 0

                  return (
                    <div key={d.category} className="space-y-1">
                      <div className="flex justify-between text-xs font-medium">
                        <span className="text-ink">{t(catKey)}</span>
                        <span className="text-gray-500 font-normal">{d.total} total</span>
                      </div>
                      <div className="w-full bg-paper rounded-md h-5 flex overflow-hidden border border-line/60">
                        {d.resolved > 0 && (
                          <div
                            className="bg-status-resolved h-full flex items-center justify-center text-[10px] text-white font-semibold transition-all duration-500"
                            style={{ width: `${resolvedPct}%` }}
                            title={`Resolved: ${d.resolved}`}
                          >
                            {resolvedPct > 8 ? d.resolved : ''}
                          </div>
                        )}
                        {openCount > 0 && (
                          <div
                            className="bg-status-assigned h-full flex items-center justify-center text-[10px] text-white font-semibold transition-all duration-500"
                            style={{ width: `${openPct}%` }}
                            title={`Open: ${openCount}`}
                          >
                            {openPct > 8 ? openCount : ''}
                          </div>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Chart 2: Average Resolution Time */}
            <div className="bg-white p-5 rounded-xl border border-line shadow-xs space-y-4">
              <h3 className="font-bold text-sm text-ink">{t('dashboard_chart_resolution_time')}</h3>

              {!hasResolvedAny ? (
                <div className="h-44 flex flex-col items-center justify-center text-center p-4 bg-paper/50 rounded-lg border border-dashed border-line">
                  <Clock className="w-6 h-6 text-gray-400 mb-2" />
                  <p className="text-xs text-gray-500 max-w-xs">
                    No complaints have been resolved yet. Average resolution times will appear once the first fix is verified.
                  </p>
                </div>
              ) : (
                <div className="space-y-3 pt-2">
                  {metrics.map(d => {
                    const catKey = CATEGORY_STRING_KEYS[d.category] || d.category
                    const hours = d.avg_resolution_hours || 0
                    const barWidth = maxAvgHours > 0 ? (hours / maxAvgHours) * 100 : 0

                    return (
                      <div key={d.category} className="space-y-1">
                        <div className="flex justify-between text-xs font-medium">
                          <span className="text-ink">{t(catKey)}</span>
                          <span className="text-gray-500">
                            {d.resolved > 0 ? `${hours} ${t('admin_hours')}` : '—'}
                          </span>
                        </div>
                        <div className="w-full bg-paper rounded-md h-5 flex overflow-hidden border border-line/60">
                          {d.resolved > 0 && hours > 0 ? (
                            <div
                              className="bg-civic h-full flex items-center px-2 text-[10px] text-white font-medium transition-all duration-500"
                              style={{ width: `${Math.max(barWidth, 6)}%` }}
                            >
                              {hours}h
                            </div>
                          ) : (
                            <div className="h-full w-full bg-gray-50 flex items-center px-2 text-[10px] text-gray-400">
                              {d.resolved > 0 ? 'Instant (<1h)' : 'No resolved complaints'}
                            </div>
                          )}
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          </div>
        </>
      )}

      {/* Community Accountability Footer Note */}
      <div className="p-4 bg-paper border border-line rounded-xl text-center text-xs text-gray-500 flex items-center justify-center gap-2">
        <CheckCircle2 className="w-4 h-4 text-status-resolved" />
        <span>Open, transparent, hyper-local civic tracking powered by citizens and municipal staff.</span>
      </div>
    </div>
  )
}
