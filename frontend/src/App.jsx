
import { useEffect, useState } from 'react'
import ApiExplorer from './ApiExplorer'
import AccessRequest from './AccessRequest'

const API_URL = import.meta.env.VITE_API_BASE_URL

const menuItems = [
  { name: 'Overview', icon: '◫' },
  { name: 'Organizations', icon: '▣' },
  { name: 'Access Requests', icon: '✉' },
  { name: 'API Keys', icon: '⚿' },
  { name: 'OCR Services', icon: '▤' },
  { name: 'OCR Playground', icon: '📄' },
  { name: 'Usage Analytics', icon: '▥' },
  { name: 'Audit Logs', icon: '☷' },
  { name: 'API Explorer', icon: '⚡' }
]

const stats = [
  { label: 'Total Organizations', key: 'total_organizations', icon: '▣' },
  { label: 'Active API Keys', key: 'active_api_keys', icon: '⚿' },
  { label: 'Pending Requests', key: 'pending_access_requests', icon: '✉' },
  { label: 'OCR Requests', key: 'total_ocr_requests', icon: '▤' },
]

function App() {
  const [token, setToken] = useState(null)
  const [showAccessRequest, setShowAccessRequest] = useState(false)
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [activePage, setActivePage] = useState('Overview')


  const [organizations, setOrganizations] = useState([])
  const [organizationsLoading, setOrganizationsLoading] = useState(false)
  const [organizationsError, setOrganizationsError] = useState('')
  const [ocrApiKey, setOcrApiKey] = useState('')
  const [selectedFile, setSelectedFile] = useState(null)
  const [ocrResult, setOcrResult] = useState(null)
  const [ocrError, setOcrError] = useState('')
  const [ocrLoading, setOcrLoading] = useState(false)
  const [ocrDuration, setOcrDuration] = useState(null)


  const [accessRequests, setAccessRequests] = useState([])
  const [requestsLoading, setRequestsLoading] = useState(false)
  const [requestsError, setRequestsError] = useState('')
  const [requestActionLoading, setRequestActionLoading] = useState(null)
  const [requestActionMessage, setRequestActionMessage] = useState('')

  const [apiKeys, setApiKeys] = useState([])
  const [apiKeysLoading, setApiKeysLoading] = useState(false)
  const [apiKeysError, setApiKeysError] = useState('')
  const [apiKeyActionLoading, setApiKeyActionLoading] = useState(null)
  const [apiKeyMessage, setApiKeyMessage] = useState('')

  // New API key form state
  const [newKeyOrganization, setNewKeyOrganization] = useState('')
  const [newKeyName, setNewKeyName] = useState('')
  const [newKeyExpiry, setNewKeyExpiry] = useState('')
  const [createKeyLoading, setCreateKeyLoading] = useState(false)
  const [generatedApiKey, setGeneratedApiKey] = useState('')


  // OCR Services state
  const [ocrServices, setOcrServices] = useState([])
  const [ocrServicesLoading, setOcrServicesLoading] = useState(false)
  const [ocrServicesError, setOcrServicesError] = useState('')
  const [serviceActionLoading, setServiceActionLoading] = useState(null)
  const [serviceActionMessage, setServiceActionMessage] = useState('')

  const [dashboardStats, setDashboardStats] = useState({
    total_organizations: 0,
    active_api_keys: 0,
    pending_access_requests: 0,
    total_ocr_requests: 0,
  })

  const [statsError, setStatsError] = useState('')
  // Usage Analytics state
  const [usageAnalytics, setUsageAnalytics] = useState({
  total_requests: 0,
  successful_requests: 0,
  failed_requests: 0,
  average_duration_ms: 0,
  organization_usage: [],
  service_usage: [],
  daily_usage: [],
})

  const [analyticsLoading, setAnalyticsLoading] = useState(false)
  const [analyticsError, setAnalyticsError] = useState('')


    // Audit Logs state
  const [auditLogs, setAuditLogs] = useState([])
  const [auditLogsLoading, setAuditLogsLoading] = useState(false)
  const [auditLogsError, setAuditLogsError] = useState('')



  // Fetch dashboard statistics
  useEffect(() => {
    if (!token) return

    async function fetchDashboardStats() {
      try {
        const response = await fetch(
          `${API_URL}/admin/dashboard/stats`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        )

        if (!response.ok) {
          throw new Error('Unable to load dashboard statistics.')
        }

        const data = await response.json()
        setDashboardStats(data)
        setStatsError('')
      } catch (error) {
        setStatsError(error.message)
      }
    }

    fetchDashboardStats()
  }, [token])

  // Fetch organizations
  useEffect(() => {
    if (!token || !['Organizations', 'OCR Playground'].includes(activePage)) return

    async function fetchOrganizations() {
      setOrganizationsLoading(true)
      setOrganizationsError('')

      try {
        const response = await fetch(
          `${API_URL}/admin/dashboard/organizations`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        )

        if (!response.ok) {
          throw new Error('Unable to load organizations.')
        }

        const data = await response.json()
        setOrganizations(data)
      } catch (error) {
        setOrganizationsError(error.message)
      } finally {
        setOrganizationsLoading(false)
      }
    }

    fetchOrganizations()
  }, [token, activePage])

  // Fetch API keys and organizations
  useEffect(() => {
    if (!token || activePage !== 'API Keys') return

    async function fetchApiKeys() {
      setApiKeysLoading(true)
      setApiKeysError('')

      try {
        const response = await fetch(
          `${API_URL}/admin/clients/api-keys`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        )

        if (!response.ok) {
          throw new Error('Unable to load API keys.')
        }

        const data = await response.json()
        setApiKeys(Array.isArray(data) ? data : [])

        // Load organizations for the API key creation form
        const orgResponse = await fetch(
          `${API_URL}/admin/dashboard/organizations`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        )

        if (!orgResponse.ok) {
          throw new Error(
            'Unable to load organizations for API key creation.'
          )
        }

        const orgData = await orgResponse.json()
        setOrganizations(orgData)
      } catch (error) {
        setApiKeysError(error.message)
      } finally {
        setApiKeysLoading(false)
      }
    }

    fetchApiKeys()
  }, [token, activePage])

  // Load OCR services when the OCR Services page is opened
  useEffect(() => {
    if (!token || activePage !== 'OCR Services') return

    async function fetchOcrServices() {
      setOcrServicesLoading(true)
      setOcrServicesError('')
      setServiceActionMessage('')

      try {
        const response = await fetch(
          `${API_URL}/admin/services/`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        )

        if (!response.ok) {
          throw new Error('Unable to load OCR services.')
        }

        const data = await response.json()
        setOcrServices(Array.isArray(data) ? data : [])
      } catch (error) {
        setOcrServicesError(error.message)
      } finally {
        setOcrServicesLoading(false)
      }
    }

    fetchOcrServices()
  }, [token, activePage])

  
// Load usage analytics when the page is opened
useEffect(() => {
  if (!token || activePage !== 'Usage Analytics') return

  async function fetchUsageAnalytics() {
    setAnalyticsLoading(true)
    setAnalyticsError('')

    try {
      const response = await fetch(
        `${API_URL}/admin/dashboard/usage-analytics`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      )

      if (!response.ok) {
        throw new Error('Unable to load usage analytics.')
      }

      const data = await response.json()
      setUsageAnalytics(data)
    } catch (error) {
      setAnalyticsError(error.message)
    } finally {
      setAnalyticsLoading(false)
    }
  }

  fetchUsageAnalytics()
}, [token, activePage])

  // Load audit logs when the Audit Logs page is opened
  useEffect(() => {
    if (!token || activePage !== 'Audit Logs') return

    async function fetchAuditLogs() {
      setAuditLogsLoading(true)
      setAuditLogsError('')

      try {
        const response = await fetch(
          `${API_URL}/admin/audit-logs/`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        )

        if (!response.ok) {
          throw new Error('Unable to load audit logs.')
        }

        const data = await response.json()
        setAuditLogs(Array.isArray(data) ? data : [])
      } catch (error) {
        setAuditLogsError(error.message)
      } finally {
        setAuditLogsLoading(false)
      }
    }

    fetchAuditLogs()
  }, [token, activePage])


  
  // Fetch pending access requests
  useEffect(() => {
    if (!token || activePage !== 'Access Requests') return

    async function fetchAccessRequests() {
      setRequestsLoading(true)
      setRequestsError('')

      try {
        const response = await fetch(
          `${API_URL}/admin/access-requests/pending`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        )

        if (!response.ok) {
          throw new Error('Unable to load access requests.')
        }

        const data = await response.json()
        setAccessRequests(data.requests || [])
      } catch (error) {
        setRequestsError(error.message)
      } finally {
        setRequestsLoading(false)
      }
    }

    fetchAccessRequests()
  }, [token, activePage])

  // Admin login
  async function handleLogin(event) {
    event.preventDefault()
    setError('')
    setLoading(true)

    try {
      const response = await fetch(`${API_URL}/admin/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username_or_email: username.trim(),
          password: password,
        }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Login failed.')
      }

      setToken(data.access_token)
      setPassword('')
    } catch (err) {
      setError(
        err.message === 'Failed to fetch'
          ? 'Cannot connect to the OCR backend. Please check that FastAPI is running.'
          : err.message
      )
    } finally {
      setLoading(false)
    }
  }

  // Admin logout
  function handleLogout() {
    setToken(null)
    setUsername('')
    setPassword('')
    setActivePage('Overview')
    setError('')
  }

  // Approve access request
  async function handleApproveRequest(requestId) {
    const confirmed = window.confirm(
      'Are you sure you want to approve this organization?'
    )

    if (!confirmed) return

    setRequestActionLoading(requestId)
    setRequestActionMessage('')
    setRequestsError('')

    try {
      const response = await fetch(
        `${API_URL}/admin/access-requests/${requestId}/approve`,
        {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      )

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Unable to approve request.')
      }

      setRequestActionMessage(data.message)
      setAccessRequests((previous) =>
        previous.filter((request) => request.id !== requestId)
      )
    } catch (error) {
      setRequestsError(error.message)
    } finally {
      setRequestActionLoading(null)
    }
  }

  // Reject access request
  async function handleRejectRequest(requestId) {
    const reviewNote = window.prompt(
      'Enter a reason for rejecting this request (minimum 3 characters):'
    )

    if (reviewNote === null) return

    if (reviewNote.trim().length < 3 || reviewNote.trim().length > 500) {
      setRequestsError(
        'The rejection note must be between 3 and 500 characters.'
      )
      return
    }

    setRequestActionLoading(requestId)
    setRequestActionMessage('')
    setRequestsError('')

    try {
      const response = await fetch(
        `${API_URL}/admin/access-requests/${requestId}/reject`,
        {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            review_note: reviewNote.trim(),
          }),
        }
      )

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Unable to reject request.')
      }

      setRequestActionMessage(data.message)
      setAccessRequests((previous) =>
        previous.filter((request) => request.id !== requestId)
      )
    } catch (error) {
      setRequestsError(error.message)
    } finally {
      setRequestActionLoading(null)
    }
  }

  // Revoke API key
  async function handleRevokeApiKey(apiKeyId) {
    const confirmed = window.confirm(
      'Are you sure you want to revoke this API key? Applications using it will stop working.'
    )

    if (!confirmed) return

    setApiKeyActionLoading(apiKeyId)
    setApiKeyMessage('')
    setApiKeysError('')

    try {
      const response = await fetch(
        `${API_URL}/admin/clients/api-keys/${apiKeyId}/revoke`,
        {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      )

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Unable to revoke API key.')
      }

      setApiKeyMessage(data.message)

      setApiKeys((previous) =>
        previous.map((key) =>
          key.id === apiKeyId
            ? {
                ...key,
                is_active: false,
                revoked_at: new Date().toISOString(),
              }
            : key
        )
      )
    } catch (error) {
      setApiKeysError(error.message)
    } finally {
      setApiKeyActionLoading(null)
    }
  }
  async function handleCreateApiKey(event) {
  event.preventDefault()

  if (!newKeyOrganization || !newKeyName.trim()) {
    setApiKeysError('Please select an organization and enter an API key name.')
    return
  }

  setCreateKeyLoading(true)
  setApiKeysError('')
  setApiKeyMessage('')
  setGeneratedApiKey('')

  try {
    const response = await fetch(
      `${API_URL}/admin/clients/${newKeyOrganization}/api-keys`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          name: newKeyName.trim(),
          expires_at: newKeyExpiry
            ? new Date(`${newKeyExpiry}T23:59:59`).toISOString()
            : null,
        }),
      }
    )

    const data = await response.json()

    if (!response.ok) {
      throw new Error(data.detail || 'Unable to create API key.')
    }

    setGeneratedApiKey(data.api_key)
    setApiKeyMessage('API key created successfully. Copy it now; it will not be shown again.')
    setNewKeyName('')
    setNewKeyExpiry('')

    const keysResponse = await fetch(
      `${API_URL}/admin/clients/api-keys`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    )

    if (keysResponse.ok) {
      const keysData = await keysResponse.json()
      setApiKeys(Array.isArray(keysData) ? keysData : [])
    }
  } catch (error) {
    setApiKeysError(error.message)
  } finally {
    setCreateKeyLoading(false)
  }
}


  async function handleToggleOcrService(serviceId, newStatus) {
    setServiceActionLoading(serviceId)
    setOcrServicesError('')
    setServiceActionMessage('')

    try {
      const response = await fetch(
        `${API_URL}/admin/services/${serviceId}/status?is_active=${newStatus}`,
        {
          method: 'PATCH',
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      )

      const data = await response.json()

      if (!response.ok) {
        throw new Error(
          data.detail || 'Unable to update OCR service status.'
        )
      }

      setOcrServices((previousServices) =>
        previousServices.map((service) =>
          service.id === serviceId
            ? { ...service, is_active: data.is_active }
            : service
        )
      )

      setServiceActionMessage(
        `${data.service_code} ${
          data.is_active ? 'enabled' : 'disabled'
        } successfully.`
      )
    } catch (error) {
      setOcrServicesError(error.message)
    } finally {
      setServiceActionLoading(null)
    }
  }



  // Submit a document to the OCR extraction API
  async function handleOcrExtraction(event) {
    event.preventDefault()
    setOcrError('')
    setOcrResult(null)
    setOcrDuration(null)

    if (!newKeyOrganization) {
      setOcrError('Please select an organization.')
      return
    }

    if (!ocrApiKey.trim()) {
      setOcrError("Please enter the organization's API key.")
      return
    }

    if (!selectedFile) {
      setOcrError('Please choose an image or PDF file.')
      return
    }

    const allowedTypes = ['image/jpeg', 'image/png', 'application/pdf']
    if (!allowedTypes.includes(selectedFile.type)) {
      setOcrError('Only JPG, PNG, and PDF files are supported.')
      return
    }

    const formData = new FormData()
    formData.append('file', selectedFile)

    setOcrLoading(true)
    const startedAt = performance.now()

    try {
      const response = await fetch(`${API_URL}/extract`, {
        method: 'POST',
        headers: {
          'X-API-Key': ocrApiKey.trim(),
        },
        body: formData,
      })

      const responseText = await response.text()
      let data = {}

      try {
        data = responseText ? JSON.parse(responseText) : {}
      } catch {
        data = { detail: responseText || 'The server returned an unreadable response.' }
      }

      if (!response.ok) {
        throw new Error(
          data.detail || data.message || `OCR request failed (${response.status}).`
        )
      }

      setOcrResult(data)
      setOcrDuration(Math.round(performance.now() - startedAt))
    } catch (error) {
      setOcrError(
        error.message === 'Failed to fetch'
          ? 'Could not connect to the OCR API. Check that the backend is running.'
          : error.message
      )
      setOcrDuration(Math.round(performance.now() - startedAt))
    } finally {
      setOcrLoading(false)
    }
  }

  // Login screen
if (!token && showAccessRequest) {
  return (
    <AccessRequest
      apiUrl={API_URL}
      onBack={() => setShowAccessRequest(false)}
    />
  )
}

if (!token) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-100 px-4">
        <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-8 shadow-xl">
          <div className="mb-7 text-center">
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-600 text-2xl font-bold text-white">
              O
            </div>

            <h1 className="mt-4 text-2xl font-bold text-slate-900">
              OCR Platform
            </h1>

            <p className="mt-1 text-sm text-slate-500">
              Super Admin Dashboard
            </p>
          </div>

          <div className="mb-6">
            <h2 className="text-lg font-semibold text-slate-900">
              Administrator Login
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              Sign in to manage your OCR platform.
            </p>
          </div>

          <form onSubmit={handleLogin} className="space-y-5">
            <div>
              <label className="mb-2 block text-sm font-medium text-slate-700">
                Username or Email
              </label>

              <input
                type="text"
                required
                autoComplete="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter your username or email"
                className="w-full rounded-lg border border-slate-300 px-4 py-3 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
              />
            </div>

            <div>
              <label className="mb-2 block text-sm font-medium text-slate-700">
                Password
              </label>

              <input
                type="password"
                required
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                className="w-full rounded-lg border border-slate-300 px-4 py-3 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
              />
            </div>

            {error && (
              <div className="rounded-lg bg-red-50 p-3 text-sm text-red-700">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-lg bg-blue-600 px-4 py-3 font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>
          <button
            type="button"
            onClick={() => setShowAccessRequest(true)}
          >
            Request API Access
          </button>

          <p className="mt-6 text-center text-xs text-slate-400">
            Restricted access · Super Administrator only
          </p>
        </div>
      </div>
    )
  }

  // Main dashboard
  return (
    <div className="min-h-screen bg-slate-100 text-slate-800">
      <aside className="fixed inset-y-0 left-0 z-20 hidden w-64 flex-col bg-slate-950 text-white md:flex">
        <div className="border-b border-slate-800 px-6 py-6">
          <h1 className="text-lg font-bold">OCR Platform</h1>
          <p className="text-xs text-slate-400">Super Admin Dashboard</p>
        </div>

        <nav className="flex-1 space-y-1 px-4 py-6">
          {menuItems.map((item) => (
            <button
              key={item.name}
              onClick={() => setActivePage(item.name)}
              className={`flex w-full items-center gap-3 rounded-lg px-3 py-3 text-left text-sm ${
                activePage === item.name
                  ? 'bg-blue-600 font-semibold text-white'
                  : 'text-slate-300 hover:bg-slate-800'
              }`}
            >
              <span>{item.icon}</span>
              {item.name}
            </button>
          ))}
        </nav>

        <div className="border-t border-slate-800 p-5">
          <p className="text-sm font-semibold">Super Administrator</p>

          <button
            onClick={handleLogout}
            className="mt-3 text-sm text-red-400 hover:text-red-300"
          >
            Sign Out →
          </button>
        </div>
      </aside>

      <main className="min-h-screen md:ml-64">
        <header className="flex items-center justify-between border-b border-slate-200 bg-white px-5 py-4 md:px-8">
          <div>
            <p className="text-xs text-slate-500">OCR Platform / Admin</p>
            <h2 className="mt-1 text-xl font-bold">{activePage}</h2>
          </div>

          <span className="rounded-full bg-green-50 px-3 py-2 text-xs font-semibold text-green-700">
            Authenticated
          </span>
        </header>

        <div className="p-5 md:p-8">
          {activePage === 'Overview' ? (
            <>
              <h3 className="text-2xl font-bold text-slate-900">
                Dashboard Overview
              </h3>

              <p className="mt-1 text-sm text-slate-500">
                Welcome to your OCR Platform administration dashboard.
              </p>

              {statsError && (
                <div className="mt-4 rounded-lg bg-red-50 p-4 text-sm text-red-700">
                  {statsError}
                </div>
              )}

              <div className="mt-7 grid gap-5 sm:grid-cols-2 xl:grid-cols-4">
                {stats.map((stat) => (
                  <div
                    key={stat.label}
                    className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"
                  >
                    <div className="flex justify-between">
                      <p className="text-sm text-slate-500">{stat.label}</p>
                      <span className="text-xl text-blue-600">
                        {stat.icon}
                      </span>
                    </div>

                    <p className="mt-4 text-3xl font-bold text-slate-900">
                      {dashboardStats[stat.key]}
                    </p>

                    <p className="mt-1 text-xs text-slate-500">
                      Live database statistics
                    </p>
                  </div>
                ))}
              </div>

              <div className="mt-7 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
                <h3 className="font-bold text-slate-900">Platform Status</h3>

                <div className="mt-4 rounded-lg bg-green-50 p-4 text-sm text-green-800">
                  Administrator login successful. Backend authentication is connected.
                </div>

                <p className="mt-3 text-sm text-slate-500">
                  Live organization and usage statistics will be connected next.
                </p>
              </div>
            </>
          ) : activePage === 'Organizations' ? (
            <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
              <div className="mb-6">
                <h3 className="text-xl font-bold text-slate-900">
                  Registered Organizations
                </h3>

                <p className="mt-1 text-sm text-slate-500">
                  View and manage organizations registered on your OCR platform.
                </p>
              </div>

              {organizationsLoading && (
                <p className="py-8 text-center text-slate-500">
                  Loading organizations...
                </p>
              )}

              {organizationsError && (
                <div className="rounded-lg bg-red-50 p-4 text-sm text-red-700">
                  {organizationsError}
                </div>
              )}

              {!organizationsLoading &&
                !organizationsError &&
                organizations.length === 0 && (
                  <p className="py-8 text-center text-slate-500">
                    No organizations found.
                  </p>
                )}

              {!organizationsLoading &&
                !organizationsError &&
                organizations.length > 0 && (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm">
                      <thead className="border-b bg-slate-50 text-slate-600">
                        <tr>
                          <th className="px-4 py-3">ID</th>
                          <th className="px-4 py-3">Organization</th>
                          <th className="px-4 py-3">Industry</th>
                          <th className="px-4 py-3">Contact</th>
                          <th className="px-4 py-3">Email</th>
                          <th className="px-4 py-3">Status</th>
                          <th className="px-4 py-3">Registered</th>
                        </tr>
                      </thead>

                      <tbody className="divide-y divide-slate-100">
                        {organizations.map((org) => (
                          <tr key={org.id} className="hover:bg-slate-50">
                            <td className="px-4 py-4">{org.id}</td>

                            <td className="px-4 py-4 font-medium text-slate-900">
                              {org.organization_name}
                            </td>

                            <td className="px-4 py-4">{org.industry}</td>
                            <td className="px-4 py-4">{org.contact_name}</td>
                            <td className="px-4 py-4">{org.contact_email}</td>

                            <td className="px-4 py-4">
                              <span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700">
                                {org.status}
                              </span>
                            </td>

                            <td className="px-4 py-4">
                              {new Date(org.created_at).toLocaleDateString()}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
            </div>
          ) : activePage === 'Access Requests' ? (
            <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
              <h3 className="text-xl font-bold text-slate-900">
                Pending Access Requests
              </h3>

              <p className="mt-1 mb-6 text-sm text-slate-500">
                Review organizations requesting access to your OCR platform.
              </p>

              {requestsLoading && (
                <p className="py-8 text-center text-slate-500">
                  Loading access requests...
                </p>
              )}

              {requestsError && (
                <div className="rounded-lg bg-red-50 p-4 text-sm text-red-700">
                  {requestsError}
                </div>
              )}

              {requestActionMessage && (
                <div className="mb-4 rounded-lg bg-green-50 p-4 text-sm text-green-700">
                  {requestActionMessage}
                </div>
              )}

              {!requestsLoading &&
                !requestsError &&
                accessRequests.length === 0 && (
                  <p className="py-8 text-center text-slate-500">
                    No pending access requests.
                  </p>
                )}

              {!requestsLoading &&
                !requestsError &&
                accessRequests.length > 0 && (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm">
                      <thead className="border-b bg-slate-50 text-slate-600">
                        <tr>
                          <th className="px-4 py-3">Organization</th>
                          <th className="px-4 py-3">Industry</th>
                          <th className="px-4 py-3">Contact</th>
                          <th className="px-4 py-3">Email</th>
                          <th className="px-4 py-3">Phone</th>
                          <th className="px-4 py-3">Requested Services</th>
                          <th className="px-4 py-3">Actions</th>
                        </tr>
                      </thead>

                      <tbody className="divide-y divide-slate-100">
                        {accessRequests.map((request) => (
                          <tr key={request.id}>
                            <td className="px-4 py-4 font-medium">
                              {request.organization_name}
                            </td>

                            <td className="px-4 py-4">{request.industry}</td>
                            <td className="px-4 py-4">{request.contact_name}</td>
                            <td className="px-4 py-4">{request.contact_email}</td>

                            <td className="px-4 py-4">
                              {request.contact_phone || '—'}
                            </td>

                            <td className="px-4 py-4">
                              {Array.isArray(request.requested_services)
                                ? request.requested_services.join(', ')
                                : '—'}
                            </td>

                            <td className="px-4 py-4">
                              <div className="flex gap-2">
                                <button
                                  onClick={() => handleApproveRequest(request.id)}
                                  disabled={requestActionLoading === request.id}
                                  className="rounded-lg bg-green-600 px-3 py-2 text-xs font-semibold text-white hover:bg-green-700 disabled:opacity-50"
                                >
                                  {requestActionLoading === request.id
                                    ? 'Please wait...'
                                    : 'Approve'}
                                </button>

                                <button
                                  onClick={() => handleRejectRequest(request.id)}
                                  disabled={requestActionLoading === request.id}
                                  className="rounded-lg bg-red-600 px-3 py-2 text-xs font-semibold text-white hover:bg-red-700 disabled:opacity-50"
                                >
                                  Reject
                                </button>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
            </div>
          ) : activePage === 'API Keys' ? (
            <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
              <h3 className="text-xl font-bold text-slate-900">
                API Key Management
              </h3>

              <p className="mt-1 mb-6 text-sm text-slate-500">
                View and manage API keys assigned to your organizations.
              </p>

              <form
                onSubmit={handleCreateApiKey}
                className="mb-6 rounded-xl border border-slate-200 bg-slate-50 p-5"
              >
                <h4 className="mb-4 text-base font-semibold text-slate-900">
                  Generate New API Key
                </h4>

                <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                  <div>
                    <label className="mb-2 block text-sm font-medium text-slate-700">
                      Organization
                    </label>
                    <select
                      value={newKeyOrganization}
                      onChange={(e) => setNewKeyOrganization(e.target.value)}
                      required
                      className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm"
                    >
                      <option value="">Select organization</option>
                      {organizations.map((org) => (
                        <option key={org.id} value={org.id}>
                          {org.organization_name}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="mb-2 block text-sm font-medium text-slate-700">
                      API Key Name
                    </label>
                    <input
                      type="text"
                      value={newKeyName}
                      onChange={(e) => setNewKeyName(e.target.value)}
                      placeholder="e.g. Production ERP"
                      minLength={2}
                      maxLength={100}
                      required
                      className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm"
                    />
                  </div>

                  <div>
                    <label className="mb-2 block text-sm font-medium text-slate-700">
                      Expiry Date (Optional)
                    </label>
                    <input
                      type="date"
                      value={newKeyExpiry}
                      onChange={(e) => setNewKeyExpiry(e.target.value)}
                      min={new Date().toISOString().split('T')[0]}
                      className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm"
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={createKeyLoading}
                  className="mt-5 rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50"
                >
                  {createKeyLoading ? 'Generating...' : 'Generate API Key'}
                </button>

                {generatedApiKey && (
                  <div className="mt-5 rounded-lg border border-green-200 bg-green-50 p-4">
                    <p className="mb-2 text-sm font-semibold text-green-800">
                      Your new API key
                    </p>

                    <div className="flex flex-col gap-2 sm:flex-row">
                      <input
                        type="text"
                        readOnly
                        value={generatedApiKey}
                        className="min-w-0 flex-1 rounded-lg border border-green-300 bg-white px-3 py-2 text-sm"
                      />

                      <button
                        type="button"
                        onClick={() => {
                          navigator.clipboard.writeText(generatedApiKey)
                          setApiKeyMessage('API key copied to clipboard.')
                        }}
                        className="rounded-lg bg-green-700 px-4 py-2 text-sm font-semibold text-white"
                      >
                        Copy API Key
                      </button>
                    </div>

                    <p className="mt-2 text-xs text-green-800">
                      Save this key securely. It will not be displayed again.
                    </p>
                  </div>
                )}
              </form>


              {apiKeysLoading && (
                <p className="py-8 text-center text-slate-500">
                  Loading API keys...
                </p>
              )}

              {apiKeysError && (
                <div className="rounded-lg bg-red-50 p-4 text-sm text-red-700">
                  {apiKeysError}
                </div>
              )}

              {apiKeyMessage && (
                <div className="mb-4 rounded-lg bg-green-50 p-4 text-sm text-green-700">
                  {apiKeyMessage}
                </div>
              )}

              {!apiKeysLoading &&
                !apiKeysError &&
                apiKeys.length === 0 && (
                  <p className="py-8 text-center text-slate-500">
                    No API keys found.
                  </p>
                )}

              {!apiKeysLoading &&
                !apiKeysError &&
                apiKeys.length > 0 && (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm">
                      <thead className="border-b bg-slate-50 text-slate-600">
                        <tr>
                          <th className="px-4 py-3">ID</th>
                          <th className="px-4 py-3">Organization</th>
                          <th className="px-4 py-3">Key Name</th>
                          <th className="px-4 py-3">Key Prefix</th>
                          <th className="px-4 py-3">Status</th>
                          <th className="px-4 py-3">Expires</th>
                          <th className="px-4 py-3">Last Used</th>
                          <th className="px-4 py-3">Created</th>
                          <th className="px-4 py-3">Actions</th>
                        </tr>
                      </thead>

                      <tbody className="divide-y divide-slate-100">
                        {apiKeys.map((key) => (
                          <tr key={key.id} className="hover:bg-slate-50">
                            <td className="px-4 py-4">{key.id}</td>

                            <td className="px-4 py-4 font-medium text-slate-900">
                              {key.organization_name}
                            </td>

                            <td className="px-4 py-4">{key.name}</td>

                            <td className="px-4 py-4 font-mono text-xs">
                              {key.key_prefix}...
                            </td>

                            <td className="px-4 py-4">
                              <span
                                className={`rounded-full px-3 py-1 text-xs font-semibold ${
                                  !key.is_active
                                    ? 'bg-red-50 text-red-700'
                                    : key.expires_at &&
                                        new Date(key.expires_at) < new Date()
                                      ? 'bg-amber-50 text-amber-700'
                                      : 'bg-green-50 text-green-700'
                                }`}
                              >
                                {!key.is_active
                                  ? 'Revoked'
                                  : key.expires_at &&
                                      new Date(key.expires_at) < new Date()
                                    ? 'Expired'
                                    : 'Active'}
                              </span>
                            </td>

                            <td className="px-4 py-4">
                              {key.expires_at
                                ? new Date(key.expires_at).toLocaleDateString()
                                : 'Never'}
                            </td>

                            <td className="px-4 py-4">
                              {key.last_used_at
                                ? new Date(key.last_used_at).toLocaleDateString()
                                : 'Never'}
                            </td>

                            <td className="px-4 py-4">
                              {key.created_at
                                ? new Date(key.created_at).toLocaleDateString()
                                : '—'}
                            </td>

                            <td className="px-4 py-4">
                              <button
                                onClick={() => handleRevokeApiKey(key.id)}
                                disabled={
                                  !key.is_active ||
                                  apiKeyActionLoading === key.id
                                }
                                className="rounded-lg bg-red-600 px-3 py-2 text-xs font-semibold text-white hover:bg-red-700 disabled:cursor-not-allowed disabled:opacity-50"
                              >
                                {apiKeyActionLoading === key.id
                                  ? 'Please wait...'
                                  : key.is_active
                                    ? 'Revoke'
                                    : 'Revoked'}
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
            </div>

          ) : activePage === 'OCR Services' ? (
            <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
              <h3 className="text-xl font-bold text-slate-900">
                OCR Services Management
              </h3>

              <p className="mt-1 mb-6 text-sm text-slate-500">
                View and manage the OCR services available on your platform.
              </p>

              {ocrServicesLoading && (
                <p className="py-8 text-center text-slate-500">
                  Loading OCR services...
                </p>
              )}

              {ocrServicesError && (
                <div className="mb-4 rounded-lg bg-red-50 p-4 text-sm text-red-700">
                  {ocrServicesError}
                </div>
              )}

              {serviceActionMessage && (
                <div className="mb-4 rounded-lg bg-green-50 p-4 text-sm text-green-700">
                  {serviceActionMessage}
                </div>
              )}

              {!ocrServicesLoading &&
                !ocrServicesError &&
                ocrServices.length === 0 && (
                  <p className="py-8 text-center text-slate-500">
                    No OCR services registered.
                  </p>
                )}

              {!ocrServicesLoading &&
                ocrServices.length > 0 && (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm">
                      <thead className="border-b bg-slate-50 text-slate-600">
                        <tr>
                          <th className="px-4 py-3">ID</th>
                          <th className="px-4 py-3">Service Name</th>
                          <th className="px-4 py-3">Service Code</th>
                          <th className="px-4 py-3">Description</th>
                          <th className="px-4 py-3">Status</th>
                          <th className="px-4 py-3">Action</th>
                        </tr>
                      </thead>

                      <tbody className="divide-y divide-slate-100">
                        {ocrServices.map((service) => (
                          <tr key={service.id}>
                            <td className="px-4 py-4">{service.id}</td>

                            <td className="px-4 py-4 font-medium text-slate-900">
                              {service.service_name}
                            </td>

                            <td className="px-4 py-4 font-mono text-xs">
                              {service.service_code}
                            </td>

                            <td className="px-4 py-4">
                              {service.description || '—'}
                            </td>

                            <td className="px-4 py-4">
                              <span
                                className={`rounded-full px-3 py-1 text-xs font-semibold ${
                                  service.is_active
                                    ? 'bg-green-50 text-green-700'
                                    : 'bg-red-50 text-red-700'
                                }`}
                              >
                                {service.is_active ? 'Active' : 'Inactive'}
                              </span>
                            </td>

                            <td className="px-4 py-4">
                              <button
                                onClick={() =>
                                  handleToggleOcrService(
                                    service.id,
                                    !service.is_active
                                  )
                                }
                                disabled={serviceActionLoading === service.id}
                                className={`rounded-lg px-3 py-2 text-xs font-semibold text-white disabled:opacity-50 ${
                                  service.is_active
                                    ? 'bg-red-600 hover:bg-red-700'
                                    : 'bg-green-600 hover:bg-green-700'
                                }`}
                              >
                                {serviceActionLoading === service.id
                                  ? 'Please wait...'
                                  : service.is_active
                                    ? 'Disable'
                                    : 'Enable'}
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}

            </div>
          
          ) : activePage === 'OCR Playground' ? (
            <div className="space-y-6">
              <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
                <h3 className="text-xl font-bold text-slate-900">
                  OCR Playground
                </h3>

                <p className="mt-2 text-sm text-slate-500">
                  Test Aadhaar and PAN document extraction using your organization's API key.
                </p>

                <form onSubmit={handleOcrExtraction} className="mt-6 space-y-5">
                  <div>
                    <label className="mb-2 block text-sm font-medium text-slate-700">
                      Select Organization
                    </label>

                    <select
                      value={newKeyOrganization}
                      onChange={(e) => {
                        setNewKeyOrganization(e.target.value)
                        setOcrResult(null)
                        setOcrError('')
                      }}
                      required
                      className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                    >
                      <option value="">Choose an organization</option>

                      {organizations.map((org) => (
                        <option key={org.id} value={org.id}>
                          {org.organization_name}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="mb-2 block text-sm font-medium text-slate-700">
                      Organization API Key
                    </label>

                    <input
                      type="password"
                      value={ocrApiKey}
                      onChange={(e) => setOcrApiKey(e.target.value)}
                      placeholder="Paste the organization's active API key"
                      className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                      autoComplete="off"
                      required
                    />

                    <p className="mt-1 text-xs text-slate-500">
                      Your API key is used only for this test and is not saved.
                    </p>
                  </div>

                  <div>
                    <label className="mb-2 block text-sm font-medium text-slate-700">
                      Document File
                    </label>

                    <input
                      type="file"
                      accept=".jpg,.jpeg,.png,.pdf,image/jpeg,image/png,application/pdf"
                      onChange={(e) => {
                        setSelectedFile(e.target.files?.[0] || null)
                        setOcrResult(null)
                        setOcrError('')
                      }}
                      className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm"
                      required
                    />

                    <p className="mt-1 text-xs text-slate-500">
                      Supported formats: JPG, JPEG, PNG, and PDF.
                    </p>

                    {selectedFile && (
                      <p className="mt-2 text-sm text-slate-700">
                        Selected: {selectedFile.name}
                      </p>
                    )}
                  </div>

                  {ocrError && (
                    <div className="rounded-lg bg-red-50 p-4 text-sm text-red-700">
                      {ocrError}
                    </div>
                  )}

                  <button
                    type="submit"
                    disabled={ocrLoading}
                    className="rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {ocrLoading ? 'Extracting document...' : 'Extract Document'}
                  </button>
                </form>
              </div>

              {ocrDuration !== null && (
                <div className="rounded-lg border border-slate-200 bg-white p-4 text-sm text-slate-600">
                  Request time: <strong>{ocrDuration} ms</strong>
                </div>
              )}

              {ocrResult && (
                <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
                  <h3 className="text-lg font-bold text-slate-900">
                    OCR Extraction Result
                  </h3>

                  <p className="mt-1 text-sm text-green-700">
                    Document processed successfully.
                  </p>

                  <pre className="mt-4 max-h-[600px] overflow-auto rounded-lg bg-slate-950 p-4 text-xs text-green-100">
                    {JSON.stringify(ocrResult, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          ) : activePage === 'Usage Analytics' ? (
            <div className="space-y-6">

              {analyticsLoading && (
                <p className="text-sm text-slate-500">
                  Loading usage analytics...
                </p>
              )}

              {analyticsError && (
                <p className="rounded-lg bg-red-50 p-3 text-sm text-red-600">
                  {analyticsError}
                </p>
              )}

              {!analyticsLoading && !analyticsError && (
                <>
                  <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">

                    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
                      <p className="text-sm text-slate-500">Total Requests</p>
                      <h3 className="mt-2 text-3xl font-bold text-slate-900">
                        {usageAnalytics.total_requests}
                      </h3>
                    </div>

                    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
                      <p className="text-sm text-slate-500">Successful Requests</p>
                      <h3 className="mt-2 text-3xl font-bold text-green-600">
                        {usageAnalytics.successful_requests}
                      </h3>
                    </div>

                    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
                      <p className="text-sm text-slate-500">Failed Requests</p>
                      <h3 className="mt-2 text-3xl font-bold text-red-600">
                        {usageAnalytics.failed_requests}
                      </h3>
                    </div>

                    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
                      <p className="text-sm text-slate-500">Average Processing Time</p>
                      <h3 className="mt-2 text-3xl font-bold text-slate-900">
                        {usageAnalytics.average_duration_ms} ms
                      </h3>
                    </div>

                  </div>

                  <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">

                    <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
                      <h3 className="mb-4 text-lg font-bold text-slate-900">
                        Organization Usage
                      </h3>

                      {usageAnalytics.organization_usage.length === 0 ? (
                        <p className="text-sm text-slate-500">
                          No organization usage recorded yet.
                        </p>
                      ) : (
                        <div className="overflow-x-auto">
                          <table className="w-full text-left text-sm">
                            <thead>
                              <tr className="border-b text-slate-500">
                                <th className="py-3">Organization</th>
                                <th className="py-3 text-right">Requests</th>
                              </tr>
                            </thead>
                            <tbody>
                              {usageAnalytics.organization_usage.map((org) => (
                                <tr key={org.organization_id} className="border-b last:border-0">
                                  <td className="py-3 font-medium text-slate-800">
                                    {org.organization_name}
                                  </td>
                                  <td className="py-3 text-right font-semibold">
                                    {org.total_requests}
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      )}
                    </div>

                    <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
                      <h3 className="mb-4 text-lg font-bold text-slate-900">
                        OCR Service Usage
                      </h3>

                      {usageAnalytics.service_usage.length === 0 ? (
                        <p className="text-sm text-slate-500">
                          No service usage recorded yet.
                        </p>
                      ) : (
                        <div className="overflow-x-auto">
                          <table className="w-full text-left text-sm">
                            <thead>
                              <tr className="border-b text-slate-500">
                                <th className="py-3">Service</th>
                                <th className="py-3 text-right">Requests</th>
                              </tr>
                            </thead>
                            <tbody>
                              {usageAnalytics.service_usage.map((service) => (
                                <tr key={service.service_code} className="border-b last:border-0">
                                  <td className="py-3 font-medium text-slate-800">
                                    {service.service_code}
                                  </td>
                                  <td className="py-3 text-right font-semibold">
                                    {service.total_requests}
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      )}
                    </div>

                  </div>

                  <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
                    <h3 className="mb-4 text-lg font-bold text-slate-900">
                      Daily Usage
                    </h3>

                    {usageAnalytics.daily_usage.length === 0 ? (
                      <p className="text-sm text-slate-500">
                        No daily usage recorded yet.
                      </p>
                    ) : (
                      <div className="overflow-x-auto">
                        <table className="w-full text-left text-sm">
                          <thead>
                            <tr className="border-b text-slate-500">
                              <th className="py-3">Date</th>
                              <th className="py-3 text-right">Requests</th>
                            </tr>
                          </thead>
                          <tbody>
                            {usageAnalytics.daily_usage.map((day) => (
                              <tr key={day.date} className="border-b last:border-0">
                                <td className="py-3 font-medium text-slate-800">
                                  {day.date}
                                </td>
                                <td className="py-3 text-right font-semibold">
                                  {day.total_requests}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>
                </>
              )}

            </div>
          ) : activePage === 'Audit Logs' ? (
            <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
              <div className="mb-6">
                <h3 className="text-xl font-bold text-slate-900">
                  Audit Logs
                </h3>
                <p className="mt-1 text-sm text-slate-500">
                  Review administrative activity across your OCR platform.
                </p>
              </div>

              {auditLogsLoading && (
                <p className="py-8 text-center text-slate-500">
                  Loading audit logs...
                </p>
              )}

              {auditLogsError && (
                <div className="mb-4 rounded-lg bg-red-50 p-4 text-sm text-red-700">
                  {auditLogsError}
                </div>
              )}

              {!auditLogsLoading &&
                !auditLogsError &&
                auditLogs.length === 0 && (
                  <p className="py-8 text-center text-slate-500">
                    No audit records found.
                  </p>
                )}

              {!auditLogsLoading &&
                !auditLogsError &&
                auditLogs.length > 0 && (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm">
                      <thead className="border-b bg-slate-50 text-slate-600">
                        <tr>
                          <th className="px-4 py-3">Date & Time</th>
                          <th className="px-4 py-3">Action</th>
                          <th className="px-4 py-3">Description</th>
                          <th className="px-4 py-3">Admin ID</th>
                          <th className="px-4 py-3">Organization ID</th>
                          <th className="px-4 py-3">Details</th>
                        </tr>
                      </thead>

                      <tbody className="divide-y divide-slate-100">
                        {auditLogs.map((log) => (
                          <tr
                            key={log.id}
                            className="align-top hover:bg-slate-50"
                          >
                            <td className="whitespace-nowrap px-4 py-4 text-slate-600">
                              {log.created_at
                                ? new Date(log.created_at).toLocaleString()
                                : '—'}
                            </td>

                            <td className="px-4 py-4">
                              <span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700">
                                {log.action}
                              </span>
                            </td>

                            <td className="min-w-64 px-4 py-4 text-slate-800">
                              {log.description || '—'}
                            </td>

                            <td className="px-4 py-4">
                              {log.admin_user_id ?? '—'}
                            </td>

                            <td className="px-4 py-4">
                              {log.client_id ?? '—'}
                            </td>

                            <td className="min-w-56 px-4 py-4">
                              <pre className="whitespace-pre-wrap break-all text-xs text-slate-500">
                                {log.extra_data
                                  ? JSON.stringify(log.extra_data, null, 2)
                                  : '—'}
                              </pre>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
            </div>
          ) : activePage === 'API Explorer' ? (
            <ApiExplorer apiUrl={API_URL} token={token} />
          ) : (
            <div className="rounded-xl border border-slate-200 bg-white p-8 shadow-sm">
              <h3 className="text-xl font-bold">{activePage}</h3>

              <p className="mt-2 text-sm text-slate-500">
                This section will be connected to the OCR backend in the upcoming steps.
              </p>
            </div>
          )}

        </div>
      </main>
    </div>
  )
}

export default App
