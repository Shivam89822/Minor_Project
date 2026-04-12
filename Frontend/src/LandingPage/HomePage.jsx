import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Navbar from './Navbar'
import Footer from './Footer'
import AuthModal from '../components/AuthModal'

const API_BASE_URL = 'http://127.0.0.1:8000'

const authCopy = {
  login: {
    title: 'Welcome back',
    subtitle: 'Sign in to continue building assistants from your files.',
    submitLabel: 'Login',
    switchLabel: "Don't have an account?",
    switchAction: 'Create one',
  },
  signup: {
    title: 'Create your account',
    subtitle: 'Start your workspace and unlock your assistant dashboard.',
    submitLabel: 'Sign Up',
    switchLabel: 'Already registered?',
    switchAction: 'Login instead',
  },
}

export default function HomePage() {
  const navigate = useNavigate()
  const [authMode, setAuthMode] = useState(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')

  const features = [
    {
      title: 'Create AI assistants',
      description:
        'Spin up focused assistants for support, onboarding, research, and internal knowledge workflows.',
    },
    {
      title: 'Upload documents/videos',
      description:
        'Bring in PDFs, notes, recordings, and video content so your assistant can learn from real material.',
    },
    {
      title: 'Chat with your knowledge base',
      description:
        'Ask questions in natural language and get grounded answers from the content you already trust.',
    },
  ]

  const closeAuth = () => {
    setAuthMode(null)
    setErrorMessage('')
    setIsSubmitting(false)
  }

  const openAuth = (mode) => {
    setAuthMode(mode)
    setErrorMessage('')
    setIsSubmitting(false)
  }

  const handleAuthSubmit = async ({ username, email, password }) => {
    setIsSubmitting(true)
    setErrorMessage('')

    try {
      if (authMode === 'signup') {
        const registerResponse = await fetch(`${API_BASE_URL}/register`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ username, email, password }),
        })

        const registerData = await registerResponse.json()

        if (!registerResponse.ok) {
          throw new Error(registerData.detail || registerData.message || 'Unable to sign up')
        }
      }

      const loginBody = new URLSearchParams({
        username: email,
        password,
      })

      const loginResponse = await fetch(`${API_BASE_URL}/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: loginBody.toString(),
      })

      const loginData = await loginResponse.json()

      if (!loginResponse.ok) {
        throw new Error(loginData.detail || 'Unable to login')
      }

      const resolvedUsername = loginData.user?.username || username || email.split('@')[0]
      localStorage.setItem('token', loginData.access_token)
      localStorage.setItem('userEmail', loginData.user?.email || email)
      localStorage.setItem('userName', resolvedUsername)
      closeAuth()
      navigate('/dashboard')
    } catch (error) {
      const message =
        error instanceof TypeError
          ? 'Cannot reach the backend server on http://127.0.0.1:8000. Start the FastAPI backend and try again.'
          : error.message || 'Something went wrong'

      setErrorMessage(message)
      setIsSubmitting(false)
    }
  }

  return (
    <div className="app-shell">
      <Navbar onOpenAuth={openAuth} />

      <main className="hero-panel">
        <span className="hero-panel__badge">Knowledge-powered AI</span>
        <h1>Build assistants that understand your content.</h1>
        <p>
          Turn your documents and videos into a searchable, conversational
          workspace with fast answers and assistant-driven support.
        </p>

        <section className="feature-grid" aria-label="Platform features">
          {features.map((feature, index) => (
            <article className="feature-card" key={feature.title}>
              <span className="feature-card__number">0{index + 1}</span>
              <h2>{feature.title}</h2>
              <p>{feature.description}</p>
            </article>
          ))}
        </section>

        <section className="preview-panel" aria-label="Dashboard preview">
          <div className="preview-panel__header">
            <div>
              <span className="preview-panel__eyebrow">Product Preview</span>
              <h2>See how your assistant looks in action.</h2>
            </div>
            <span className="preview-panel__status">Live knowledge chat</span>
          </div>

          <div className="preview-window">
            <aside className="preview-sidebar">
              <h3>Dashboard</h3>
              <span>AI Chat</span>
              <span>Documents</span>
              <span>Analytics</span>
            </aside>

            <div className="preview-chat">
              <div className="preview-chat__message preview-chat__message--assistant">
                Hello! I have indexed your uploaded files. What would you like
                to know?
              </div>
              <div className="preview-chat__message preview-chat__message--user">
                Summarize the uploaded project report and highlight action
                items.
              </div>
              <div className="preview-chat__message preview-chat__message--assistant">
                I found 3 key action items, 2 pending risks, and a strong
                recommendation to automate document ingestion.
              </div>
            </div>
          </div>
        </section>
      </main>

      <Footer />

      <AuthModal
        isOpen={Boolean(authMode)}
        mode={authMode ?? 'login'}
        copy={authCopy[authMode ?? 'login']}
        isSubmitting={isSubmitting}
        errorMessage={errorMessage}
        onClose={closeAuth}
        onModeChange={openAuth}
        onSubmit={handleAuthSubmit}
      />
    </div>
  )
}
