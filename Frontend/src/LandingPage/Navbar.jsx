function Navbar() {
  return (
    <header className="navbar">
      <div className="navbar__brand">
        <div className="navbar__logo" aria-hidden="true">
          R
        </div>
        <div>
          <span className="navbar__title">RAG Assistant</span>
          <p className="navbar__subtitle">Create your own AI assistants from your documents and videos</p>
        </div>
      </div>

      <nav className="navbar__links" aria-label="Primary navigation">
        <button type="button" className="navbar__link navbar__link--active">
          Home
        </button>

        <button type="button" className="navbar__link">
          About
        </button>

        <button type="button" className="navbar__link">
          Contacts
        </button>
      </nav>

      <div className="navbar__actions">
        <button type="button" className="navbar__action navbar__action--secondary">
          Sign Up
        </button>
        <button type="button" className="navbar__action navbar__action--primary">
          Login
        </button>
      </div>
    </header>
  )
}

export default Navbar
