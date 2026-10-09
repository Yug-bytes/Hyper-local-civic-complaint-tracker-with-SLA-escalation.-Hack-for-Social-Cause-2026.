/**
 * Utility functions for formatting ISO timestamps for display.
 */

export function formatDateTime(isoString?: string | null): string {
  if (!isoString) return '—'
  try {
    const d = new Date(isoString)
    if (isNaN(d.getTime())) return isoString

    return d.toLocaleString('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: true,
      timeZone: 'UTC',
    }) + ' UTC'
  } catch {
    return isoString
  }
}

export function formatDateOnly(isoString?: string | null): string {
  if (!isoString) return '—'
  try {
    const d = new Date(isoString)
    if (isNaN(d.getTime())) return isoString

    return d.toLocaleDateString('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      timeZone: 'UTC',
    })
  } catch {
    return isoString
  }
}

export function isPastDeadline(isoString?: string | null): boolean {
  if (!isoString) return false
  try {
    const d = new Date(isoString)
    return d.getTime() < Date.now()
  } catch {
    return false
  }
}
