import React, { useEffect, useState, useCallback } from 'react'
import {
  ShieldCheck,
  Lock,
  LogOut,
  RefreshCw,
  Search,
  AlertTriangle,
  Clock,
  Trash2,
  Send,
  Eye,
  Check,
  Copy,
  Layers,
  BarChart2,
  Calendar,
  MapPin,
  Tag,
  CheckCircle2,
} from 'lucide-react'
import { useI18n, CATEGORY_STRING_KEYS, STATUS_STRING_KEYS } from '@/lib/i18n'
import { api, type ComplaintAdmin, type StatusHistory, type AdminMetricsSummary } from '@/lib/api'
import { formatDateTime } from '@/lib/date'
import { StatusBadge } from '@/components/ui/StatusBadge'
import { EscalationBadge } from '@/components/ui/EscalationBadge'
import { Button } from '@/components/ui/Button'

const ALLOWED_NEXT_STATUS: Record<string, string> = {
  submitted: 'assigned',
  assigned: 'in_progress',
  in_progress: 'resolved',
}

export const AdminPage: React.FC = () => {
  const { t } = useI18n()

  // Authentication State
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false)
  const [isCheckingSession, setIsCheckingSession] = useState<boolean>(true)
  const [passwordInput, setPasswordInput] = useState<string>('')
  const [loginError, setLoginError] = useState<string | null>(null)
  const [isLoggingIn, setIsLoggingIn] = useState<boolean>(false)

  // Active Tab
  const [activeTab, setActiveTab] = useState<'complaints' | 'analytics'>('complaints')

  // Data State
  const [complaints, setComplaints] = useState<ComplaintAdmin[]>([])
  const [metrics, setMetrics] = useState<AdminMetricsSummary | null>(null)
  const [isLoadingData, setIsLoadingData] = useState<boolean>(false)
  const [dataError, setDataError] = useState<string | null>(null)

  // Filters State
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [categoryFilter, setCategoryFilter] = useState<string>('')
  const [overdueOnly, setOverdueOnly] = useState<boolean>(false)
  const [searchQuery, setSearchQuery] = useState<string>('')

  // Selected Complaint for Detail View
  const [selectedComplaintId, setSelectedComplaintId] = useState<string | null>(null)
  const [historyList, setHistoryList] = useState<StatusHistory[]>([])
  const [isLoadingHistory, setIsLoadingHistory] = useState<boolean>(false)

  // Status Update Form State
  const [statusNote, setStatusNote] = useState<string>('')
  const [isUpdatingStatus, setIsUpdatingStatus] = useState<boolean>(false)
  const [actionSuccess, setActionSuccess] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)

  // Photo Unlink State
  const [isUnlinkingPhoto, setIsUnlinkingPhoto] = useState<boolean>(false)
  const [copiedId, setCopiedId] = useState<boolean>(false)

  // 1. Initial Session Check
  useEffect(() => {
    const verifySession = async () => {
      try {
        setIsCheckingSession(true)
        const res = await api.checkAdminSession()
        setIsAuthenticated(res.authenticated)
      } catch {
        setIsAuthenticated(false)
      } finally {
        setIsCheckingSession(false)
      }
    }
    verifySession()
  }, [])

  // 2. Fetch Admin Data
  const loadAdminData = useCallback(async () => {
    if (!isAuthenticated) return
    try {
      setIsLoadingData(true)
      setDataError(null)

      const [complaintsData, metricsData] = await Promise.all([
        api.getAdminComplaints({
          status: statusFilter || undefined,
          category: categoryFilter || undefined,
          overdue_only: overdueOnly || undefined,
        }),
        api.getAdminMetrics().catch(() => null),
      ])

      setComplaints(complaintsData)
      if (metricsData) setMetrics(metricsData)

      // Keep selection or auto-select first if none selected
      if (complaintsData.length > 0) {
        if (!selectedComplaintId || !complaintsData.find(c => c.tracking_id === selectedComplaintId)) {
          setSelectedComplaintId(complaintsData[0].tracking_id)
        }
      } else {
        setSelectedComplaintId(null)
      }
    } catch (err: unknown) {
      const apiErr = err as { message?: string }
      setDataError(apiErr.message || 'Failed to load complaints')
    } finally {
      setIsLoadingData(false)
    }
  }, [isAuthenticated, statusFilter, categoryFilter, overdueOnly, selectedComplaintId])

  useEffect(() => {
    if (isAuthenticated) {
      loadAdminData()
    }
  }, [isAuthenticated, statusFilter, categoryFilter, overdueOnly]) // eslint-disable-line react-hooks/exhaustive-deps

  // 3. Fetch History when selected complaint changes
  useEffect(() => {
    const fetchHistory = async () => {
      if (!selectedComplaintId) {
        setHistoryList([])
        return
      }
      try {
        setIsLoadingHistory(true)
        const full = await api.getComplaintStatus(selectedComplaintId)
        setHistoryList(full.history || [])
      } catch {
        setHistoryList([])
      } finally {
        setIsLoadingHistory(false)
      }
    }

    if (isAuthenticated && selectedComplaintId) {
      fetchHistory()
      setStatusNote('')
      setActionSuccess(null)
      setActionError(null)
    }
  }, [selectedComplaintId, isAuthenticated])

  // Login Handler
  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!passwordInput.trim()) return

    try {
      setIsLoggingIn(true)
      setLoginError(null)
      await api.adminLogin(passwordInput.trim())
      setIsAuthenticated(true)
      setPasswordInput('')
    } catch (err: unknown) {
      const apiErr = err as { message?: string }
      setLoginError(apiErr.message || t('admin_password_error'))
    } finally {
      setIsLoggingIn(false)
    }
  }

  // Logout Handler
  const handleLogout = async () => {
    try {
      await api.adminLogout()
    } finally {
      setIsAuthenticated(false)
      setComplaints([])
      setSelectedComplaintId(null)
      setMetrics(null)
    }
  }

  // Status Update Handler
  const handleStatusUpdate = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedComplaint) return

    const nextStatus = ALLOWED_NEXT_STATUS[selectedComplaint.status]
    if (!nextStatus) return

    try {
      setIsUpdatingStatus(true)
      setActionError(null)
      setActionSuccess(null)

      const updated = await api.updateComplaintStatus(
        selectedComplaint.tracking_id,
        nextStatus,
        statusNote.trim() || undefined
      )

      // Update in local state
      setComplaints(prev =>
        prev.map(c => (c.tracking_id === updated.tracking_id ? updated : c))
      )
      setStatusNote('')
      const nextLabel = t(STATUS_STRING_KEYS[nextStatus] || nextStatus)
      setActionSuccess(`Status advanced to "${nextLabel}"`)

      // Refresh history & metrics
      const full = await api.getComplaintStatus(updated.tracking_id)
      setHistoryList(full.history || [])
      api.getAdminMetrics().then(setMetrics).catch(() => {})
    } catch (err: unknown) {
      const apiErr = err as { message?: string }
      setActionError(apiErr.message || 'Status update failed')
    } finally {
      setIsUpdatingStatus(false)
    }
  }

  // Photo Unlink Handler
  const handleUnlinkPhoto = async () => {
    if (!selectedComplaint) return
    const confirmed = window.confirm(
      'Are you sure you want to remove this photo? This cannot be undone.'
    )
    if (!confirmed) return

    try {
      setIsUnlinkingPhoto(true)
      setActionError(null)
      await api.deleteComplaintPhoto(selectedComplaint.tracking_id)

      // Update complaint in local state
      setComplaints(prev =>
        prev.map(c =>
          c.tracking_id === selectedComplaint.tracking_id
            ? { ...c, photo_url: null }
            : c
        )
      )
      setActionSuccess('Attached photo successfully removed.')
    } catch (err: unknown) {
      const apiErr = err as { message?: string }
      setActionError(apiErr.message || 'Failed to remove photo')
    } finally {
      setIsUnlinkingPhoto(false)
    }
  }

  const handleCopyId = (id: string) => {
    navigator.clipboard.writeText(id)
    setCopiedId(true)
    setTimeout(() => setCopiedId(false), 2000)
  }

  // Filter complaints by client-side search query
  const filteredComplaints = complaints.filter(c => {
    if (!searchQuery.trim()) return true
    const q = searchQuery.toLowerCase()
    return (
      c.tracking_id.toLowerCase().includes(q) ||
      c.locality.toLowerCase().includes(q) ||
      (c.reporter_name && c.reporter_name.toLowerCase().includes(q)) ||
      c.description.toLowerCase().includes(q)
    )
  })

  const selectedComplaint = complaints.find(c => c.tracking_id === selectedComplaintId)

  // Loading Session State
  if (isCheckingSession) {
    return (
      <div className="min-h-[50vh] flex flex-col items-center justify-center space-y-3">
        <div className="w-10 h-10 border-4 border-civic border-t-transparent rounded-full animate-spin" />
        <p className="text-sm text-gray-500 font-medium">Verifying administrator session...</p>
      </div>
    )
  }

  // Unauthenticated Login Card
  if (!isAuthenticated) {
    return (
      <div className="max-w-md mx-auto space-y-6 pt-6">
        <div className="text-center space-y-2">
          <div className="w-14 h-14 bg-civic-light text-civic rounded-2xl mx-auto flex items-center justify-center border border-blue-200 shadow-xs">
            <ShieldCheck className="w-8 h-8" />
          </div>
          <h1 className="text-2xl font-bold text-ink">{t('admin_title')}</h1>
          <p className="text-sm text-gray-600">
            Sign in with the municipal administrator key to manage complaints and view citizen escalations.
          </p>
        </div>

        <form
          onSubmit={handleLogin}
          className="bg-white p-6 sm:p-7 rounded-2xl border border-line shadow-xs space-y-4"
        >
          <div>
            <label className="block text-sm font-semibold text-ink mb-1.5">
              {t('admin_login_prompt')}
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 absolute left-3.5 top-3.5 text-gray-400" />
              <input
                type="password"
                required
                autoFocus
                value={passwordInput}
                onChange={e => setPasswordInput(e.target.value)}
                placeholder="Enter admin password"
                className="w-full pl-10 pr-3.5 py-2.5 border border-line rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-civic bg-white"
              />
            </div>
          </div>

          {loginError && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-xl text-xs text-red-700 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0 text-status-overdue" />
              <span>{loginError}</span>
            </div>
          )}

          <Button type="submit" disabled={isLoggingIn} className="w-full py-2.5">
            {isLoggingIn ? (
              <span className="flex items-center justify-center gap-2">
                <RefreshCw className="w-4 h-4 animate-spin" />
                Signing in...
              </span>
            ) : (
              t('admin_login_btn')
            )}
          </Button>

          <p className="text-center text-[11px] text-gray-500 pt-1">
            Protected by server-side rate limiting and secure session authentication.
          </p>
        </form>
      </div>
    )
  }

  // Summary Metrics calculations
  const totalCount = metrics?.total_complaints ?? complaints.length
  const openCount =
    metrics?.open_complaints ??
    complaints.filter(c => c.status !== 'resolved').length
  const overdueCount =
    metrics?.overdue_complaints ??
    complaints.filter(c => c.is_overdue).length
  const avgHours = metrics?.avg_resolution_hours ?? 0

  return (
    <div className="space-y-6">
      {/* Top Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-3 border-b border-line">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-civic-light text-civic rounded-xl flex items-center justify-center border border-blue-200 shrink-0">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-ink">{t('admin_title')}</h1>
            <p className="text-xs text-gray-500">
              Authenticated Area Administrator • Session Active
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={loadAdminData}
            disabled={isLoadingData}
            className="p-2 text-gray-600 hover:text-civic hover:bg-gray-100 rounded-lg border border-line transition-colors"
            title="Refresh Complaints"
            aria-label="Refresh"
          >
            <RefreshCw className={`w-4 h-4 ${isLoadingData ? 'animate-spin' : ''}`} />
          </button>

          <Button
            variant="outline"
            onClick={handleLogout}
            className="text-xs py-2 px-3 flex items-center gap-1.5 border-line text-gray-700 hover:bg-red-50 hover:text-red-700 hover:border-red-200"
          >
            <LogOut className="w-3.5 h-3.5" />
            <span>{t('admin_logout_btn')}</span>
          </Button>
        </div>
      </div>

      {/* 4 Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="bg-white p-4 rounded-xl border border-line shadow-xs">
          <span className="text-xs font-medium text-gray-500">{t('admin_total_complaints')}</span>
          <div className="text-2xl font-extrabold text-ink mt-1">{totalCount}</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-line shadow-xs">
          <span className="text-xs font-medium text-gray-500">{t('admin_open_count')}</span>
          <div className="text-2xl font-extrabold text-status-assigned mt-1">{openCount}</div>
        </div>

        <div
          className={`p-4 rounded-xl border shadow-xs ${
            overdueCount > 0 ? 'bg-red-50/50 border-red-200' : 'bg-white border-line'
          }`}
        >
          <div className="flex items-center justify-between">
            <span
              className={`text-xs font-medium ${
                overdueCount > 0 ? 'text-status-overdue font-semibold' : 'text-gray-500'
              }`}
            >
              {t('admin_overdue_count')}
            </span>
            {overdueCount > 0 && <AlertTriangle className="w-3.5 h-3.5 text-status-overdue" />}
          </div>
          <div
            className={`text-2xl font-extrabold mt-1 ${
              overdueCount > 0 ? 'text-status-overdue' : 'text-gray-400'
            }`}
          >
            {overdueCount}
          </div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-line shadow-xs">
          <span className="text-xs font-medium text-gray-500">{t('admin_avg_resolution')}</span>
          <div className="text-2xl font-extrabold text-status-resolved mt-1">
            {avgHours > 0 ? (
              <span>
                {avgHours} <span className="text-xs font-normal text-gray-500">{t('admin_hours')}</span>
              </span>
            ) : (
              <span className="text-gray-400 text-lg font-normal">—</span>
            )}
          </div>
        </div>
      </div>

      {/* Tab Switcher */}
      <div className="flex items-center border-b border-line gap-2">
        <button
          onClick={() => setActiveTab('complaints')}
          className={`pb-2.5 px-3 text-sm font-semibold flex items-center gap-2 border-b-2 transition-colors ${
            activeTab === 'complaints'
              ? 'border-civic text-civic'
              : 'border-transparent text-gray-500 hover:text-ink'
          }`}
        >
          <Layers className="w-4 h-4" />
          <span>{t('admin_tab_complaints')}</span>
          <span className="ml-1 px-1.5 py-0.2 rounded-full text-[11px] bg-paper text-gray-600 border border-line">
            {complaints.length}
          </span>
        </button>

        <button
          onClick={() => setActiveTab('analytics')}
          className={`pb-2.5 px-3 text-sm font-semibold flex items-center gap-2 border-b-2 transition-colors ${
            activeTab === 'analytics'
              ? 'border-civic text-civic'
              : 'border-transparent text-gray-500 hover:text-ink'
          }`}
        >
          <BarChart2 className="w-4 h-4" />
          <span>{t('admin_tab_analytics')}</span>
        </button>
      </div>

      {/* TAB 1: COMPLAINTS MANAGEMENT */}
      {activeTab === 'complaints' && (
        <div className="space-y-4">
          {/* Filter Toolbar */}
          <div className="bg-white p-4 rounded-xl border border-line shadow-xs flex flex-col md:flex-row gap-3 items-stretch md:items-center justify-between">
            <div className="flex flex-wrap gap-2.5 items-center flex-1">
              {/* Status Select */}
              <select
                value={statusFilter}
                onChange={e => setStatusFilter(e.target.value)}
                className="px-3 py-2 border border-line rounded-lg text-xs font-medium bg-white text-ink focus:outline-none focus:ring-1 focus:ring-civic"
              >
                <option value="">{t('status')}: {t('admin_filter_all')}</option>
                <option value="submitted">{t('status_submitted')}</option>
                <option value="assigned">{t('status_assigned')}</option>
                <option value="in_progress">{t('status_in_progress')}</option>
                <option value="resolved">{t('status_resolved')}</option>
              </select>

              {/* Category Select */}
              <select
                value={categoryFilter}
                onChange={e => setCategoryFilter(e.target.value)}
                className="px-3 py-2 border border-line rounded-lg text-xs font-medium bg-white text-ink focus:outline-none focus:ring-1 focus:ring-civic"
              >
                <option value="">{t('category')}: {t('admin_filter_all')}</option>
                <option value="pothole">{t('cat_pothole')}</option>
                <option value="water">{t('cat_water')}</option>
                <option value="streetlight">{t('cat_streetlight')}</option>
                <option value="garbage">{t('cat_garbage')}</option>
                <option value="other">{t('cat_other')}</option>
              </select>

              {/* Overdue Checkbox */}
              <label className="flex items-center gap-2 cursor-pointer text-xs font-medium text-ink px-2.5 py-1.5 rounded-lg border border-line hover:bg-gray-50 select-none">
                <input
                  type="checkbox"
                  checked={overdueOnly}
                  onChange={e => setOverdueOnly(e.target.checked)}
                  className="rounded text-civic focus:ring-civic w-3.5 h-3.5"
                />
                <span className={overdueOnly ? 'text-status-overdue font-semibold' : ''}>
                  {t('admin_filter_overdue')}
                </span>
              </label>
            </div>

            {/* Quick Search */}
            <div className="relative w-full md:w-64">
              <Search className="w-4 h-4 absolute left-3 top-2.5 text-gray-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                placeholder="Search ID, locality, reporter..."
                className="w-full pl-9 pr-3 py-1.5 border border-line rounded-lg text-xs focus:outline-none focus:ring-1 focus:ring-civic"
              />
            </div>
          </div>

          {/* Master-Detail Layout */}
          {dataError && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-xs">
              {dataError}
            </div>
          )}

          {filteredComplaints.length === 0 ? (
            <div className="bg-white p-12 rounded-xl border border-line shadow-xs text-center space-y-2">
              <p className="text-sm font-medium text-gray-500">{t('admin_no_complaints')}</p>
              <button
                onClick={() => {
                  setStatusFilter('')
                  setCategoryFilter('')
                  setOverdueOnly(false)
                  setSearchQuery('')
                }}
                className="text-xs text-civic hover:underline"
              >
                Clear all filters
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
              {/* Left Column: Complaints List (5 cols on lg) */}
              <div className="lg:col-span-5 bg-white rounded-xl border border-line shadow-xs divide-y divide-line/60 max-h-[750px] overflow-y-auto">
                {filteredComplaints.map(c => {
                  const isSelected = c.tracking_id === selectedComplaintId
                  const catKey = CATEGORY_STRING_KEYS[c.category] || c.category

                  return (
                    <div
                      key={c.tracking_id}
                      onClick={() => setSelectedComplaintId(c.tracking_id)}
                      className={`p-3.5 cursor-pointer transition-colors text-left ${
                        isSelected
                          ? 'bg-blue-50/70 border-l-4 border-l-civic'
                          : 'hover:bg-gray-50/70'
                      }`}
                    >
                      <div className="flex items-center justify-between gap-2 mb-1">
                        <span className="font-mono text-xs font-bold text-ink">
                          {c.tracking_id}
                        </span>
                        <div className="flex items-center gap-1.5 shrink-0">
                          <StatusBadge status={c.status} isOverdue={c.is_overdue} />
                          <EscalationBadge level={c.escalation_level} />
                        </div>
                      </div>

                      <div className="flex items-center justify-between text-xs text-gray-600 mt-1">
                        <span className="font-medium text-ink">{t(catKey)}</span>
                        <span className="text-[11px] text-gray-500 truncate max-w-[150px]">
                          {c.locality}
                        </span>
                      </div>

                      <p className="text-xs text-gray-500 mt-1.5 line-clamp-2">
                        {c.description}
                      </p>

                      <div className="flex items-center justify-between text-[11px] text-gray-400 mt-2">
                        <span>{formatDateTime(c.created_at)}</span>
                        {c.is_overdue && (
                          <span className="text-status-overdue font-semibold flex items-center gap-1">
                            <AlertTriangle className="w-3 h-3" />
                            Overdue
                          </span>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>

              {/* Right Column: Selected Complaint Detail Inspection & Actions (7 cols on lg) */}
              <div className="lg:col-span-7">
                {selectedComplaint ? (
                  <div className="bg-white rounded-xl border border-line shadow-xs p-5 sm:p-6 space-y-6">
                    {/* Detail Header */}
                    <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 pb-4 border-b border-line">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-lg font-extrabold text-ink">
                          {selectedComplaint.tracking_id}
                        </span>
                        <button
                          onClick={() => handleCopyId(selectedComplaint.tracking_id)}
                          className="p-1 text-gray-400 hover:text-ink hover:bg-gray-100 rounded"
                          title="Copy Tracking ID"
                        >
                          {copiedId ? (
                            <Check className="w-4 h-4 text-status-resolved" />
                          ) : (
                            <Copy className="w-4 h-4" />
                          )}
                        </button>
                      </div>

                      <div className="flex items-center gap-2 flex-wrap">
                        <StatusBadge
                          status={selectedComplaint.status}
                          isOverdue={selectedComplaint.is_overdue}
                        />
                        <EscalationBadge level={selectedComplaint.escalation_level} />
                      </div>
                    </div>

                    {/* Overdue Banner if applicable */}
                    {selectedComplaint.is_overdue && (
                      <div className="p-3.5 bg-red-50 border border-status-overdue rounded-xl text-status-overdue flex items-start gap-3">
                        <AlertTriangle className="w-5 h-5 shrink-0 mt-0.5 text-status-overdue" />
                        <div className="space-y-0.5 text-xs">
                          <span className="font-bold block">
                            {t('overdue')}: {t('overdue_alert')}
                          </span>
                          <span>
                            Official SLA deadline was {formatDateTime(selectedComplaint.due_at)}.
                          </span>
                        </div>
                      </div>
                    )}

                    {/* Metadata Grid */}
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs bg-paper/60 p-3.5 rounded-xl border border-line/70">
                      <div>
                        <span className="text-gray-500 font-medium flex items-center gap-1">
                          <Tag className="w-3 h-3" />
                          {t('category')}
                        </span>
                        <div className="font-semibold text-ink mt-0.5">
                          {t(CATEGORY_STRING_KEYS[selectedComplaint.category] || selectedComplaint.category)}
                        </div>
                      </div>

                      <div>
                        <span className="text-gray-500 font-medium flex items-center gap-1">
                          <MapPin className="w-3 h-3" />
                          {t('locality')}
                        </span>
                        <div className="font-semibold text-ink mt-0.5 truncate">
                          {selectedComplaint.locality}
                        </div>
                      </div>

                      <div>
                        <span className="text-gray-500 font-medium flex items-center gap-1">
                          <Calendar className="w-3 h-3" />
                          {t('filed_on')}
                        </span>
                        <div className="font-semibold text-ink mt-0.5">
                          {formatDateTime(selectedComplaint.created_at)}
                        </div>
                      </div>

                      <div>
                        <span className="text-gray-500 font-medium flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {t('due_date')}
                        </span>
                        <div
                          className={`font-semibold mt-0.5 ${
                            selectedComplaint.is_overdue ? 'text-status-overdue' : 'text-ink'
                          }`}
                        >
                          {formatDateTime(selectedComplaint.due_at)}
                        </div>
                      </div>
                    </div>

                    {selectedComplaint.resolved_at && (
                      <div className="text-xs bg-emerald-50 text-status-resolved p-2.5 rounded-lg border border-emerald-200 flex items-center gap-2">
                        <CheckCircle2 className="w-4 h-4" />
                        <span>
                          <strong>{t('resolved_on')}:</strong> {formatDateTime(selectedComplaint.resolved_at)}
                        </span>
                      </div>
                    )}

                    {/* Description */}
                    <div>
                      <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-1">
                        {t('description')}
                      </h4>
                      <p className="text-sm text-ink bg-white p-3 rounded-lg border border-line/60 leading-relaxed whitespace-pre-wrap">
                        {selectedComplaint.description}
                      </p>
                    </div>

                    {/* Confidential Reporter Details (Admin Only) */}
                    <div className="p-3.5 bg-amber-50/70 border border-amber-200 rounded-xl space-y-1">
                      <span className="text-xs font-bold text-amber-900 flex items-center gap-1.5">
                        <Lock className="w-3.5 h-3.5" />
                        {t('admin_reporter_info')} (Confidential)
                      </span>
                      <div className="text-xs text-amber-950 flex flex-wrap gap-4 pt-1">
                        <span>
                          <strong>Name:</strong> {selectedComplaint.reporter_name || 'Anonymous'}
                        </span>
                        <span>
                          <strong>Phone:</strong> {selectedComplaint.reporter_phone || 'Not provided'}
                        </span>
                      </div>
                    </div>

                    {/* Photo & Unlink Action */}
                    {selectedComplaint.photo_url && (
                      <div className="space-y-2 pt-1 border-t border-line/60">
                        <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wider">
                          {t('photo')}
                        </h4>
                        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 p-3 bg-paper rounded-xl border border-line">
                          <div className="flex items-center gap-3">
                            <img
                              src={selectedComplaint.photo_url}
                              alt="Complaint attachment"
                              className="w-16 h-16 object-cover rounded-lg border border-line shadow-xs bg-white"
                            />
                            <a
                              href={selectedComplaint.photo_url}
                              target="_blank"
                              rel="noreferrer"
                              className="text-xs font-semibold text-civic flex items-center gap-1 hover:underline"
                            >
                              <Eye className="w-3.5 h-3.5" />
                              View original photo
                            </a>
                          </div>

                          <Button
                            variant="danger"
                            onClick={handleUnlinkPhoto}
                            disabled={isUnlinkingPhoto}
                            className="text-xs py-1.5 px-3 flex items-center gap-1.5"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                            <span>{t('admin_unlink_photo')}</span>
                          </Button>
                        </div>
                      </div>
                    )}

                    {/* Action Feedback Messages */}
                    {actionSuccess && (
                      <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-xs text-status-resolved flex items-center gap-2">
                        <CheckCircle2 className="w-4 h-4 shrink-0" />
                        <span>{actionSuccess}</span>
                      </div>
                    )}
                    {actionError && (
                      <div className="p-3 bg-red-50 border border-red-200 rounded-xl text-xs text-red-700 flex items-center gap-2">
                        <AlertTriangle className="w-4 h-4 shrink-0 text-status-overdue" />
                        <span>{actionError}</span>
                      </div>
                    )}

                    {/* Status Update Form Controls */}
                    <div className="pt-2 border-t border-line/80 space-y-3">
                      <h4 className="text-sm font-bold text-ink flex items-center gap-2">
                        <Send className="w-4 h-4 text-civic" />
                        {t('admin_update_status')}
                      </h4>

                      {ALLOWED_NEXT_STATUS[selectedComplaint.status] ? (
                        <form onSubmit={handleStatusUpdate} className="space-y-3">
                          <div className="text-xs text-gray-600">
                            <strong>{t('admin_next_status')}: </strong>
                            <span className="font-semibold text-civic">
                              {t(STATUS_STRING_KEYS[ALLOWED_NEXT_STATUS[selectedComplaint.status]] || ALLOWED_NEXT_STATUS[selectedComplaint.status])}
                            </span>
                          </div>

                          <div>
                            <label className="block text-xs font-medium text-gray-600 mb-1">
                              {t('admin_status_note')}
                            </label>
                            <input
                              type="text"
                              maxLength={500}
                              value={statusNote}
                              onChange={e => setStatusNote(e.target.value)}
                              placeholder="e.g. Assigned to Line Inspector, team dispatched"
                              className="w-full px-3 py-2 border border-line rounded-lg text-xs focus:outline-none focus:ring-1 focus:ring-civic bg-white"
                            />
                          </div>

                          <Button
                            type="submit"
                            disabled={isUpdatingStatus}
                            className="w-full text-xs py-2.5 flex items-center justify-center gap-2"
                          >
                            {isUpdatingStatus ? (
                              <>
                                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                                Updating...
                              </>
                            ) : (
                              <>
                                <span>{t('admin_update_status')}</span>
                                <span>→</span>
                                <span>
                                  {t(STATUS_STRING_KEYS[ALLOWED_NEXT_STATUS[selectedComplaint.status]] || ALLOWED_NEXT_STATUS[selectedComplaint.status])}
                                </span>
                              </>
                            )}
                          </Button>
                        </form>
                      ) : (
                        <div className="p-3 bg-gray-50 border border-line rounded-lg text-xs text-gray-500 flex items-center gap-2">
                          <CheckCircle2 className="w-4 h-4 text-status-resolved" />
                          <span>{t('admin_already_resolved')}</span>
                        </div>
                      )}
                    </div>

                    {/* Status History Timeline */}
                    <div className="pt-2 border-t border-line/80 space-y-3">
                      <h4 className="text-sm font-bold text-ink">{t('history')}</h4>

                      {isLoadingHistory ? (
                        <div className="text-xs text-gray-400 py-3 text-center">Loading audit log...</div>
                      ) : historyList.length === 0 ? (
                        <div className="text-xs text-gray-400 py-2">No status changes recorded yet.</div>
                      ) : (
                        <div className="space-y-2.5">
                          {historyList.map((entry, idx) => (
                            <div
                              key={idx}
                              className="p-3 rounded-lg border border-line/60 bg-paper/40 text-xs space-y-1"
                            >
                              <div className="flex items-center justify-between">
                                <span className="text-gray-500 font-mono text-[11px]">
                                  {formatDateTime(entry.changed_at)} ({entry.changed_by})
                                </span>
                                <StatusBadge status={entry.status} />
                              </div>
                              {entry.note && (
                                <p className="text-gray-700 italic pl-1 border-l-2 border-civic/40 mt-1">
                                  "{entry.note}"
                                </p>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                ) : (
                  <div className="bg-white rounded-xl border border-line shadow-xs p-12 text-center text-gray-400 text-sm">
                    Select a complaint from the list to view its details and update status.
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 2: ANALYTICS & PERFORMANCE CHARTS */}
      {activeTab === 'analytics' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Chart 1: Complaints by Category */}
            <div className="bg-white p-5 rounded-xl border border-line shadow-xs space-y-4">
              <h3 className="font-bold text-sm text-ink">Complaints by Category</h3>
              <div className="space-y-3 pt-1">
                {(['pothole', 'water', 'streetlight', 'garbage', 'other'] as const).map(cat => {
                  const count = complaints.filter(c => c.category === cat).length
                  const pct = complaints.length > 0 ? (count / complaints.length) * 100 : 0
                  const catLabel = t(CATEGORY_STRING_KEYS[cat] || cat)

                  return (
                    <div key={cat} className="space-y-1">
                      <div className="flex justify-between text-xs font-medium">
                        <span className="text-ink">{catLabel}</span>
                        <span className="text-gray-500">{count} ({Math.round(pct)}%)</span>
                      </div>
                      <div className="w-full bg-paper rounded-md h-4 overflow-hidden border border-line/60">
                        <div
                          className="bg-civic h-full transition-all duration-500 rounded-xs"
                          style={{ width: `${Math.max(pct, count > 0 ? 5 : 0)}%` }}
                        />
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Chart 2: Complaints by Status */}
            <div className="bg-white p-5 rounded-xl border border-line shadow-xs space-y-4">
              <h3 className="font-bold text-sm text-ink">Complaints by Status</h3>
              <div className="space-y-3 pt-1">
                {[
                  { status: 'submitted', color: 'bg-status-submitted' },
                  { status: 'assigned', color: 'bg-status-assigned' },
                  { status: 'in_progress', color: 'bg-status-progress' },
                  { status: 'resolved', color: 'bg-status-resolved' },
                ].map(({ status, color }) => {
                  const count = complaints.filter(c => c.status === status).length
                  const pct = complaints.length > 0 ? (count / complaints.length) * 100 : 0
                  const label = t(STATUS_STRING_KEYS[status] || status)

                  return (
                    <div key={status} className="space-y-1">
                      <div className="flex justify-between text-xs font-medium">
                        <span className="text-ink">{label}</span>
                        <span className="text-gray-500">{count} ({Math.round(pct)}%)</span>
                      </div>
                      <div className="w-full bg-paper rounded-md h-4 overflow-hidden border border-line/60">
                        <div
                          className={`${color} h-full transition-all duration-500 rounded-xs`}
                          style={{ width: `${Math.max(pct, count > 0 ? 5 : 0)}%` }}
                        />
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          </div>

          {/* Average Resolution Time by Department */}
          <div className="bg-white p-5 rounded-xl border border-line shadow-xs space-y-4">
            <h3 className="font-bold text-sm text-ink">Average Resolution Time per Department</h3>
            {metrics?.departments && metrics.departments.some(d => d.resolved > 0) ? (
              <div className="space-y-3 pt-1">
                {metrics.departments.map(d => {
                  const catLabel = t(CATEGORY_STRING_KEYS[d.category] || d.category)
                  const hours = d.avg_resolution_hours || 0
                  const maxHours = Math.max(...metrics.departments.map(m => m.avg_resolution_hours || 0), 1)
                  const barWidth = maxHours > 0 ? (hours / maxHours) * 100 : 0

                  return (
                    <div key={d.category} className="space-y-1">
                      <div className="flex justify-between text-xs font-medium">
                        <span className="text-ink">{catLabel}</span>
                        <span className="text-gray-500">
                          {d.resolved > 0 ? `${hours} ${t('admin_hours')}` : '—'}
                        </span>
                      </div>
                      <div className="w-full bg-paper rounded-md h-4 overflow-hidden border border-line/60">
                        {d.resolved > 0 && hours > 0 ? (
                          <div
                            className="bg-status-resolved h-full transition-all duration-500 rounded-xs flex items-center px-2 text-[10px] text-white"
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
            ) : (
              <div className="p-8 text-center text-xs text-gray-500 bg-paper/50 rounded-xl border border-dashed border-line">
                No complaints have been resolved yet. Average resolution times will appear once the first fix is completed.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
