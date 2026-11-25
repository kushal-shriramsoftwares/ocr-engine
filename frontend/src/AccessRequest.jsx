
import { useState } from 'react'

function AccessRequest({ apiUrl, onBack }) {
  const [formData, setFormData] = useState({
    organization_name: '',
    industry: '',
    contact_name: '',
    contact_email: '',
    contact_phone: '',
    requested_services: [],
  })

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(null)

  function handleChange(event) {
    const { name, value } = event.target

    setFormData((previous) => ({
      ...previous,
      [name]: value,
    }))
  }

  function handleServiceChange(event) {
    const { value, checked } = event.target

    setFormData((previous) => ({
      ...previous,
      requested_services: checked
        ? [...previous.requested_services, value]
        : previous.requested_services.filter(
            (service) => service !== value
          ),
    }))
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    setSuccess(null)

    if (formData.requested_services.length === 0) {
      setError('Please select at least one OCR service.')
      return
    }

    setLoading(true)

    try {
      const response = await fetch(`${apiUrl}/access-requests/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...formData,
          organization_name: formData.organization_name.trim(),
          industry: formData.industry.trim(),
          contact_name: formData.contact_name.trim(),
          contact_email: formData.contact_email.trim(),
          contact_phone: formData.contact_phone.trim(),
        }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(
          data.detail || 'Unable to submit your access request.'
        )
      }

      setSuccess(data)
      setFormData({
        organization_name: '',
        industry: '',
        contact_name: '',
        contact_email: '',
        contact_phone: '',
        requested_services: [],
      })
    } catch (err) {
      setError(
        err.message === 'Failed to fetch'
          ? 'Unable to connect to the OCR platform. Please try again.'
          : err.message
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-100 px-4 py-10">
      <div className="mx-auto max-w-2xl rounded-2xl border border-slate-200 bg-white p-6 shadow-xl sm:p-8">

        <div className="mb-7 text-center">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-600 text-2xl font-bold text-white">
            O
          </div>

          <h1 className="mt-4 text-2xl font-bold text-slate-900">
            OCR Platform
          </h1>

          <p className="mt-2 text-sm text-slate-500">
            Request access to our OCR API services
          </p>
        </div>

        {success ? (
          <div className="rounded-xl border border-green-200 bg-green-50 p-6">
            <h2 className="text-lg font-bold text-green-800">
              Access Request Submitted!
            </h2>

            <p className="mt-2 text-sm text-green-700">
              Your request has been submitted successfully. Our administrator
              will review your application.
            </p>

            {success.request_id && (
              <p className="mt-3 text-sm font-semibold text-green-800">
                Request ID: {success.request_id}
              </p>
            )}

            <p className="mt-2 text-sm text-green-700">
              Status: {success.status || 'Pending'}
            </p>

            <button
              type="button"
              onClick={onBack}
              className="mt-6 rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-blue-700"
            >
              Back to Admin Login
            </button>
          </div>
        ) : (
          <>
            <div className="mb-6">
              <h2 className="text-xl font-bold text-slate-900">
                Organization Access Request
              </h2>

              <p className="mt-1 text-sm text-slate-500">
                Fill in your organization details to request access.
                No admin login is required.
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-5">

              <div>
                <label className="mb-2 block text-sm font-medium text-slate-700">
                  Organization Name
                </label>

                <input
                  type="text"
                  name="organization_name"
                  value={formData.organization_name}
                  onChange={handleChange}
                  minLength={2}
                  maxLength={200}
                  required
                  placeholder="Enter organization name"
                  className="w-full rounded-lg border border-slate-300 px-4 py-3 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                />
              </div>

              <div>
                <label className="mb-2 block text-sm font-medium text-slate-700">
                  Industry
                </label>

                <input
                  type="text"
                  name="industry"
                  value={formData.industry}
                  onChange={handleChange}
                  minLength={2}
                  maxLength={100}
                  required
                  placeholder="e.g. Banking, Finance, Healthcare"
                  className="w-full rounded-lg border border-slate-300 px-4 py-3 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                />
              </div>

              <div>
                <label className="mb-2 block text-sm font-medium text-slate-700">
                  Contact Person Name
                </label>

                <input
                  type="text"
                  name="contact_name"
                  value={formData.contact_name}
                  onChange={handleChange}
                  minLength={2}
                  maxLength={150}
                  required
                  placeholder="Enter contact person's name"
                  className="w-full rounded-lg border border-slate-300 px-4 py-3 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                />
              </div>

              <div>
                <label className="mb-2 block text-sm font-medium text-slate-700">
                  Contact Email
                </label>

                <input
                  type="email"
                  name="contact_email"
                  value={formData.contact_email}
                  onChange={handleChange}
                  maxLength={255}
                  required
                  placeholder="name@organization.com"
                  className="w-full rounded-lg border border-slate-300 px-4 py-3 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                />
              </div>

              <div>
                <label className="mb-2 block text-sm font-medium text-slate-700">
                  Contact Phone
                </label>

                <input
                  type="tel"
                  name="contact_phone"
                  value={formData.contact_phone}
                  onChange={handleChange}
                  maxLength={30}
                  required
                  placeholder="Enter contact phone number"
                  className="w-full rounded-lg border border-slate-300 px-4 py-3 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                />
              </div>

              <div>
                <label className="mb-3 block text-sm font-medium text-slate-700">
                  Requested OCR Services
                </label>

                <div className="space-y-3 rounded-lg border border-slate-200 p-4">

                  <label className="flex items-center gap-3 text-sm text-slate-700">
                    <input
                      type="checkbox"
                      value="aadhaar_ocr"
                      checked={formData.requested_services.includes('aadhaar_ocr')}
                      onChange={handleServiceChange}
                      className="h-4 w-4"
                    />
                    Aadhaar OCR
                  </label>

                  <label className="flex items-center gap-3 text-sm text-slate-700">
                    <input
                      type="checkbox"
                      value="pan_ocr"
                      checked={formData.requested_services.includes('pan_ocr')}
                      onChange={handleServiceChange}
                      className="h-4 w-4"
                    />
                    PAN OCR
                  </label>

                </div>
              </div>

              {error && (
                <div className="rounded-lg bg-red-50 p-4 text-sm text-red-700">
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className="w-full rounded-lg bg-blue-600 px-5 py-3 text-sm font-semibold text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {loading ? 'Submitting Request...' : 'Submit Access Request'}
              </button>

              <button
                type="button"
                onClick={onBack}
                className="w-full rounded-lg border border-slate-300 px-5 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-50"
              >
                Back to Admin Login
              </button>

            </form>
          </>
        )}
      </div>
    </div>
  )
}

export default AccessRequest