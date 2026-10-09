export interface Department {
  id?: number
  category: string
  department_name: string
  responsible_role: string
  escalation_role: string
  sla_days: number
}

export interface StatusHistory {
  status: string
  note?: string | null
  changed_by: string
  changed_at?: string | null
}

export interface ComplaintPublic {
  tracking_id: string
  category: string
  description: string
  locality: string
  photo_url?: string | null
  status: string
  created_at: string
  due_at: string
  resolved_at?: string | null
  history: StatusHistory[]
}

export interface DepartmentMetric {
  category: string
  department_name?: string
  total: number
  resolved: number
  open: number
  overdue: number
  avg_resolution_hours: number
  resolution_rate_pct?: number
  sla_days?: number
  total_complaints?: number
  resolved_complaints?: number
  open_complaints?: number
  overdue_complaints?: number
}

export interface ComplaintAdmin {
  id?: string
  tracking_id: string
  category: string
  description: string
  locality: string
  photo_url?: string | null
  reporter_name?: string | null
  reporter_phone?: string | null
  status: string
  created_at: string
  due_at: string
  resolved_at?: string | null
  escalation_level: number
  is_overdue: boolean
}

export interface AdminMetricsSummary {
  total_complaints: number
  open_complaints: number
  overdue_complaints: number
  avg_resolution_hours: number
  departments: DepartmentMetric[]
}

export interface ApiError {
  code: string
  message: string
}

const API_BASE = (import.meta.env.VITE_API_BASE || '/api').replace(/\/$/, '')

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${endpoint}`
  const headers = new Headers(options.headers || {})

  if (!headers.has('X-Requested-With')) {
    headers.set('X-Requested-With', 'XMLHttpRequest')
  }

  const response = await fetch(url, {
    ...options,
    headers,
    credentials: 'include', // essential for HttpOnly session cookies
  })

  if (!response.ok) {
    let errorDetail: ApiError = {
      code: 'UNKNOWN_ERROR',
      message: `Request failed with status ${response.status}`,
    }
    try {
      const errorJson = await response.json()
      if (errorJson?.error) {
        errorDetail = errorJson.error
      }
    } catch {
      // ignore json parse error
    }
    throw errorDetail
  }

  return response.json()
}

export const api = {
  getHealth: () => request<{ status: string; env: string }>('/health'),

  getDepartments: () => request<Department[]>('/departments'),

  createComplaint: (formData: FormData) =>
    request<{ tracking_id: string }>('/complaints', {
      method: 'POST',
      body: formData,
    }),

  getComplaintStatus: (trackingId: string) =>
    request<ComplaintPublic>(`/complaints/${encodeURIComponent(trackingId.trim().toUpperCase())}`),

  getPublicMetrics: () => request<DepartmentMetric[]>('/metrics'),

  adminLogin: (password: string) =>
    request<{ status: string }>('/admin/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password }),
    }),

  adminLogout: () =>
    request<{ status: string }>('/admin/logout', {
      method: 'POST',
    }),

  checkAdminSession: () =>
    request<{ authenticated: boolean }>('/admin/session'),

  getAdminComplaints: (params?: { status?: string; category?: string; overdue_only?: boolean }) => {
    const query = new URLSearchParams()
    if (params?.status) query.append('status', params.status)
    if (params?.category) query.append('category', params.category)
    if (params?.overdue_only) query.append('overdue_only', 'true')
    const qs = query.toString() ? `?${query.toString()}` : ''
    return request<ComplaintAdmin[]>(`/admin/complaints${qs}`)
  },

  updateComplaintStatus: (trackingId: string, newStatus: string, note?: string) =>
    request<ComplaintAdmin>(`/admin/complaints/${encodeURIComponent(trackingId)}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ new_status: newStatus, note }),
    }),

  deleteComplaintPhoto: (trackingId: string) =>
    request<{ tracking_id: string; photo_url: null }>(`/admin/complaints/${encodeURIComponent(trackingId)}/photo`, {
      method: 'DELETE',
    }),

  getAdminMetrics: () => request<AdminMetricsSummary>('/admin/metrics'),
}
