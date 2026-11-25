
import { useEffect, useMemo, useState } from 'react'

const METHODS = ['get', 'post', 'put', 'patch', 'delete']

function pretty(value) {
  return JSON.stringify(value, null, 2)
}

function getRequestBodyInfo(operation) {
  const content = operation?.requestBody?.content || {}
  const mediaType = Object.keys(content).find((type) =>
    ['application/json', 'multipart/form-data', 'application/x-www-form-urlencoded'].includes(type)
  )

  return {
    mediaType: mediaType || '',
    schema: mediaType ? content[mediaType]?.schema || {} : {},
  }
}

function getSchemaProperties(schema, openApi) {
  if (!schema) return {}
  if (schema.$ref) {
    const name = schema.$ref.split('/').pop()
    return openApi?.components?.schemas?.[name]?.properties || {}
  }
  return schema.properties || {}
}

function makeDefaultBody(schema, openApi) {
  const properties = getSchemaProperties(schema, openApi)
  const result = {}

  Object.entries(properties).forEach(([key, value]) => {
    if (value.type === 'array') result[key] = []
    else if (value.type === 'integer' || value.type === 'number') result[key] = 0
    else if (value.type === 'boolean') result[key] = false
    else if (value.type === 'object') result[key] = {}
    else result[key] = ''
  })

  return result
}

function ApiExplorer({ apiUrl, token }) {
  const [openApi, setOpenApi] = useState(null)
  const [loadingSpec, setLoadingSpec] = useState(true)
  const [specError, setSpecError] = useState('')
  const [selectedKey, setSelectedKey] = useState('')
  const [pathValues, setPathValues] = useState({})
  const [queryValues, setQueryValues] = useState({})
  const [bodyText, setBodyText] = useState('{}')
  const [selectedFile, setSelectedFile] = useState(null)
  const [ocrApiKey, setOcrApiKey] = useState('')
  const [sending, setSending] = useState(false)
  const [responseData, setResponseData] = useState(null)
  const [responseStatus, setResponseStatus] = useState(null)
  const [requestError, setRequestError] = useState('')

  useEffect(() => {
    let cancelled = false

    async function loadOpenApi() {
      setLoadingSpec(true)
      setSpecError('')

      try {
        const response = await fetch(`${apiUrl}/openapi.json`)
        if (!response.ok) {
          throw new Error(`Could not load API documentation (${response.status}).`)
        }

        const data = await response.json()
        if (!cancelled) {
          setOpenApi(data)
          const first = Object.entries(data.paths || {}).flatMap(([path, methods]) =>
            METHODS.filter((method) => methods[method]).map((method) => `${method.toUpperCase()} ${path}`)
          )[0]
          setSelectedKey(first || '')
        }
      } catch (error) {
        if (!cancelled) setSpecError(error.message)
      } finally {
        if (!cancelled) setLoadingSpec(false)
      }
    }

    loadOpenApi()
    return () => {
      cancelled = true
    }
  }, [apiUrl])

  const endpoints = useMemo(() => {
    if (!openApi?.paths) return []

    return Object.entries(openApi.paths).flatMap(([path, methods]) =>
      METHODS.filter((method) => methods[method]).map((method) => ({
        key: `${method.toUpperCase()} ${path}`,
        path,
        method,
        operation: methods[method],
      }))
    )
  }, [openApi])

  const selectedEndpoint = endpoints.find((item) => item.key === selectedKey)
  const parameters = selectedEndpoint?.operation?.parameters || []
  const pathParameters = parameters.filter((item) => item.in === 'path')
  const queryParameters = parameters.filter((item) => item.in === 'query')
  const bodyInfo = getRequestBodyInfo(selectedEndpoint?.operation)
  const bodyProperties = getSchemaProperties(bodyInfo.schema, openApi)
  const isMultipart = bodyInfo.mediaType === 'multipart/form-data'
  const isOcrEndpoint = selectedEndpoint?.path === '/extract'
  const needsAdminAuth = selectedEndpoint?.path?.startsWith('/admin/') &&
    selectedEndpoint?.path !== '/admin/login'

  function selectEndpoint(key) {
    setSelectedKey(key)
    setPathValues({})
    setQueryValues({})
    setSelectedFile(null)
    setResponseData(null)
    setResponseStatus(null)
    setRequestError('')

    const endpoint = endpoints.find((item) => item.key === key)
    if (endpoint) {
      const info = getRequestBodyInfo(endpoint.operation)
      setBodyText(pretty(makeDefaultBody(info.schema, openApi)))
    } else {
      setBodyText('{}')
    }
  }

  function updateValue(setter, name, value) {
    setter((previous) => ({ ...previous, [name]: value }))
  }

  async function handleSendRequest(event) {
    event.preventDefault()
    if (!selectedEndpoint) return

    setSending(true)
    setRequestError('')
    setResponseData(null)
    setResponseStatus(null)

    try {
      let requestPath = selectedEndpoint.path

      pathParameters.forEach((parameter) => {
        const value = pathValues[parameter.name]
        if (value === undefined || value === '') {
          throw new Error(`Please enter the path parameter: ${parameter.name}`)
        }
        requestPath = requestPath.replace(
          `{${parameter.name}}`,
          encodeURIComponent(value)
        )
      })

      const url = new URL(`${apiUrl}${requestPath}`)
      queryParameters.forEach((parameter) => {
        const value = queryValues[parameter.name]
        if (value !== undefined && value !== '') {
          url.searchParams.set(parameter.name, value)
        }
      })

      const headers = {}
      let body

      if (needsAdminAuth) {
        if (!token) throw new Error('Admin login token is missing. Please sign in again.')
        headers.Authorization = `Bearer ${token}`
      }

      if (isOcrEndpoint) {
        if (!ocrApiKey.trim()) throw new Error('Enter the organization API key for this OCR request.')
        headers['X-API-Key'] = ocrApiKey.trim()
      }

      if (selectedEndpoint.operation?.requestBody) {
        if (isMultipart) {
          const formData = new FormData()
          const fileProperty = Object.keys(bodyProperties).find((key) =>
            bodyProperties[key]?.format === 'binary' || key === 'file'
          )

          if (fileProperty) {
            if (!selectedFile) throw new Error('Please select a file to upload.')
            formData.append(fileProperty, selectedFile)
          }

          Object.entries(bodyProperties).forEach(([key, schema]) => {
            if (key === fileProperty) return
            if (schema.type === 'array') {
              const rawValue = queryValues[`body_${key}`] || ''
              rawValue.split(',').map((item) => item.trim()).filter(Boolean)
                .forEach((item) => formData.append(key, item))
            } else {
              const value = queryValues[`body_${key}`]
              if (value !== undefined && value !== '') formData.append(key, value)
            }
          })

          body = formData
        } else if (bodyInfo.mediaType === 'application/x-www-form-urlencoded') {
          const formData = new URLSearchParams()
          Object.entries(JSON.parse(bodyText || '{}')).forEach(([key, value]) => {
            if (value !== undefined && value !== null) formData.set(key, String(value))
          })
          headers['Content-Type'] = 'application/x-www-form-urlencoded'
          body = formData
        } else {
          headers['Content-Type'] = 'application/json'
          body = bodyText.trim() ? bodyText : '{}'
          JSON.parse(body)
        }
      }

      const response = await fetch(url.toString(), {
        method: selectedEndpoint.method.toUpperCase(),
        headers,
        body,
      })

      const responseText = await response.text()
      let data

      try {
        data = responseText ? JSON.parse(responseText) : '(Empty response)'
      } catch {
        data = responseText
      }

      setResponseStatus(response.status)
      setResponseData(data)
    } catch (error) {
      setRequestError(error.message)
    } finally {
      setSending(false)
    }
  }

  if (loadingSpec) {
    return <div className="rounded-xl border bg-white p-6 text-sm text-slate-500">Loading API documentation...</div>
  }

  if (specError) {
    return (
      <div className="rounded-xl border border-red-200 bg-white p-6">
        <h3 className="font-bold text-slate-900">Unable to load API Explorer</h3>
        <p className="mt-2 text-sm text-red-700">{specError}</p>
        <p className="mt-2 text-sm text-slate-500">
          Check that the FastAPI backend is running and that {apiUrl}/openapi.json is accessible.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h3 className="text-xl font-bold text-slate-900">API Explorer</h3>
        <p className="mt-1 text-sm text-slate-500">
          Select an endpoint from your FastAPI documentation, provide its inputs, and send a request.
        </p>

        <form onSubmit={handleSendRequest} className="mt-6 space-y-5">
          <div>
            <label className="mb-2 block text-sm font-medium text-slate-700">Endpoint</label>
            <select
              value={selectedKey}
              onChange={(event) => selectEndpoint(event.target.value)}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-3 text-sm"
            >
              {endpoints.map((endpoint) => (
                <option key={endpoint.key} value={endpoint.key}>{endpoint.key}</option>
              ))}
            </select>
          </div>

          {selectedEndpoint && (
            <div className="rounded-lg bg-slate-50 p-4">
              <p className="font-semibold text-slate-800">
                {selectedEndpoint.operation.summary || selectedEndpoint.operation.operationId || selectedEndpoint.path}
              </p>
              {selectedEndpoint.operation.description && (
                <p className="mt-1 text-sm text-slate-500">{selectedEndpoint.operation.description}</p>
              )}
              <p className="mt-2 break-all font-mono text-xs text-slate-500">
                {selectedEndpoint.path}
              </p>
            </div>
          )}

          {needsAdminAuth && (
            <div className="rounded-lg border border-blue-100 bg-blue-50 p-3 text-sm text-blue-800">
              Admin authentication will be sent automatically using your current dashboard login.
            </div>
          )}

          {isOcrEndpoint && (
            <div>
              <label className="mb-2 block text-sm font-medium text-slate-700">Organization API Key</label>
              <input
                type="password"
                value={ocrApiKey}
                onChange={(event) => setOcrApiKey(event.target.value)}
                autoComplete="off"
                placeholder="Enter X-API-Key"
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
            </div>
          )}

          {pathParameters.length > 0 && (
            <div className="space-y-3">
              <h4 className="font-semibold text-slate-900">Path Parameters</h4>
              {pathParameters.map((parameter) => (
                <div key={parameter.name}>
                  <label className="mb-1 block text-sm font-medium text-slate-700">
                    {parameter.name} {parameter.required && <span className="text-red-600">*</span>}
                  </label>
                  <input
                    required={parameter.required}
                    value={pathValues[parameter.name] || ''}
                    onChange={(event) => updateValue(setPathValues, parameter.name, event.target.value)}
                    placeholder={parameter.description || parameter.name}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  />
                </div>
              ))}
            </div>
          )}

          {queryParameters.length > 0 && (
            <div className="space-y-3">
              <h4 className="font-semibold text-slate-900">Query Parameters</h4>
              {queryParameters.map((parameter) => (
                <div key={parameter.name}>
                  <label className="mb-1 block text-sm font-medium text-slate-700">
                    {parameter.name} {parameter.required && <span className="text-red-600">*</span>}
                  </label>
                  <input
                    required={parameter.required}
                    value={queryValues[parameter.name] || ''}
                    onChange={(event) => updateValue(setQueryValues, parameter.name, event.target.value)}
                    placeholder={parameter.description || parameter.name}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  />
                </div>
              ))}
            </div>
          )}

          {selectedEndpoint?.operation?.requestBody && (
            <div className="space-y-3">
              <h4 className="font-semibold text-slate-900">Request Body</h4>

              {isMultipart ? (
                <>
                  {Object.entries(bodyProperties).map(([key, schema]) => (
                    <div key={key}>
                      <label className="mb-1 block text-sm font-medium text-slate-700">{key}</label>
                      {schema.format === 'binary' || key === 'file' ? (
                        <input
                          type="file"
                          onChange={(event) => setSelectedFile(event.target.files?.[0] || null)}
                          className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm"
                        />
                      ) : (
                        <input
                          value={queryValues[`body_${key}`] || ''}
                          onChange={(event) => updateValue(setQueryValues, `body_${key}`, event.target.value)}
                          placeholder={schema.description || key}
                          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                        />
                      )}
                    </div>
                  ))}
                  {Object.keys(bodyProperties).length === 0 && (
                    <p className="text-sm text-slate-500">This endpoint expects multipart form data.</p>
                  )}
                </>
              ) : (
                <>
                  <p className="text-xs text-slate-500">
                    Enter a JSON request body. The editor is prefilled with fields detected from the API schema.
                  </p>
                  <textarea
                    value={bodyText}
                    onChange={(event) => setBodyText(event.target.value)}
                    rows={10}
                    spellCheck="false"
                    className="w-full rounded-lg border border-slate-300 bg-slate-950 p-4 font-mono text-xs text-green-100 outline-none focus:border-blue-500"
                  />
                </>
              )}
            </div>
          )}

          {requestError && (
            <div className="rounded-lg bg-red-50 p-4 text-sm text-red-700">{requestError}</div>
          )}

          <button
            type="submit"
            disabled={sending || !selectedEndpoint}
            className="rounded-lg bg-blue-600 px-5 py-3 text-sm font-semibold text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {sending ? 'Sending request...' : 'Send Request'}
          </button>
        </form>
      </div>

      {(responseStatus !== null || responseData !== null) && (
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-lg font-bold text-slate-900">Response</h3>
            <span className={`rounded-full px-3 py-1 text-xs font-semibold ${
              responseStatus >= 200 && responseStatus < 300
                ? 'bg-green-50 text-green-700'
                : 'bg-red-50 text-red-700'
            }`}>
              HTTP {responseStatus}
            </span>
          </div>
          <pre className="max-h-[600px] overflow-auto rounded-lg bg-slate-950 p-4 text-xs text-green-100">
            {typeof responseData === 'string' ? responseData : pretty(responseData)}
          </pre>
        </div>
      )}
    </div>
  )
}

export default ApiExplorer
