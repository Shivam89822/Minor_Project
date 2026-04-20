import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

const API_BASE_URL = 'http://127.0.0.1:8000'

function ChatIcon({ type }) {
  const icons = {
    assistant: (
      <path d="M8 9.5h8M10 6.5h4M9 13.5h6M9.5 4h5a2.5 2.5 0 0 1 2.5 2.5V14A2 2 0 0 1 15 16H9a2 2 0 0 1-2-2V6.5A2.5 2.5 0 0 1 9.5 4ZM5.5 8.5h1v4h-1m11 0h1v-4h-1" />
    ),
    upload: <path d="M12 15V7m0 0-3 3m3-3 3 3M7 15.5v1A1.5 1.5 0 0 0 8.5 18h7a1.5 1.5 0 0 0 1.5-1.5v-1" />,
    send: <path d="m5 12 14-7-3 14-4.5-4.5L5 12Z" />,
    document: (
      <path d="M8.5 4.5h5l3 3V15a2 2 0 0 1-2 2h-6a2 2 0 0 1-2-2V6.5a2 2 0 0 1 2-2Zm5 0V8h3M9.5 11h5M9.5 14h5" />
    ),
    clock: <path d="M12 7.5v4l2.5 1.5M19 12a7 7 0 1 1-14 0 7 7 0 0 1 14 0Z" />,
    back: <path d="m15 18-6-6 6-6M9 12h10" />,
  }

  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" className="dashboard-icon">
      {icons[type]}
    </svg>
  )
}

function formatCitation(match) {
  const pieces = [match.source]
  if (match.page) {
    pieces.push(`Page ${match.page}`)
  }
  if (match.start !== null && match.start !== undefined) {
    const start = Number(match.start)
    const end = Number(match.end ?? match.start)
    const formatSeconds = (value) => {
      const total = Math.max(0, Math.floor(value))
      const minutes = Math.floor(total / 60)
      const seconds = total % 60
      return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
    }
    pieces.push(`${formatSeconds(start)} - ${formatSeconds(end)}`)
  }
  return pieces.join(' | ')
}

function ChatLoader() {
  return <span className="chat-loader" aria-hidden="true" />
}

function UploadMoreModal({ isOpen, onClose, assistantId, onUploaded }) {
  const [files, setFiles] = useState([])
  const [errorMessage, setErrorMessage] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    if (!isOpen) {
      setFiles([])
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

    if (files.length === 0) {
      setErrorMessage('Please choose at least one PDF or video file.')
      return
    }

    const token = localStorage.getItem('token')
    const formData = new FormData()
    files.forEach((file) => formData.append('files', file))

    try {
      setIsSubmitting(true)
      const response = await fetch(`${API_BASE_URL}/assistants/${assistantId}/files`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      })

      const data = await response.json()
      if (!response.ok) {
        throw new Error(data.detail || 'Unable to upload more files.')
      }

      onUploaded(data.assistant)
      onClose()
    } catch (error) {
      setErrorMessage(error.message || 'Unable to upload more files.')
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
      >
        <button type="button" className="auth-modal__close" onClick={onClose} aria-label="Close">
          x
        </button>
        <div className="auth-modal__glow" aria-hidden="true" />
        <span className="auth-modal__badge">Upload more</span>
        <h2>Add more knowledge files</h2>
        <p className="auth-modal__subtitle">
          These files will be embedded and merged into this assistant&apos;s current knowledge base.
        </p>

        <form className="auth-form" onSubmit={handleSubmit}>
          <label className="auth-form__field">
            <span>Files</span>
            <input
              type="file"
              accept=".pdf,.docx,video/*"
              multiple
              onChange={(event) => setFiles(Array.from(event.target.files || []))}
              required
            />
          </label>

          {files.length > 0 ? (
            <div className="dashboard-file-list">
              {files.map((file) => (
                <span key={`${file.name}-${file.lastModified}`} className="dashboard-file-pill">
                  {file.name}
                </span>
              ))}
            </div>
          ) : null}

          {errorMessage ? <p className="auth-form__error">{errorMessage}</p> : null}

          <button type="submit" className="auth-form__submit" disabled={isSubmitting}>
            {isSubmitting ? 'Uploading...' : 'Upload and Merge'}
          </button>
        </form>
      </section>
    </div>
  )
}

function AssistantChatPage() {
  const { assistantId } = useParams()
  const navigate = useNavigate()
  const [assistant, setAssistant] = useState(null)
  const [messages, setMessages] = useState([])
  const [question, setQuestion] = useState('')
  const [isSending, setIsSending] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [errorMessage, setErrorMessage] = useState('')
  const [isUploadOpen, setIsUploadOpen] = useState(false)
  const chatEndRef = useRef(null)

  const token = localStorage.getItem('token')

  const handleUnauthorized = (message = 'Session expired. Please login again.') => {
    localStorage.removeItem('token')
    localStorage.removeItem('userEmail')
    localStorage.removeItem('userName')
    setErrorMessage(message)
    navigate('/')
  }

  const loadAssistant = useCallback(async ({ silent = false } = {}) => {
    if (!token) {
      setErrorMessage('Missing login token. Please login again.')
      setIsLoading(false)
      return
    }

    try {
      if (!silent) {
        setIsLoading(true)
      }

      const response = await fetch(`${API_BASE_URL}/assistants/${assistantId}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })

      const data = await response.json()
      if (!response.ok) {
        if (response.status === 401) {
          handleUnauthorized('Session expired. Please login again.')
          return
        }
        throw new Error(data.detail || 'Unable to load assistant.')
      }

      setAssistant(data.assistant)
      setMessages(data.messages || [])
      setErrorMessage('')
    } catch (error) {
      setErrorMessage(error.message || 'Unable to load assistant.')
    } finally {
      if (!silent) {
        setIsLoading(false)
      }
    }
  }, [assistantId, token])

  useEffect(() => {
    loadAssistant()
  }, [loadAssistant])

  useEffect(() => {
    if (assistant?.status !== 'training') {
      return undefined
    }

    const intervalId = window.setInterval(() => {
      loadAssistant({ silent: true })
    }, 4000)

    return () => window.clearInterval(intervalId)
  }, [assistant?.status, loadAssistant])

  useEffect(() => {
    if (!chatEndRef.current) {
      return
    }

    const scrollToLatestChat = () => {
      chatEndRef.current?.scrollIntoView({
        behavior: 'smooth',
        block: 'end',
      })
      window.scrollTo({
        top: document.documentElement.scrollHeight,
        behavior: 'smooth',
      })
    }

    const frameId = window.requestAnimationFrame(scrollToLatestChat)
    const timeoutId = window.setTimeout(scrollToLatestChat, 120)

    return () => {
      window.cancelAnimationFrame(frameId)
      window.clearTimeout(timeoutId)
    }
  }, [messages, isSending])

  const chatDisabledReason = useMemo(() => {
    if (!assistant) {
      return 'Loading assistant...'
    }
    if (assistant.status === 'training') {
      return 'Embeddings are still being prepared. Please wait a little.'
    }
    if (assistant.status === 'failed') {
      return assistant.last_error || 'Assistant indexing failed. Upload more files to retry.'
    }
    return ''
  }, [assistant])

  const uploadedFiles = useMemo(() => {
    const fromAssistantItems = Array.isArray(assistant?.source_file_items)
      ? assistant.source_file_items
          .map((item) => ({
            name: typeof item?.name === 'string' ? item.name.trim() : '',
            url: typeof item?.url === 'string' ? item.url.trim() : '',
          }))
          .filter((item) => item.name)
      : []

    if (fromAssistantItems.length > 0) {
      return fromAssistantItems
    }

    const fromAssistantNames = Array.isArray(assistant?.source_files)
      ? assistant.source_files
          .filter((fileName) => typeof fileName === 'string' && fileName.trim())
          .map((name) => ({ name: name.trim(), url: '' }))
      : []

    if (fromAssistantNames.length > 0) {
      return fromAssistantNames
    }

    const fallbackFromMessages = []
    const seen = new Set()
    for (const message of messages) {
      const matches = Array.isArray(message?.matches) ? message.matches : []
      for (const match of matches) {
        const source = typeof match?.source === 'string' ? match.source.trim() : ''
        if (!source) {
          continue
        }
        const key = source.toLowerCase()
        if (seen.has(key)) {
          continue
        }
        seen.add(key)
        fallbackFromMessages.push({ name: source, url: '' })
      }
    }

    return fallbackFromMessages
  }, [assistant, messages])

  const handleSend = async (event) => {
    event.preventDefault()
    const trimmedQuestion = question.trim()
    if (!trimmedQuestion || !assistant || assistant.status !== 'active') {
      return
    }

    const userMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      text: trimmedQuestion,
    }

    setMessages((current) => [...current, userMessage])
    setQuestion('')
    setIsSending(true)

    try {
      const response = await fetch(`${API_BASE_URL}/assistants/${assistantId}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          question: trimmedQuestion,
          top_k: 4,
        }),
      })

      const data = await response.json()
      if (!response.ok) {
        if (response.status === 401) {
          handleUnauthorized('Session expired. Please login again.')
          return
        }
        throw new Error(data.detail || 'Unable to query assistant.')
      }

      setMessages((current) => [
        ...current,
        {
          id: `assistant-${Date.now()}`,
          role: 'assistant',
          text: data.answer,
          matches: data.matches || [],
        },
      ])
    } catch (error) {
      setMessages((current) => [
        ...current,
        {
          id: `assistant-error-${Date.now()}`,
          role: 'assistant',
          text: error.message || 'Unable to query assistant.',
          matches: [],
        },
      ])
    } finally {
      setIsSending(false)
    }
  }

  const handleComposerKeyDown = (event) => {
    if (event.key !== 'Enter' || event.shiftKey) {
      return
    }

    event.preventDefault()
    if (isSending || chatDisabledReason) {
      return
    }

    handleSend(event)
  }

  return (
    <main className="chat-shell">
      <div className="chat-layout">
        <header className="chat-topbar">
          <div className="chat-topbar__left">
            <button type="button" className="chat-topbar__back" onClick={() => navigate('/dashboard')}>
              <ChatIcon type="back" />
              <span>Back to dashboard</span>
            </button>
            <div className="chat-topbar__title">
              <span className="chat-topbar__eyebrow">Assistant Chat</span>
              <h1>{assistant?.name || 'Loading assistant...'}</h1>
            </div>
          </div>

          <div className="chat-topbar__actions">
            <button type="button" className="dashboard-button dashboard-button--primary" onClick={() => setIsUploadOpen(true)}>
              <ChatIcon type="upload" />
              <span>Upload More</span>
            </button>
          </div>
        </header>

        <section className="chat-header-card">
          <div>
            <span className={`assistant-status assistant-status--${assistant?.status || 'training'}`}>
              <i />
              {assistant?.status === 'active'
                ? 'Active'
                : assistant?.status === 'failed'
                  ? 'Failed'
                  : 'Training'}
            </span>
            <h2>Ask questions grounded in your uploaded files</h2>
            <p>
              Every answer is built from the most relevant vector matches in this assistant&apos;s
              knowledge base, along with source references like page numbers or timestamps.
            </p>
          </div>

          <div className="chat-header-card__stats">
            <article className="chat-mini-card">
              <ChatIcon type="document" />
              <div>
                <strong>{assistant?.source_count ?? 0}</strong>
                <span>Sources</span>
              </div>
            </article>
            <article className="chat-mini-card">
              <ChatIcon type="clock" />
              <div>
                <strong>{assistant?.updated_at ? new Date(assistant.updated_at).toLocaleDateString('en-IN') : '--'}</strong>
                <span>Last Updated</span>
              </div>
            </article>
          </div>
        </section>

        <section className="chat-main">
          <div className="chat-thread">
            {isLoading ? <div className="dashboard-empty-state">Loading assistant chat...</div> : null}
            {!isLoading && errorMessage ? (
              <div className="dashboard-empty-state dashboard-empty-state--error">{errorMessage}</div>
            ) : null}
            {!isLoading && !errorMessage && messages.length === 0 ? (
              <div className="dashboard-empty-state">
                <div className="assistant-card__create-icon">
                  <ChatIcon type="assistant" />
                </div>
                <h3>Start the conversation</h3>
                <p>Ask about your uploaded PDFs or videos to see the most relevant retrieved context.</p>
              </div>
            ) : null}

            {messages.map((message) => (
              <article key={message.id} className={`chat-message chat-message--${message.role}`}>
                <div className="chat-message__bubble">
                  <p>{message.text}</p>
                </div>

                {message.role === 'assistant' && message.matches?.length ? (
                  <div className="chat-sources">
                    <h3>Sources used</h3>
                    <div className="chat-sources__list">
                      {message.matches.map((match) => (
                        <article key={match.id} className="chat-source-card">
                          <div className="chat-source-card__header">
                            <strong>{formatCitation(match)}</strong>
                          </div>
                          <p>{match.text}</p>
                        </article>
                      ))}
                    </div>
                  </div>
                ) : null}
              </article>
            ))}

            {isSending ? (
              <article className="chat-message chat-message--assistant chat-message--pending" aria-live="polite">
                <div className="chat-message__bubble chat-message__bubble--loading">
                  <ChatLoader />
                  <p>Searching your knowledge base...</p>
                </div>
              </article>
            ) : null}

            {chatDisabledReason ? (
              <div className="chat-status-note">{chatDisabledReason}</div>
            ) : null}

            <div ref={chatEndRef} className="chat-thread__end" aria-hidden="true" />
          </div>

          <aside className="chat-sidebar">
            <section className="dashboard-panel">
              <div className="dashboard-panel__heading">
                <h2>How This Chat Works</h2>
              </div>
              <div className="chat-guide">
                <p>Your question is embedded and matched against this assistant&apos;s stored chunks.</p>
                <p>The response returns the most relevant text from your sources, plus citations.</p>
                <p>Use Upload More any time to merge new files into this assistant.</p>
              </div>
            </section>

            <section className="dashboard-panel">
              <div className="dashboard-panel__heading">
                <h2>Suggested Questions</h2>
              </div>
              <div className="chat-suggestions">
                <button type="button" onClick={() => setQuestion('Summarize the most important parts of the uploaded content.')}>
                  Summarize the uploaded content
                </button>
                <button type="button" onClick={() => setQuestion('Which part of the source best answers my question?')}>
                  Show the most relevant source
                </button>
                <button type="button" onClick={() => setQuestion('List key points with source references.')}>
                  List key points with citations
                </button>
              </div>
            </section>

            <section className="dashboard-panel">
              <div className="dashboard-panel__heading">
                <h2>Uploaded Files</h2>
              </div>
              {uploadedFiles.length > 0 ? (
                <div className="chat-uploaded-files">
                  {uploadedFiles.map((file) => (
                    file.url ? (
                      <a
                        key={`${file.name}-${file.url}`}
                        className="chat-uploaded-files__item chat-uploaded-files__item--link"
                        title={file.name}
                        href={file.url}
                        target="_blank"
                        rel="noreferrer"
                      >
                        {file.name}
                      </a>
                    ) : (
                      <span key={file.name} className="chat-uploaded-files__item" title={file.name}>
                        {file.name}
                      </span>
                    )
                  ))}
                </div>
              ) : (
                <p className="chat-uploaded-files__empty">
                  No file names are available for this assistant yet.
                </p>
              )}
            </section>
          </aside>
        </section>

        <form className="chat-composer" onSubmit={handleSend}>
          <textarea
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            onKeyDown={handleComposerKeyDown}
            placeholder="Ask about your documents or videos..."
            rows={3}
            disabled={isSending || Boolean(chatDisabledReason)}
          />
          <div className="chat-composer__actions">
            <Link to="/dashboard" className="chat-composer__secondary">
              Dashboard
            </Link>
            <button type="submit" className="dashboard-button dashboard-button--primary" disabled={isSending || Boolean(chatDisabledReason)}>
              {isSending ? <ChatLoader /> : <ChatIcon type="send" />}
              <span>{isSending ? 'Searching...' : 'Ask Assistant'}</span>
            </button>
          </div>
        </form>
      </div>

      <UploadMoreModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        assistantId={assistantId}
        onUploaded={(nextAssistant) => setAssistant(nextAssistant)}
      />
    </main>
  )
}

export default AssistantChatPage
