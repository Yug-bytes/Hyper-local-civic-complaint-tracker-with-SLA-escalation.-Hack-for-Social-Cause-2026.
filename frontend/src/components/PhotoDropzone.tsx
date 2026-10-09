import React, { useRef, useState } from 'react'
import { UploadCloud, X, Image as ImageIcon, AlertTriangle } from 'lucide-react'
import { useI18n } from '@/lib/i18n'

interface PhotoDropzoneProps {
  selectedFile: File | null
  onFileSelect: (file: File | null) => void
  error?: string | null
}

const MAX_PHOTO_MB = 5
const MAX_PHOTO_BYTES = MAX_PHOTO_MB * 1024 * 1024

export const PhotoDropzone: React.FC<PhotoDropzoneProps> = ({ selectedFile, onFileSelect, error }) => {
  const { t } = useI18n()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [validationError, setValidationError] = useState<string | null>(null)

  const validateAndSetFile = (file: File) => {
    setValidationError(null)

    // Check size
    if (file.size > MAX_PHOTO_BYTES) {
      setValidationError(`Photo must be ${MAX_PHOTO_MB} MB or smaller.`)
      return
    }

    // Check type
    if (!['image/jpeg', 'image/png'].includes(file.type)) {
      setValidationError('Photo must be a JPG or PNG file.')
      return
    }

    onFileSelect(file)
    const url = URL.createObjectURL(file)
    setPreviewUrl(url)
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0])
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0])
    }
  }

  const handleRemove = () => {
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl)
    }
    setPreviewUrl(null)
    onFileSelect(null)
    setValidationError(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="text-sm font-semibold text-ink flex items-center">
          <ImageIcon className="w-4 h-4 mr-1.5 text-civic" />
          {t('photo')}
        </label>
        {selectedFile && (
          <button
            type="button"
            onClick={handleRemove}
            className="text-xs text-status-overdue hover:underline flex items-center"
          >
            <X className="w-3.5 h-3.5 mr-0.5" />
            Remove
          </button>
        )}
      </div>

      {previewUrl ? (
        <div className="relative rounded-lg overflow-hidden border border-line bg-gray-50 flex items-center justify-center p-2">
          <img
            src={previewUrl}
            alt="Complaint preview"
            className="max-h-48 rounded object-contain"
          />
          <div className="absolute bottom-2 left-2 right-2 bg-black/60 text-white text-xs px-2 py-1 rounded truncate backdrop-blur-xs flex justify-between items-center">
            <span className="truncate">{selectedFile?.name}</span>
            <span className="text-gray-300 ml-2">
              {((selectedFile?.size || 0) / (1024 * 1024)).toFixed(1)} MB
            </span>
          </div>
        </div>
      ) : (
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-lg p-5 text-center cursor-pointer transition-colors ${
            isDragging
              ? 'border-civic bg-civic-light'
              : 'border-line hover:border-civic hover:bg-gray-50'
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept="image/jpeg,image/png"
            className="hidden"
            onChange={handleInputChange}
          />
          <UploadCloud className="w-8 h-8 mx-auto text-civic mb-2" />
          <p className="text-sm font-medium text-ink">
            Click to upload or drag and drop a photo
          </p>
          <p className="text-xs text-gray-500 mt-1">PNG, JPG up to 5 MB</p>
        </div>
      )}

      {/* Privacy note */}
      <div className="flex items-start text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded p-2">
        <AlertTriangle className="w-4 h-4 mr-1.5 shrink-0 mt-0.5 text-amber-600" />
        <span>{t('photo_warning')}</span>
      </div>

      {(validationError || error) && (
        <p className="text-xs font-semibold text-status-overdue">
          {validationError || error}
        </p>
      )}
    </div>
  )
}
