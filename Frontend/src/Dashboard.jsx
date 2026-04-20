import { useEffect, useEffectEvent, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'

const API_BASE_URL = 'http://127.0.0.1:8000'

const quickActions = [
  {
    title: 'Upload Documents',
    description: 'Add PDFs, docs, or videos',
    icon: 'upload',
  },
  {
    title: 'Knowledge Base',
    description: 'Manage your sources',
    icon: 'book',
  },
  {
    title: 'Prompt Library',
    description: 'Reuse proven instructions',
    icon: 'spark',
  },
  {
    title: 'Analytics',
    description: 'View performance stats',
    icon: 'chart',
  },
]

function DashboardIcon({ type }) {
  const icons = {
    assistant: (
      <path d="M8 9.5h8M10 6.5h4M9 13.5h6M9.5 4h5a2.5 2.5 0 0 1 2.5 2.5V14A2 2 0 0 1 15 16H9a2 2 0 0 1-2-2V6.5A2.5 2.5 0 0 1 9.5 4ZM5.5 8.5h1v4h-1m11 0h1v-4h-1" />
    ),
    document: (
      <path d="M8.5 4.5h5l3 3V15a2 2 0 0 1-2 2h-6a2 2 0 0 1-2-2V6.5a2 2 0 0 1 2-2Zm5 0V8h3M9.5 11h5M9.5 14h5" />
    ),
    chat: <path d="M7 6.5A2.5 2.5 0 0 1 9.5 4h6A2.5 2.5 0 0 1 18 6.5v4A2.5 2.5 0 0 1 15.5 13H11l-3.5 3v-3H9.5A2.5 2.5 0 0 1 7 10.5Z" />,
    upload: <path d="M12 15V7m0 0-3 3m3-3 3 3M7 15.5v1A1.5 1.5 0 0 0 8.5 18h7a1.5 1.5 0 0 0 1.5-1.5v-1" />,
    book: <path d="M6.5 5.5A2.5 2.5 0 0 1 9 3h8v13.5A2.5 2.5 0 0 0 14.5 14H6.5Zm0 0V17A2 2 0 0 0 8.5 19H16" />,
    spark: <path d="m12 4 1.3 3.7L17 9l-3.7 1.3L12 14l-1.3-3.7L7 9l3.7-1.3ZM6 14l.7 2 .8.3-.8.3L6 18l-.7-1.4-.8-.3.8-.3Zm12-1 .9 2.3 2.1.9-2.1.9L18 19.5l-.9-2.3-2.1-.9 2.1-.9Z" />,
    chart: <path d="M6 17.5V11m4 6.5V8m4 9.5v-5m4 5v-8" />,
    plus: <path d="M12 7v10M7 12h10" />,
    bell: <path d="M9 17h6M10 17a2 2 0 0 0 4 0m-6-2h8l-1-2v-2.5a3 3 0 1 0-6 0V13Z" />,
    search: <path d="m16 16 3 3M9.5 17a7.5 7.5 0 1 1 0-15 7.5 7.5 0 0 1 0 15Z" />,
    clock: <path d="M12 7.5v4l2.5 1.5M19 12a7 7 0 1 1-14 0 7 7 0 0 1 14 0Z" />,
    trash: <path d="M8 7h8m-7 0 .5 10.5A1.5 1.5 0 0 0 11 19h2a1.5 1.5 0 0 0 1.5-1.5L15 7M10 7V5.8A1.8 1.8 0 0 1 11.8 4h.4A1.8 1.8 0 0 1 14 5.8V7m-7 0h10" />,
  }

  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" className="dashboard-icon">
      {icons[type]}
    </svg>
  )
}

function formatTimestamp(value) {
  if (!value) {
    return 'Just now'
  }

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return 'Just now'
  }

  return new Intl.DateTimeFormat('en-IN', {
    day: 'numeric',
    month: 'short',
    hour: 'numeric',
    minute: '2-digit',
  }).format(date)
}

function CreateAssistantModal({
  isOpen,
  onClose,
  onCreated,
}) {
  const [assistantName, setAssistantName] = useState('')
  const [selectedFiles, setSelectedFiles] = useState([])
  const [errorMessage, setErrorMessage] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    if (!isOpen) {
      setAssistantName('')
      setSelectedFiles([])
      setErrorMessage('')
      setIsSubmitting(false)
    }
  }, [isOpen])

  if (!isOpen) {
    return null
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setErrorMessage('')

    if (!assistantName.trim()) {
      setErrorMessage('Assistant name is required.')
      return
    }

    if (selectedFiles.length === 0) {
      setErrorMessage('Please upload at least one PDF or video file.')
      return
    }

    const token = localStorage.getItem('token')
    if (!token) {
      setErrorMessage('Login expired. Please login again.')
      return
    }

    const formData = new FormData()
    formData.append('assistant_name', assistantName.trim())
    selectedFiles.forEach((file) => {
      formData.append('files', file)
    })

    try {
      setIsSubmitting(true)
      const response = await fetch(`${API_BASE_URL}/assistants`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      })

      const data = await response.json()
      if (!response.ok) {
        throw new Error(data.detail || 'Unable to create assistant.')
      }

      onCreated(data.assistant)
      onClose()
    } catch (error) {
      setErrorMessage(error.message || 'Unable to create assistant.')
      setIsSubmitting(false)
    }
  }

  return (
    <div className="auth-modal-overlay" onClick={onClose} role="presentation">
      <section
        className="auth-modal dashboard-create-modal"
        onClick={(event) => event.stopPropagation()}
        aria-modal="true"
        role="dialog"
        aria-labelledby="create-assistant-title"
      >
        <button type="button" className="auth-modal__close" onClick={onClose} aria-label="Close">
          x
        </button>

        <div className="auth-modal__glow" aria-hidden="true" />
        <span className="auth-modal__badge">New assistant</span>
        <h2 id="create-assistant-title">Create your next AI assistant</h2>
        <p className="auth-modal__subtitle">
          Add an assistant name, upload PDFs or videos, and we will start embedding them right away.
        </p>

        <form className="auth-form" onSubmit={handleSubmit}>
          <label className="auth-form__field">
            <span>Assistant Name</span>
            <input
              type="text"
              value={assistantName}
              onChange={(event) => setAssistantName(event.target.value)}
              placeholder="e.g. Product Knowledge Bot"
              required
            />
          </label>

          <label className="auth-form__field">
            <span>Knowledge Files</span>
            <input
              type="file"
              accept=".pdf,.docx,video/*"
              multiple
              onChange={(event) => setSelectedFiles(Array.from(event.target.files || []))}
              required
            />
          </label>

          {selectedFiles.length > 0 ? (
            <div className="dashboard-file-list">
              {selectedFiles.map((file) => (
                <span key={`${file.name}-${file.lastModified}`} className="dashboard-file-pill">
                  {file.name}
                </span>
              ))}
            </div>
          ) : null}

          {errorMessage ? <p className="auth-form__error">{errorMessage}</p> : null}

          <button type="submit" className="auth-form__submit" disabled={isSubmitting}>
            {isSubmitting ? 'Starting assistant...' : 'Create Assistant'}
          </button>
        </form>
      </section>
    </div>
  )
}

function DeleteAssistantModal({
  assistant,
  isDeleting,
  onCancel,
  onConfirm,
}) {
  if (!assistant) {
    return null
  }

  return (
    <div className="auth-modal-overlay" onClick={onCancel} role="presentation">
      <section
        className="auth-modal dashboard-delete-modal"
        onClick={(event) => event.stopPropagation()}
        aria-modal="true"
        role="dialog"
        aria-labelledby="delete-assistant-title"
      >
        <button
          type="button"
          className="auth-modal__close"
          onClick={onCancel}
          aria-label="Close"
          disabled={isDeleting}
        >
          x
        </button>

        <div className="auth-modal__glow" aria-hidden="true" />
        <span className="auth-modal__badge auth-modal__badge--danger">Delete assistant</span>
        <h2 id="delete-assistant-title">Remove {assistant.name}?</h2>
        <p className="auth-modal__subtitle">
          This will delete the assistant card and permanently remove all embeddings related to it.
        </p>

        <div className="dashboard-delete-modal__actions">
          <button type="button" className="dashboard-delete-modal__cancel" onClick={onCancel} disabled={isDeleting}>
            Cancel
          </button>
          <button type="button" className="dashboard-delete-modal__confirm" onClick={onConfirm} disabled={isDeleting}>
            {isDeleting ? 'Deleting...' : 'Delete Assistant'}
          </button>
        </div>
      </section>
    </div>
  )
}

function Dashboard() {
  const navigate = useNavigate()
  const [assistants, setAssistants] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [isCreateOpen, setIsCreateOpen] = useState(false)
  const [dashboardError, setDashboardError] = useState('')
  const [deletingAssistantId, setDeletingAssistantId] = useState(null)
  const [assistantPendingDelete, setAssistantPendingDelete] = useState(null)
  const [isProfileMenuOpen, setIsProfileMenuOpen] = useState(false)
  const profileMenuRef = useRef(null)

  const token = localStorage.getItem('token')
  const userEmail = localStorage.getItem('userEmail') || 'creator@example.com'
  const userName = localStorage.getItem('userName') || userEmail.split('@')[0] || 'Creator'

  const profileInitial = useMemo(() => userName.trim().charAt(0).toUpperCase() || 'C', [userName])

  const clearAuthAndRedirect = (message = 'Login expired. Please login again.') => {
    localStorage.removeItem('token')
    localStorage.removeItem('userEmail')
    localStorage.removeItem('userName')
    setDashboardError(message)
    navigate('/')
  }

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('userEmail')
    localStorage.removeItem('userName')
    setIsProfileMenuOpen(false)
    navigate('/')
  }

  useEffect(() => {
    if (!isProfileMenuOpen) {
      return undefined
    }

    const handlePointerDown = (event) => {
      if (profileMenuRef.current && !profileMenuRef.current.contains(event.target)) {
        setIsProfileMenuOpen(false)
      }
    }

    const handleEscape = (event) => {
      if (event.key === 'Escape') {
        setIsProfileMenuOpen(false)
      }
    }

    window.addEventListener('mousedown', handlePointerDown)
    window.addEventListener('keydown', handleEscape)

    return () => {
      window.removeEventListener('mousedown', handlePointerDown)
      window.removeEventListener('keydown', handleEscape)
    }
  }, [isProfileMenuOpen])

  const fetchAssistants = useEffectEvent(async ({ silent = false } = {}) => {
    if (!token) {
      setDashboardError('Missing login token. Please login again.')
      setIsLoading(false)
      return
    }

    try {
      if (!silent) {
        setIsLoading(true)
      }

      const response = await fetch(`${API_BASE_URL}/assistants`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })

      const data = await response.json()
      if (!response.ok) {
        if (response.status === 401) {
          clearAuthAndRedirect('Session expired. Please login again.')
          return
        }
        throw new Error(data.detail || 'Unable to load assistants.')
      }

      setAssistants(data.assistants || [])
      setDashboardError('')
    } catch (error) {
      setDashboardError(error.message || 'Unable to load assistants.')
    } finally {
      if (!silent) {
        setIsLoading(false)
      }
    }
  })

  useEffect(() => {
    fetchAssistants()
  }, [])

  useEffect(() => {
    if (!assistants.some((assistant) => assistant.status === 'training')) {
      return undefined
    }

    const intervalId = window.setInterval(() => {
      fetchAssistants({ silent: true })
    }, 4000)

    return () => window.clearInterval(intervalId)
  }, [assistants])

  const stats = useMemo(() => {
    const activeAssistants = assistants.filter((assistant) => assistant.status === 'active').length
    const trainingAssistants = assistants.filter((assistant) => assistant.status === 'training').length
    const totalSources = assistants.reduce((sum, assistant) => sum + (assistant.source_count || 0), 0)

    return [
      { label: 'Assistants', value: String(assistants.length), icon: 'assistant' },
      { label: 'Knowledge Sources', value: String(totalSources), icon: 'document' },
      { label: 'Active Now', value: String(activeAssistants || trainingAssistants), icon: 'chat' },
    ]
  }, [assistants])

  const recentActivity = useMemo(() => {
    return assistants.slice(0, 4).map((assistant) => ({
      title: assistant.name,
      detail:
        assistant.status === 'active'
          ? `Assistant is ready with ${assistant.source_count} sources`
          : assistant.status === 'failed'
            ? assistant.last_error || 'Embedding failed. Try again with another name or file set.'
            : 'Embeddings are still processing in the background',
      time: formatTimestamp(assistant.updated_at),
      icon: assistant.status === 'active' ? 'assistant' : assistant.status === 'failed' ? 'document' : 'spark',
    }))
  }, [assistants])

  const handleAssistantCreated = (assistant) => {
    setAssistants((current) => [assistant, ...current])
  }

  const requestAssistantDelete = (assistant) => {
    setAssistantPendingDelete(assistant)
  }

  const handleAssistantDelete = async () => {
    const assistant = assistantPendingDelete
    if (!assistant) {
      return
    }

    const token = localStorage.getItem('token')
    if (!token) {
      setDashboardError('Missing login token. Please login again.')
      return
    }

    try {
      setDeletingAssistantId(assistant.id)
      const response = await fetch(`${API_BASE_URL}/assistants/${assistant.assistant_id}`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })

      const data = await response.json()
      if (!response.ok) {
        if (response.status === 401) {
          clearAuthAndRedirect('Session expired. Please login again.')
          return
        }
        throw new Error(data.detail || 'Unable to delete assistant.')
      }

      setAssistants((current) => current.filter((item) => item.id !== assistant.id))
      setDashboardError('')
      setAssistantPendingDelete(null)
    } catch (error) {
      setDashboardError(error.message || 'Unable to delete assistant.')
    } finally {
      setDeletingAssistantId(null)
    }
  }

  const renderAssistantBody = () => {
    if (isLoading) {
      return <div className="dashboard-empty-state">Loading assistants...</div>
    }

    if (dashboardError) {
      return <div className="dashboard-empty-state dashboard-empty-state--error">{dashboardError}</div>
    }

    if (assistants.length === 0) {
      return (
        <div className="dashboard-empty-state">
          <div className="assistant-card__create-icon">
            <DashboardIcon type="plus" />
          </div>
          <h3>No assistants yet</h3>
          <p>Create your first assistant by uploading PDFs or videos.</p>
          <button
            type="button"
            className="dashboard-button dashboard-button--primary"
            onClick={() => setIsCreateOpen(true)}
          >
            <DashboardIcon type="plus" />
            <span>Create Assistant</span>
          </button>
        </div>
      )
    }

    return (
      <div className="assistant-grid">
        {assistants.map((assistant) => (
          <article key={assistant.id} className="assistant-card">
            <button
              type="button"
              className="assistant-card__delete"
              aria-label={`Delete ${assistant.name}`}
              title="Delete assistant"
              onClick={() => requestAssistantDelete(assistant)}
              disabled={deletingAssistantId === assistant.id}
            >
              <DashboardIcon type="trash" />
            </button>

            <div className="assistant-card__icon">
              <DashboardIcon type="assistant" />
            </div>

            <h3>{assistant.name}</h3>
            <p>
              {assistant.status === 'active'
                ? 'Embeddings are ready and this assistant can now be used across your workspace.'
                : assistant.status === 'failed'
                  ? assistant.last_error || 'Assistant creation failed during embedding.'
                  : 'Files uploaded successfully. Embeddings are still being generated.'}
            </p>

            <div className="assistant-card__meta">
              <span>
                <DashboardIcon type="document" />
                {assistant.source_count} sources
              </span>
              <span>
                <DashboardIcon type="clock" />
                {formatTimestamp(assistant.updated_at)}
              </span>
            </div>

            <div className="assistant-card__footer">
              <span className={`assistant-status assistant-status--${assistant.status}`}>
                <i />
                {assistant.status === 'active'
                  ? 'Active'
                  : assistant.status === 'failed'
                    ? 'Failed'
                    : 'Training'}
              </span>
              <button
                type="button"
                className="assistant-card__chat"
                onClick={() => navigate(`/assistants/${assistant.assistant_id}`)}
                disabled={deletingAssistantId === assistant.id}
              >
                <DashboardIcon type="chat" />
                {deletingAssistantId === assistant.id ? 'Deleting...' : 'Open Chat'}
              </button>
            </div>
          </article>
        ))}

        <article
          className="assistant-card assistant-card--create"
          onClick={() => setIsCreateOpen(true)}
          role="button"
          tabIndex={0}
          onKeyDown={(event) => {
            if (event.key === 'Enter' || event.key === ' ') {
              event.preventDefault()
              setIsCreateOpen(true)
            }
          }}
        >
          <div className="assistant-card__create-icon">
            <DashboardIcon type="plus" />
          </div>
          <h3>Create New Assistant</h3>
          <p>Upload docs &amp; start building</p>
        </article>
      </div>
    )
  }

  return (
    <main className="dashboard-shell">
      <div className="dashboard-layout">
        <header className="dashboard-topbar">
          <div className="dashboard-brand">
            <div className="dashboard-brand__logo">
              <DashboardIcon type="spark" />
            </div>
            <div>
              <span className="dashboard-brand__title">AssistantAI</span>
            </div>
          </div>

          <div className="dashboard-search">
            <DashboardIcon type="search" />
            <span>Search assistants, documents...</span>
            <div className="dashboard-search__shortcut">Ctrl K</div>
          </div>

          <div className="dashboard-topbar__actions">
            <button
              type="button"
              className="dashboard-button dashboard-button--primary"
              onClick={() => setIsCreateOpen(true)}
            >
              <DashboardIcon type="plus" />
              <span>New Assistant</span>
            </button>
            <button type="button" className="dashboard-icon-button" aria-label="Notifications">
              <DashboardIcon type="bell" />
              <span className="dashboard-icon-button__dot" />
            </button>
            <div className="dashboard-profile-wrap" ref={profileMenuRef}>
              <button
                type="button"
                className={`dashboard-profile${isProfileMenuOpen ? ' dashboard-profile--open' : ''}`}
                aria-label="Profile"
                aria-haspopup="menu"
                aria-expanded={isProfileMenuOpen}
                onClick={() => setIsProfileMenuOpen((current) => !current)}
              >
                <span className="dashboard-profile__avatar">{profileInitial}</span>
                <span className="dashboard-profile__caret">{isProfileMenuOpen ? '^' : 'v'}</span>
              </button>

              {isProfileMenuOpen ? (
                <div className="dashboard-profile-menu" role="menu" aria-label="Profile menu">
                  <div className="dashboard-profile-menu__summary">
                    <span className="dashboard-profile-menu__label">Signed in as</span>
                    <strong>{userName}</strong>
                    <span className="dashboard-profile-menu__email">{userEmail}</span>
                  </div>
                  <button
                    type="button"
                    className="dashboard-profile-menu__action"
                    onClick={() => {
                      setIsProfileMenuOpen(false)
                      window.scrollTo({ top: 0, behavior: 'smooth' })
                    }}
                    role="menuitem"
                  >
                    Back to top
                  </button>
                  <button
                    type="button"
                    className="dashboard-profile-menu__action dashboard-profile-menu__action--danger"
                    onClick={handleLogout}
                    role="menuitem"
                  >
                    Logout
                  </button>
                </div>
              ) : null}
            </div>
          </div>
        </header>

        <section className="dashboard-hero">
          <div className="dashboard-hero__content">
            <h1>
              Welcome back, <span>{userName}</span>
            </h1>
            <p>
              Your AI workspace is ready. Build intelligent assistants from your documents
              and videos all in one place.
            </p>
          </div>

          <div className="dashboard-stats">
            {stats.map((stat) => (
              <article key={stat.label} className="dashboard-stat-card">
                <div className="dashboard-stat-card__icon">
                  <DashboardIcon type={stat.icon} />
                </div>
                <div>
                  <strong>{stat.value}</strong>
                  <span>{stat.label}</span>
                </div>
              </article>
            ))}
          </div>
        </section>

        <section className="dashboard-main">
          <div className="dashboard-main__content">
            <div className="dashboard-section-heading">
              <h2>Your Assistants</h2>
              <button type="button" onClick={() => fetchAssistants()}>
                Refresh
              </button>
            </div>
            {renderAssistantBody()}
          </div>

          <aside className="dashboard-sidebar">
            <section className="dashboard-panel">
              <div className="dashboard-panel__heading">
                <h2>Quick Actions</h2>
              </div>

              <div className="quick-actions-grid">
                {quickActions.map((action) => (
                  <article key={action.title} className="quick-action-card">
                    <div className="quick-action-card__icon">
                      <DashboardIcon type={action.icon} />
                    </div>
                    <h3>{action.title}</h3>
                    <p>{action.description}</p>
                  </article>
                ))}
              </div>
            </section>

            <section className="dashboard-panel">
              <div className="dashboard-panel__heading">
                <h2>Recent Activity</h2>
                <button type="button">View all</button>
              </div>

              <div className="activity-list">
                {recentActivity.length > 0 ? (
                  recentActivity.map((item) => (
                    <article key={`${item.title}-${item.time}`} className="activity-item">
                      <div className="activity-item__icon">
                        <DashboardIcon type={item.icon} />
                      </div>
                      <div className="activity-item__content">
                        <h3>{item.title}</h3>
                        <p>{item.detail}</p>
                      </div>
                      <span className="activity-item__time">{item.time}</span>
                    </article>
                  ))
                ) : (
                  <div className="dashboard-empty-state dashboard-empty-state--compact">
                    Recent assistant activity will appear here once you create one.
                  </div>
                )}
              </div>
            </section>
          </aside>
        </section>
      </div>

      <CreateAssistantModal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        onCreated={handleAssistantCreated}
      />
      <DeleteAssistantModal
        assistant={assistantPendingDelete}
        isDeleting={deletingAssistantId === assistantPendingDelete?.id}
        onCancel={() => {
          if (!deletingAssistantId) {
            setAssistantPendingDelete(null)
          }
        }}
        onConfirm={handleAssistantDelete}
      />
    </main>
  )
}

export default Dashboard
