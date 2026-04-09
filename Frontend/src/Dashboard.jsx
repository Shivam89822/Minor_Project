const stats = [
  { label: 'Assistants', value: '5', icon: 'assistant' },
  { label: 'Knowledge Sources', value: '93', icon: 'document' },
  { label: 'Conversations', value: '247', icon: 'chat' },
]

const assistants = [
  {
    name: 'Product Docs Bot',
    description: 'Answers questions about product features, pricing, and onboarding guides.',
    sources: '24 sources',
    updated: '2h ago',
    status: 'Training',
    statusTone: 'warning',
  },
  {
    name: 'Legal Assistant',
    description: 'Reviews contracts and answers policy-related queries from uploaded legal docs.',
    sources: '18 sources',
    updated: '1d ago',
    status: 'Draft',
    statusTone: 'draft',
  },
  {
    name: 'HR Policy Bot',
    description: 'Trained on employee handbook and company policies.',
    sources: '12 sources',
    updated: '3h ago',
    status: 'Training',
    statusTone: 'warning',
  },
  {
    name: 'Code Review Helper',
    description: 'Understands your codebase docs and helps with code reviews.',
    sources: '8 sources',
    updated: '5d ago',
    status: 'Draft',
    statusTone: 'draft',
  },
  {
    name: 'Sales Enablement',
    description: 'Assists sales team with product info, case studies, and competitive intel.',
    sources: '31 sources',
    updated: '12h ago',
    status: 'Active',
    statusTone: 'success',
  },
]

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

const recentActivity = [
  {
    title: 'Chat with Product Docs...',
    detail: 'Asked about pricing tiers',
    time: '2 min ago',
    icon: 'chat',
  },
  {
    title: 'Uploaded 3 PDF files',
    detail: 'Added to Legal Assistant knowledge base',
    time: '1 hour ago',
    icon: 'upload',
  },
  {
    title: 'Created HR Policy Bot',
    detail: 'New assistant with 12 documents',
    time: '3 hours ago',
    icon: 'assistant',
  },
  {
    title: 'Chat with Code Review ...',
    detail: 'Reviewed pull request #142',
    time: 'Yesterday',
    icon: 'chat',
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
  }

  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" className="dashboard-icon">
      {icons[type]}
    </svg>
  )
}

function Dashboard() {
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
            <div className="dashboard-search__shortcut">⌘K</div>
          </div>

          <div className="dashboard-topbar__actions">
            <button type="button" className="dashboard-button dashboard-button--primary">
              <DashboardIcon type="plus" />
              <span>New Assistant</span>
            </button>
            <button type="button" className="dashboard-icon-button" aria-label="Notifications">
              <DashboardIcon type="bell" />
              <span className="dashboard-icon-button__dot" />
            </button>
            <button type="button" className="dashboard-profile" aria-label="Profile">
              <span className="dashboard-profile__avatar" />
              <span className="dashboard-profile__caret">⌄</span>
            </button>
          </div>
        </header>

        <section className="dashboard-hero">
          <div className="dashboard-hero__content">
            <h1>
              Welcome back, <span>Creator</span>
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
              <button type="button">View All</button>
            </div>

            <div className="assistant-grid">
              {assistants.map((assistant) => (
                <article key={assistant.name} className="assistant-card">
                  <div className="assistant-card__icon">
                    <DashboardIcon type="assistant" />
                  </div>

                  <h3>{assistant.name}</h3>
                  <p>{assistant.description}</p>

                  <div className="assistant-card__meta">
                    <span>
                      <DashboardIcon type="document" />
                      {assistant.sources}
                    </span>
                    <span>
                      <DashboardIcon type="clock" />
                      {assistant.updated}
                    </span>
                  </div>

                  <div className="assistant-card__footer">
                    <span className={`assistant-status assistant-status--${assistant.statusTone}`}>
                      <i />
                      {assistant.status}
                    </span>
                    <button type="button" className="assistant-card__chat">
                      <DashboardIcon type="chat" />
                      Chat
                    </button>
                  </div>
                </article>
              ))}

              <article className="assistant-card assistant-card--create">
                <div className="assistant-card__create-icon">
                  <DashboardIcon type="plus" />
                </div>
                <h3>Create New Assistant</h3>
                <p>Upload docs &amp; start building</p>
              </article>
            </div>
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
                <button type="button">View all →</button>
              </div>

              <div className="activity-list">
                {recentActivity.map((item) => (
                  <article key={item.title} className="activity-item">
                    <div className="activity-item__icon">
                      <DashboardIcon type={item.icon} />
                    </div>
                    <div className="activity-item__content">
                      <h3>{item.title}</h3>
                      <p>{item.detail}</p>
                    </div>
                    <span className="activity-item__time">{item.time}</span>
                  </article>
                ))}
              </div>
            </section>
          </aside>
        </section>
      </div>
    </main>
  )
}

export default Dashboard
