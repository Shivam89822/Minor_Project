import { useEffect, useState } from 'react'

const initialFormState = {
  email: '',
  password: '',
}

function AuthModal({
  isOpen,
  mode,
  copy,
  isSubmitting,
  errorMessage,
  onClose,
  onModeChange,
  onSubmit,
}) {
  const [formData, setFormData] = useState(initialFormState)

  useEffect(() => {
    if (isOpen) {
      setFormData(initialFormState)
    }
  }, [isOpen, mode])

  useEffect(() => {
    if (!isOpen) {
      return undefined
    }

    const handleEscape = (event) => {
      if (event.key === 'Escape') {
        onClose()
      }
    }

    window.addEventListener('keydown', handleEscape)
    return () => window.removeEventListener('keydown', handleEscape)
  }, [isOpen, onClose])

  if (!isOpen) {
    return null
  }

  const handleChange = (event) => {
    const { name, value } = event.target
    setFormData((current) => ({
      ...current,
      [name]: value,
    }))
  }

  const handleSubmit = (event) => {
    event.preventDefault()
    onSubmit(formData)
  }

  return (
    <div className="auth-modal-overlay" onClick={onClose} role="presentation">
      <section
        className="auth-modal"
        onClick={(event) => event.stopPropagation()}
        aria-modal="true"
        role="dialog"
        aria-labelledby="auth-modal-title"
      >
        <button type="button" className="auth-modal__close" onClick={onClose} aria-label="Close">
          x
        </button>

        <div className="auth-modal__glow" aria-hidden="true" />

        <span className="auth-modal__badge">
          {mode === 'login' ? 'Secure login' : 'Quick signup'}
        </span>
        <h2 id="auth-modal-title">{copy.title}</h2>
        <p className="auth-modal__subtitle">{copy.subtitle}</p>

        <form className="auth-form" onSubmit={handleSubmit}>
          <label className="auth-form__field">
            <span>Email</span>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              placeholder="you@example.com"
              autoComplete="email"
              required
            />
          </label>

          <label className="auth-form__field">
            <span>Password</span>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              placeholder="Enter your password"
              autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
              required
            />
          </label>

          {errorMessage ? <p className="auth-form__error">{errorMessage}</p> : null}

          <button type="submit" className="auth-form__submit" disabled={isSubmitting}>
            {isSubmitting ? 'Please wait...' : copy.submitLabel}
          </button>
        </form>

        <p className="auth-modal__switch">
          {copy.switchLabel}{' '}
          <button
            type="button"
            className="auth-modal__switch-button"
            onClick={() => onModeChange(mode === 'login' ? 'signup' : 'login')}
          >
            {copy.switchAction}
          </button>
        </p>
      </section>
    </div>
  )
}

export default AuthModal
