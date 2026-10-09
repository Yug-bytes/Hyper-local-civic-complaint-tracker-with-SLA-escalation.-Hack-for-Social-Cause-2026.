import React, { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import {
  CheckCircle2,
  Copy,
  Check,
  Search,
  AlertCircle,
  Clock,
  Send,
  Building,
  Shield,
  FileText,
  MapPin,
  User,
  Phone,
} from 'lucide-react'
import { useI18n, CATEGORY_STRING_KEYS } from '../lib/i18n'
import { api, type Department, type ApiError } from '../lib/api'
import { Button } from '../components/ui/Button'
import { PhotoDropzone } from '../components/PhotoDropzone'

export const CitizenPage: React.FC = () => {
  const { t } = useI18n()
  const [searchParams] = useSearchParams()

  // Data states
  const [departments, setDepartments] = useState<Department[]>([])
  const [selectedCategory, setSelectedCategory] = useState<string>(
    searchParams.get('category') || 'pothole'
  )

  useEffect(() => {
    const cat = searchParams.get('category')
    if (cat) {
      setSelectedCategory(cat)
    }
  }, [searchParams])
  const [description, setDescription] = useState<string>('')
  const [locality, setLocality] = useState<string>('')
  const [photoFile, setPhotoFile] = useState<File | null>(null)
  const [name, setName] = useState<string>('')
  const [phone, setPhone] = useState<string>('')

  // UI / Submission states
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)
  const [submittedTrackingId, setSubmittedTrackingId] = useState<string | null>(null)
  const [copied, setCopied] = useState<boolean>(false)
  const [cooldownRemaining, setCooldownRemaining] = useState<number>(0)

  // Load departments metadata
  useEffect(() => {
    api
      .getDepartments()
      .then((data: Department[]) => setDepartments(data))
      .catch(() => {
        // Fallback default departments if API unavailable
      })
  }, [])

  // Cooldown countdown timer
  useEffect(() => {
    if (cooldownRemaining <= 0) return
    const timer = setInterval(() => {
      setCooldownRemaining((prev: number) => (prev > 0 ? prev - 1 : 0))
    }, 1000)
    return () => clearInterval(timer)
  }, [cooldownRemaining])

  const selectedDept = departments.find((d: Department) => d.category === selectedCategory)

  const handleCopyTrackingId = () => {
    if (!submittedTrackingId) return
    navigator.clipboard.writeText(submittedTrackingId)
    setCopied(true)
    setTimeout(() => setCopied(false), 2500)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setErrorMsg(null)

    // Basic client validations
    if (!description.trim()) {
      setErrorMsg('Description is required.')
      return
    }
    if (!locality.trim()) {
      setErrorMsg('Locality is required.')
      return
    }
    if (phone.trim() && !/^\d{10}$/.test(phone.trim())) {
      setErrorMsg('Phone must be exactly 10 digits (e.g. 9876543210).')
      return
    }

    setIsSubmitting(true)
    try {
      const formData = new FormData()
      formData.append('category', selectedCategory)
      formData.append('description', description.trim())
      formData.append('locality', locality.trim())
      if (name.trim()) formData.append('name', name.trim())
      if (phone.trim()) formData.append('phone', phone.trim())
      if (photoFile) formData.append('photo', photoFile)

      const result = await api.createComplaint(formData)
      setSubmittedTrackingId(result.tracking_id)
      setCooldownRemaining(30) // start 30-second cooldown
    } catch (err: unknown) {
      const apiErr = err as ApiError
      if (apiErr?.code === 'RATE_LIMITED') {
        // Parse seconds from rate limit message if available
        const match = apiErr.message.match(/(\d+)\s*seconds/)
        const secs = match ? parseInt(match[1], 10) : 30
        setCooldownRemaining(secs)
      }
      setErrorMsg(apiErr?.message || 'Failed to submit complaint. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleResetForm = () => {
    setSubmittedTrackingId(null)
    setDescription('')
    setLocality('')
    setPhotoFile(null)
    setName('')
    setPhone('')
    setErrorMsg(null)
  }

  // ────────────────────────────────────────────────────────────
  // Success Confirmation View
  // ────────────────────────────────────────────────────────────
  if (submittedTrackingId) {
    return (
      <div className="max-w-xl mx-auto space-y-6 animate-fade-in">
        <div className="bg-white p-6 sm:p-8 rounded-2xl border border-line shadow-sm text-center space-y-6">
          <div className="w-16 h-16 bg-green-100 text-status-resolved rounded-full mx-auto flex items-center justify-center">
            <CheckCircle2 className="w-10 h-10" />
          </div>

          <div className="space-y-1">
            <h2 className="text-2xl font-bold text-ink">
              {t('complaint_saved')}
            </h2>
            <p className="text-sm text-gray-600">
              {t('tracking_id_instruction')}
            </p>
          </div>

          {/* Tracking ID Display Card */}
          <div className="p-4 bg-paper rounded-xl border border-line flex flex-col sm:flex-row items-center justify-between gap-3">
            <div className="text-left">
              <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider block">
                {t('tracking_id_label')}
              </span>
              <span className="text-2xl font-mono font-bold text-civic tracking-wider">
                {submittedTrackingId}
              </span>
            </div>

            <button
              onClick={handleCopyTrackingId}
              className="inline-flex items-center px-4 py-2 border border-line bg-white hover:bg-gray-50 rounded-lg text-sm font-semibold text-ink shadow-2xs transition-colors"
            >
              {copied ? (
                <>
                  <Check className="w-4 h-4 mr-1.5 text-status-resolved" />
                  <span>Copied</span>
                </>
              ) : (
                <>
                  <Copy className="w-4 h-4 mr-1.5 text-gray-500" />
                  <span>Copy ID</span>
                </>
              )}
            </button>
          </div>

          {/* Department routing info */}
          {selectedDept && (
            <div className="text-left p-3.5 bg-civic-light border border-blue-200 rounded-lg text-xs space-y-1">
              <div className="flex items-center font-bold text-civic">
                <Building className="w-3.5 h-3.5 mr-1" />
                <span>Routed to: {selectedDept.department_name}</span>
              </div>
              <div className="text-gray-600 flex items-center">
                <Clock className="w-3.5 h-3.5 mr-1 text-gray-400" />
                <span>
                  Official SLA: {selectedDept.sla_days} days to resolve
                </span>
              </div>
            </div>
          )}

          {/* Action buttons */}
          <div className="flex flex-col sm:flex-row gap-3 pt-2">
            <Link to={`/track?id=${submittedTrackingId}`} className="flex-1">
              <Button variant="primary" className="w-full">
                <Search className="w-4 h-4 mr-2" />
                {t('check_status')}
              </Button>
            </Link>

            <Button
              variant="secondary"
              onClick={handleResetForm}
              className="flex-1"
            >
              {t('file_another')}
            </Button>
          </div>
        </div>
      </div>
    )
  }

  // ────────────────────────────────────────────────────────────
  // Complaint Submission Form View
  // ────────────────────────────────────────────────────────────
  return (
    <div className="max-w-xl mx-auto space-y-6">
      <div className="space-y-1 text-center sm:text-left">
        <h2 className="text-2xl sm:text-3xl font-bold text-ink">
          {t('file_complaint')}
        </h2>
        <p className="text-sm text-gray-600">
          Report civic issues in your area. Complaints are automatically routed to the responsible department with fixed resolution deadlines.
        </p>
      </div>

      <form
        onSubmit={handleSubmit}
        className="bg-white p-5 sm:p-7 rounded-2xl border border-line shadow-xs space-y-5"
      >
        {/* Error Alert */}
        {errorMsg && (
          <div className="p-3.5 rounded-lg bg-red-50 border border-red-200 text-status-overdue text-sm flex items-start space-x-2">
            <AlertCircle className="w-5 h-5 shrink-0 mt-0.5 text-status-overdue" />
            <div className="flex-1">{errorMsg}</div>
          </div>
        )}

        {/* Cooldown Timer Alert */}
        {cooldownRemaining > 0 && (
          <div className="p-3 rounded-lg bg-blue-50 border border-blue-200 text-civic text-xs font-semibold flex items-center space-x-2">
            <Clock className="w-4 h-4 animate-spin" />
            <span>
              {t('error_cooldown', { seconds: cooldownRemaining })}
            </span>
          </div>
        )}

        {/* 1. Category Selection */}
        <div className="space-y-1.5">
          <label className="text-sm font-semibold text-ink flex items-center justify-between">
            <span className="flex items-center">
              <Building className="w-4 h-4 mr-1.5 text-civic" />
              {t('category')}
            </span>
            {selectedDept && (
              <span className="text-xs font-normal text-civic bg-civic-light px-2 py-0.5 rounded">
                SLA: {selectedDept.sla_days} days
              </span>
            )}
          </label>
          <select
            value={selectedCategory}
            onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setSelectedCategory(e.target.value)}
            className="w-full px-3 py-2.5 border border-line rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-civic"
          >
            {departments.length > 0 ? (
              departments.map((dept: Department) => (
                <option key={dept.category} value={dept.category}>
                  {t(CATEGORY_STRING_KEYS[dept.category] || dept.category)} ({dept.department_name})
                </option>
              ))
            ) : (
              <>
                <option value="pothole">{t('cat_pothole')}</option>
                <option value="water">{t('cat_water')}</option>
                <option value="streetlight">{t('cat_streetlight')}</option>
                <option value="garbage">{t('cat_garbage')}</option>
                <option value="other">{t('cat_other')}</option>
              </>
            )}
          </select>
          {selectedDept && (
            <p className="text-xs text-gray-500">
              Assigned to: <strong className="text-ink">{selectedDept.responsible_role}</strong> ({selectedDept.department_name})
            </p>
          )}
        </div>

        {/* 2. Description Field */}
        <div className="space-y-1.5">
          <div className="flex justify-between items-center">
            <label className="text-sm font-semibold text-ink flex items-center">
              <FileText className="w-4 h-4 mr-1.5 text-civic" />
              {t('description')}
            </label>
            <span
              className={`text-xs ${
                description.length > 900 ? 'text-status-overdue font-bold' : 'text-gray-400'
              }`}
            >
              {description.length} / 1000
            </span>
          </div>
          <textarea
            rows={3}
            maxLength={1000}
            required
            placeholder={t('description_help')}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="w-full px-3 py-2 border border-line rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-civic"
          />
        </div>

        {/* 3. Locality Field */}
        <div className="space-y-1.5">
          <div className="flex justify-between items-center">
            <label className="text-sm font-semibold text-ink flex items-center">
              <MapPin className="w-4 h-4 mr-1.5 text-civic" />
              {t('locality')}
            </label>
            <span className="text-xs text-gray-400">
              {locality.length} / 100
            </span>
          </div>
          <input
            type="text"
            maxLength={100}
            required
            placeholder="e.g. Near Water Tank, Ward 12, Sector 4"
            value={locality}
            onChange={(e) => setLocality(e.target.value)}
            className="w-full px-3 py-2 border border-line rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-civic"
          />
        </div>

        {/* 4. Photo Dropzone */}
        <PhotoDropzone
          selectedFile={photoFile}
          onFileSelect={(file) => setPhotoFile(file)}
        />

        {/* 5. Optional Reporter Details */}
        <div className="pt-2 border-t border-line space-y-3">
          <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider flex items-center">
            <Shield className="w-3.5 h-3.5 mr-1 text-civic" />
            <span>Optional Contact Information</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1 flex items-center">
                <User className="w-3 h-3 mr-1 text-gray-400" />
                {t('name')}
              </label>
              <input
                type="text"
                maxLength={80}
                placeholder="Citizen Name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full px-3 py-1.5 border border-line rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-civic"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1 flex items-center">
                <Phone className="w-3 h-3 mr-1 text-gray-400" />
                {t('phone')}
              </label>
              <input
                type="tel"
                maxLength={10}
                placeholder="10-digit mobile"
                value={phone}
                onChange={(e) => setPhone(e.target.value.replace(/\D/g, ''))}
                className="w-full px-3 py-1.5 border border-line rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-civic"
              />
            </div>
          </div>

          <p className="text-xs text-gray-500 bg-paper p-2 rounded border border-line/60">
            {t('consent')}
          </p>
        </div>

        {/* Submit Button */}
        <Button
          type="submit"
          variant="primary"
          size="lg"
          isLoading={isSubmitting}
          disabled={cooldownRemaining > 0}
          className="w-full"
        >
          {isSubmitting ? (
            t('submitting')
          ) : (
            <>
              <Send className="w-4 h-4 mr-2" />
              {t('send_complaint')}
            </>
          )}
        </Button>
      </form>
    </div>
  )
}
