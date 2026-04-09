import Navbar from './Navbar';
import Footer from './Footer';

export default function HomePage() {
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

  return (
    <div className="app-shell">
      <Navbar />

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
    </div>
  )
}
