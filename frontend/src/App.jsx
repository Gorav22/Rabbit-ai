import { useState, useRef, useCallback } from 'react'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const STEPS = [
  { id: 'parse', label: 'Parsing sales data…', icon: '📊' },
  { id: 'ai', label: 'Generating AI summary…', icon: '🤖' },
  { id: 'email', label: 'Sending to your inbox…', icon: '📧' },
]

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
}

function validateEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
}

/* ── Upload Zone Component ───────────────────────────────────────────────── */
function UploadZone({ file, onFile, onRemove }) {
  const [dragging, setDragging] = useState(false)
  const inputRef = useRef(null)

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    setDragging(false)
    const dropped = e.dataTransfer.files[0]
    if (dropped) onFile(dropped)
  }, [onFile])

  const handleDrag = (e) => { e.preventDefault(); setDragging(true) }
  const handleDragLeave = () => setDragging(false)
  const handleChange = (e) => { if (e.target.files[0]) onFile(e.target.files[0]) }

  if (file) {
    return (
      <div className="field">
        <label>📁 Selected File</label>
        <div className="file-selected" onClick={() => inputRef.current?.click()}>
          <span className="file-icon">
            {file.name.endsWith('.csv') ? '📋' : '📊'}
          </span>
          <div className="file-info">
            <div className="file-name">{file.name}</div>
            <div className="file-size">{formatBytes(file.size)} · Click to change</div>
          </div>
          <button type="button" className="remove-btn" onClick={(e) => { e.stopPropagation(); onRemove() }} title="Remove file">✕</button>
          <input ref={inputRef} type="file" accept=".csv,.xlsx,.xls" onChange={handleChange} style={{ display: 'none' }} />
        </div>
      </div>
    )
  }

  return (
    <div className="field">
      <label>📁 Sales Data File</label>
      <div
        className={`upload-zone ${dragging ? 'dragging' : ''}`}
        onDrop={handleDrop}
        onDragOver={handleDrag}
        onDragLeave={handleDragLeave}
      >
        <input type="file" accept=".csv,.xlsx,.xls" onChange={handleChange} />
        <div className="upload-icon-wrap">📤</div>
        <h3>Drop your file here</h3>
        <p>or click to browse from your computer</p>
        <div className="upload-types">
          <span className="type-badge csv">CSV</span>
          <span className="type-badge xlsx">XLSX</span>
          <span className="type-badge xls">XLS</span>
        </div>
        <p style={{ marginTop: '10px', fontSize: '12px', color: 'var(--text-muted)' }}>CSV · XLSX · XLS</p>
      </div>
    </div>
  )
}

/* ── Loading Steps Component ─────────────────────────────────────────────── */
function LoadingSteps({ currentStep }) {
  return (
    <div className="loading-steps">
      {STEPS.map((step, i) => {
        const state = i < currentStep ? 'done' : i === currentStep ? 'active' : ''
        return (
          <div key={step.id} className={`step ${state}`}>
            <div className="step-dot">
              {i < currentStep ? '✓' : step.icon}
            </div>
            <span>{step.label}</span>
          </div>
        )
      })}
    </div>
  )
}

/* ── Status Banner Component ─────────────────────────────────────────────── */
function StatusBanner({ status, data, onRetry, onNewAnalysis }) {
  if (status === 'loading') {
    return (
      <div className="status-banner loading">
        <div className="banner-header">
          <div className="banner-icon">⚡</div>
          <div>
            <div className="banner-title">Processing Your Data</div>
            <div className="banner-body">Hang tight — your AI summary is being crafted…</div>
          </div>
        </div>
        <LoadingSteps currentStep={data.step ?? 0} />
      </div>
    )
  }

  if (status === 'success') {
    return (
      <div className="status-banner success">
        <div className="banner-header">
          <div className="banner-icon">✅</div>
          <div>
            <div className="banner-title">Analysis Complete!</div>
            <div className="banner-body">
              Your executive summary has been sent to <strong style={{ color: '#6ee7b7' }}>{data.recipient}</strong>.
            </div>
          </div>
        </div>
        {data.summary_preview && (
          <>
            <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '12px', letterSpacing: '0.5px', textTransform: 'uppercase', fontWeight: 600 }}>
              Summary Preview
            </div>
            <div className="summary-preview">{data.summary_preview}</div>
          </>
        )}
        <div className="meta-tags">
          {data.rows_processed && <span className="meta-tag">📊 {data.rows_processed} rows processed</span>}
          {data.columns_detected && <span className="meta-tag">🔢 {data.columns_detected.length} columns</span>}
          <span className="meta-tag">🤖 Groq · Llama 3</span>
        </div>
        <button className="new-analysis-btn" onClick={onNewAnalysis}>
          ➕ New Analysis
        </button>
      </div>
    )
  }

  if (status === 'error') {
    return (
      <div className="status-banner error">
        <div className="banner-header">
          <div className="banner-icon">⚠️</div>
          <div>
            <div className="banner-title">Something Went Wrong</div>
            <div className="banner-body">{data.message}</div>
          </div>
        </div>
        <button className="retry-btn" onClick={onRetry}>
          🔄 Try Again
        </button>
      </div>
    )
  }

  return null
}

/* ── Main App ─────────────────────────────────────────────────────────────── */
export default function App() {
  const [file, setFile] = useState(null)
  const [email, setEmail] = useState('')
  const [emailError, setEmailError] = useState('')
  const [status, setStatus] = useState('idle') // idle | loading | success | error
  const [statusData, setStatusData] = useState({})

  const handleFile = (f) => setFile(f)
  const handleRemove = () => setFile(null)

  const handleEmailChange = (e) => {
    setEmail(e.target.value)
    if (emailError && validateEmail(e.target.value)) setEmailError('')
  }

  const handleReset = () => {
    setStatus('idle')
    setStatusData({})
    setFile(null)
    setEmail('')
    setEmailError('')
  }

  const handleRetry = () => {
    setStatus('idle')
    setStatusData({})
  }

  const handleSubmit = async (e) => {
    e.preventDefault()

    // Validate
    if (!file) return
    if (!validateEmail(email)) {
      setEmailError('Please enter a valid email address.')
      return
    }

    setStatus('loading')
    setStatusData({ step: 0 })

    // Simulate step progression for UX
    const stepTimer1 = setTimeout(() => setStatusData(d => ({ ...d, step: 1 })), 1500)
    const stepTimer2 = setTimeout(() => setStatusData(d => ({ ...d, step: 2 })), 4000)

    try {
      const form = new FormData()
      form.append('file', file)
      form.append('email', email)

      const res = await fetch(`${API_BASE}/api/analyze`, {
        method: 'POST',
        body: form,
      })

      clearTimeout(stepTimer1)
      clearTimeout(stepTimer2)

      const json = await res.json()

      if (!res.ok) {
        throw new Error(json.detail || `Server error ${res.status}`)
      }

      setStatus('success')
      setStatusData(json)
    } catch (err) {
      clearTimeout(stepTimer1)
      clearTimeout(stepTimer2)
      setStatus('error')
      setStatusData({ message: err.message || 'An unexpected error occurred.' })
    }
  }

  const canSubmit = file && email && status !== 'loading'

  return (
    <>
      {/* Background effects */}
      <div className="bg-mesh" />
      <div className="orb orb-1" />
      <div className="orb orb-2" />
      <div className="orb orb-3" />

      <div className="app-wrapper">
        {/* Header */}
        <header className="site-header">
          <div className="header-brand">
            <div className="brand-logo">🐇</div>
            <div className="brand-name">Rabbitt AI</div>
          </div>
          <p className="site-tagline">Sales Insight Automator — Powered by Groq · Llama 3</p>
          <div style={{ display: 'flex', justifyContent: 'center', gap: '8px', marginTop: '12px' }}>
            <div className="badge-ai">
              <div className="badge-dot" />
              Groq AI · Live
            </div>
          </div>
          <div className="feature-pills">
            <span className="pill">⚡ Instant Summaries</span>
            <span className="pill">📧 Email Delivery</span>
            <span className="pill">🔒 Secured API</span>
            <span className="pill">📊 CSV & Excel</span>
          </div>
        </header>

        {/* Stats row */}
        <div className="stats-row">
          <div className="stat-card">
            <div className="stat-value purple">~3s</div>
            <div className="stat-label">Avg. Response</div>
          </div>
          <div className="stat-card">
            <div className="stat-value green">100%</div>
            <div className="stat-label">AI Powered</div>
          </div>
          <div className="stat-card">
            <div className="stat-value blue">Groq</div>
            <div className="stat-label">Llama 3.3-70b</div>
          </div>
        </div>

        {/* Status banner (above form when active) */}
        {status !== 'idle' && (
          <StatusBanner
            status={status}
            data={statusData}
            onRetry={handleRetry}
            onNewAnalysis={handleReset}
          />
        )}

        {/* Main upload card (hidden when success) */}
        {status !== 'success' && (
          <div className="main-card">
            <div className="card-header">
              <div className="card-title">
                <span>📈</span> Upload Sales Data
              </div>
              <p className="card-subtitle">
                Upload your quarterly CSV or Excel file. Our AI will analyze it and deliver
                a professional executive summary straight to your inbox.
              </p>
            </div>

            <form className="card-body" onSubmit={handleSubmit}>
              <UploadZone file={file} onFile={handleFile} onRemove={handleRemove} />

              <div className="field">
                <label>📬 Recipient Email</label>
                <div className="input-wrap">
                  <span className="input-icon">✉️</span>
                  <input
                    type="email"
                    placeholder="executive@company.com"
                    value={email}
                    onChange={handleEmailChange}
                    className={emailError ? 'error' : ''}
                    disabled={status === 'loading'}
                    required
                  />
                </div>
                {emailError && (
                  <span style={{ fontSize: '12px', color: 'var(--error)', marginTop: '2px' }}>
                    ⚠ {emailError}
                  </span>
                )}
              </div>

              <button
                type="submit"
                className={`submit-btn ${status === 'loading' ? 'loading' : ''}`}
                disabled={!canSubmit}
              >
                {status === 'loading' ? (
                  <>
                    <div className="spinner" />
                    Analyzing…
                  </>
                ) : (
                  <>
                    ⚡ Generate AI Summary & Send
                  </>
                )}
              </button>

              <p style={{ fontSize: '11px', color: 'var(--text-muted)', textAlign: 'center', marginTop: '-8px' }}>
                🔒 Your data is processed securely and never stored permanently.
              </p>
            </form>
          </div>
        )}

        {/* Footer */}
        <footer className="site-footer">
          <p>
            Built by <strong>Rabbitt AI Engineering</strong> · Secured API ·{' '}
            <a href={`${API_BASE}/docs`} target="_blank" rel="noopener noreferrer">
              Swagger Docs ↗
            </a>
          </p>
        </footer>
      </div>
    </>
  )
}
