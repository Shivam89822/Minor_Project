import './App.css'
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom'
import HomePage from './LandingPage/HomePage'
import Dashboard from './Dashboard'
import AssistantChatPage from './AssistantChatPage'

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/assistants/:assistantId" element={<AssistantChatPage />} />
      </Routes>
    </Router>
  )
}

export default App
