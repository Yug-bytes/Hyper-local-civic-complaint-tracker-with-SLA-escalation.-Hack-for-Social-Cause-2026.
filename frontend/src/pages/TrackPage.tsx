import React, { useEffect, useState } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import {
  Search,
  AlertCircle,
  Clock,
  Calendar,
  MapPin,
  Building,
  Image as ImageIcon,
  CheckCircle2,
  Copy,
  Check,
  AlertTriangle,
  FileText,
  PlusCircle,
} from 'lucide-react'
import { useI18n, CATEGORY_STRING_KEYS } from '../lib/i18n'
import { api, type ComplaintPublic, type StatusHistory, type ApiError } from '../lib/api'
import { formatDateTime, isPastDeadline } from '../lib/date'
import { StatusBadge } from '../components/ui/StatusBadge'
import { StatusStepper } from '../components/StatusStepper'
import { Button } from '../components/ui/Button'

export const TrackPage: React.FC = () => {
  const { t } = useI18n()
  const [searchParams, setSearchParams] = useSearchParams()

  const [inputTrackingId, setInputTrackingId] = useState<string>('')
  const [complaint, setComplaint] = useState<ComplaintPublic | null>(null)
  const [isLoading, setIsLoading] = useState<boolean>(false)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)
  const [copied, setCopied] = useState<boolean>(false)

  const fetchStatus = React.useCallback(async (trackingId: string) => {
    if (!trackingId.trim()) return

    setIsLoading(true)
    setErrorMsg(null)

    try {
      const data = await api.getComplaintStatus(trackingId)
      setComplaint(data)
    } catch (err: unknown) {
      setComplaint(null)
      const apiErr = err as ApiError
      setErrorMsg(
        apiErr?.message || t('no_complaint_found')
      )
    } finally {
      setIsLoading(false)
    }
  }, [t])

  // Check URL query param on mount or change
  useEffect(() => {
    const urlId = searchParams.get('id')
    if (urlId) {
      const cleanId = urlId.trim().toUpperCase()
      setInputTrackingId(cleanId)
      fetchStatus(cleanId)
    }
  }, [searchParams, fetchStatus])

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!inputTrackingId.trim()) return
    const cleanId = inputTrackingId.trim().toUpperCase()
    setSearchParams({ id: cleanId })
    fetchStatus(cleanId)
  }

  const handleCopyId = () => {
    if (!complaint) return
    navigator.clipboard.writeText(complaint.tracking_id)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const isOverdue = Boolean(
    complaint &&
    complaint.status !== 'resolved' &&
    isPastDeadline(complaint.due_at)
  )

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Page Header */}
      <div className="text-center sm:text-left space-y-1">
        <h2 className="text-2xl sm:text-3xl font-bold text-ink">
          {t('check_status')}
        </h2>
        <p className="text-sm text-gray-600">
          Enter your unique tracking ID (e.g. <code>CT-261009-TGCT</code>) to view the live status, resolution deadline, and department history.
        </p>
      </div>

      {/* Search Bar */}
      <form
        onSubmit={handleSearchSubmit}
        className="bg-white p-4 sm:p-5 rounded-2xl border border-line shadow-xs flex flex-col sm:flex-row gap-2.5"
      >
        <div className="relative flex-1">
          <Search className="w-5 h-5 absolute left-3.5 top-3 text-gray-400" />
          <input
            type="text"
            required
            placeholder={t('tracking_id_placeholder')}
            value={inputTrackingId}
            onChange={(e) => setInputTrackingId(e.target.value.toUpperCase())}
            className="w-full pl-10 pr-3 py-2.5 border border-line rounded-xl text-sm font-mono tracking-wider uppercase focus:outline-none focus:ring-2 focus:ring-civic"
          />
        </div>

        <Button
          type="submit"
          variant="primary"
          isLoading={isLoading}
          className="sm:w-auto w-full px-6 py-2.5"
        >
          <Search className="w-4 h-4 mr-1.5" />
          {t('check')}
        </Button>
      </form>

      {/* Error state */}
      {errorMsg && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-status-overdue text-sm flex items-start space-x-3">
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5 text-status-overdue" />
          <div>
            <p className="font-semibold">{errorMsg}</p>
            <p className="text-xs text-red-600 mt-1">
              Please check that you entered the tracking ID accurately, including the prefix (e.g. CT-261009-XXXX).
            </p>
          </div>
        </div>
      )}

      {/* Loading state skeleton */}
      {isLoading && (
        <div className="bg-white p-8 rounded-2xl border border-line shadow-xs text-center space-y-3">
          <div className="w-10 h-10 border-4 border-civic border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-sm text-gray-500 font-medium">Fetching complaint status from department database...</p>
        </div>
      )}

      {/* Active Complaint Status View */}
      {complaint && !isLoading && (
        <div className="space-y-6 animate-fade-in">
          {/* Overdue Alert Banner (Requirement 3 from designsystem.md) */}
          {isOverdue && (
            <div className="p-4 rounded-xl bg-red-50 border border-status-overdue text-status-overdue flex items-start space-x-3 shadow-xs">
              <AlertTriangle className="w-5 h-5 shrink-0 mt-0.5 text-status-overdue animate-pulse" />
              <div className="space-y-0.5">
                <span className="font-bold text-sm block">
                  {t('overdue')}: {t('overdue_alert')}
                </span>
                <span className="text-xs text-red-800">
                  The official SLA resolution deadline ({formatDateTime(complaint.due_at)}) has passed. This complaint has been flagged for administrative escalation.
                </span>
              </div>
            </div>
          )}

          {/* Stepper Progression Card */}
          <div className="bg-white p-6 rounded-2xl border border-line shadow-xs space-y-4">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 pb-4 border-b border-line">
              <div className="flex items-center space-x-2">
                <span className="font-mono text-xl font-bold text-ink">
                  {complaint.tracking_id}
                </span>
                <button
                  onClick={handleCopyId}
                  className="p-1.5 hover:bg-gray-100 rounded text-gray-500 hover:text-ink transition-colors"
                  title="Copy Tracking ID"
                >
                  {copied ? <Check className="w-4 h-4 text-status-resolved" /> : <Copy className="w-4 h-4" />}
                </button>
              </div>

              <StatusBadge status={complaint.status} isOverdue={isOverdue} />
            </div>

            {/* Visual 4-Stage Stepper */}
            <StatusStepper currentStatus={complaint.status} />
          </div>

          {/* Complaint Metadata & Details Card */}
          <div className="bg-white p-6 rounded-2xl border border-line shadow-xs space-y-6">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {/* Category */}
              <div className="flex items-start space-x-3">
                <Building className="w-5 h-5 text-civic shrink-0 mt-0.5" />
                <div>
                  <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider block">
                    {t('category')}
                  </span>
                  <span className="text-sm font-medium text-ink">
                    {t(CATEGORY_STRING_KEYS[complaint.category] || complaint.category)}
                  </span>
                </div>
              </div>

              {/* Locality */}
              <div className="flex items-start space-x-3">
                <MapPin className="w-5 h-5 text-civic shrink-0 mt-0.5" />
                <div>
                  <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider block">
                    {t('locality')}
                  </span>
                  <span className="text-sm font-medium text-ink">
                    {complaint.locality}
                  </span>
                </div>
              </div>

              {/* Filed Date */}
              <div className="flex items-start space-x-3">
                <Calendar className="w-5 h-5 text-civic shrink-0 mt-0.5" />
                <div>
                  <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider block">
                    {t('filed_on')}
                  </span>
                  <span className="text-sm font-medium text-ink">
                    {formatDateTime(complaint.created_at)}
                  </span>
                </div>
              </div>

              {/* Due Date */}
              <div className="flex items-start space-x-3">
                <Clock className="w-5 h-5 text-civic shrink-0 mt-0.5" />
                <div>
                  <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider block">
                    {t('due_date')}
                  </span>
                  <span
                    className={`text-sm font-medium ${
                      isOverdue ? 'text-status-overdue font-bold' : 'text-ink'
                    }`}
                  >
                    {formatDateTime(complaint.due_at)}
                  </span>
                </div>
              </div>
            </div>

            {/* Resolved timestamp if completed */}
            {complaint.resolved_at && (
              <div className="p-3 bg-green-50 border border-green-200 rounded-lg flex items-center space-x-2 text-status-resolved text-sm font-medium">
                <CheckCircle2 className="w-4 h-4" />
                <span>
                  {t('resolved_on')}: {formatDateTime(complaint.resolved_at)}
                </span>
              </div>
            )}

            {/* Description */}
            <div className="space-y-1.5 pt-4 border-t border-line">
              <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider block flex items-center">
                <FileText className="w-3.5 h-3.5 mr-1 text-civic" />
                {t('description')}
              </span>
              <p className="text-sm text-gray-800 bg-paper p-3.5 rounded-lg border border-line/60 whitespace-pre-wrap leading-relaxed">
                {complaint.description}
              </p>
            </div>

            {/* Attached Photo Preview (Signed Ephemeral URL) */}
            {complaint.photo_url && (
              <div className="space-y-2 pt-4 border-t border-line">
                <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider block flex items-center">
                  <ImageIcon className="w-3.5 h-3.5 mr-1 text-civic" />
                  {t('photo')}
                </span>
                <div className="rounded-xl overflow-hidden border border-line bg-gray-50 p-2 flex justify-center">
                  <img
                    src={complaint.photo_url}
                    alt="Complaint attachment"
                    className="max-h-72 object-contain rounded-lg shadow-2xs"
                  />
                </div>
                <p className="text-2xs text-gray-400 text-center">
                  Secure time-limited photo access URL.
                </p>
              </div>
            )}
          </div>

          {/* Status History Timeline */}
          {complaint.history && complaint.history.length > 0 && (
            <div className="bg-white p-6 rounded-2xl border border-line shadow-xs space-y-4">
              <h3 className="text-base font-bold text-ink flex items-center">
                <Clock className="w-4 h-4 mr-2 text-civic" />
                {t('history')}
              </h3>

              <div className="space-y-4 relative before:absolute before:left-3 before:top-2 before:bottom-2 before:w-0.5 before:bg-line pl-6">
                {complaint.history.map((entry: StatusHistory, idx: number) => (
                  <div key={idx} className="relative space-y-1">
                    {/* Timeline bullet */}
                    <div className="absolute -left-6 top-1.5 w-2.5 h-2.5 rounded-full bg-civic border-2 border-white shadow-xs" />

                    <div className="flex flex-wrap items-center gap-2">
                      <StatusBadge status={entry.status} />
                      <span className="text-xs text-gray-500">
                        {formatDateTime(entry.changed_at)}
                      </span>
                    </div>

                    {entry.note && (
                      <p className="text-xs text-gray-700 bg-paper p-2 rounded border border-line/60 mt-1">
                        {entry.note}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Initial Empty state when no search performed yet */}
      {!complaint && !isLoading && !errorMsg && (
        <div className="bg-white p-8 rounded-2xl border border-line shadow-xs text-center space-y-3">
          <Search className="w-12 h-12 text-gray-300 mx-auto" />
          <h3 className="text-base font-semibold text-ink">
            Track Your Complaint Progress
          </h3>
          <p className="text-xs text-gray-500 max-w-sm mx-auto">
            All submitted complaints receive a tracking code like <code>CT-261009-XXXX</code>. Enter your code above to follow every action taken by municipal engineers.
          </p>
          <div className="pt-2">
            <Link to="/">
              <Button variant="outline" size="sm">
                <PlusCircle className="w-4 h-4 mr-1.5" />
                {t('file_complaint')}
              </Button>
            </Link>
          </div>
        </div>
      )}
    </div>
  )
}
