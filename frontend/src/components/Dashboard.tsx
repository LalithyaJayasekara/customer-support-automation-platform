import React, { useState } from 'react';
import axios from 'axios';
import '../styles/Dashboard.css';

interface DashboardProps {
  user: any;
  onLogout: () => void;
}

interface TicketResult {
  ticket_id: string;
  category: string;
  urgency: string;
  status: string;
  assigned_team: string;
  draft_reply: string;
  qa_status: string;
}

const Dashboard: React.FC<DashboardProps> = ({ user, onLogout }) => {
  const [ticketInput, setTicketInput] = useState('');
  const [results, setResults] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const tickets = ticketInput
        .split('\n')
        .filter(t => t.trim())
        .map((text, idx) => ({
          ticket_id: `M${idx + 1}`,
          text: text.trim()
        }));

      const response = await axios.post('/analyze', 
        { tickets },
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        }
      );

      setResults(response.data);
      setTicketInput('');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to analyze messages');
    } finally {
      setLoading(false);
    }
  };

  const getUrgencyColor = (urgency: string) => {
    const colors: Record<string, string> = {
      high: '#e74c3c',
      medium: '#f39c12',
      low: '#27ae60'
    };
    return colors[urgency] || '#95a5a6';
  };

  const getTeamIcon = (team: string) => {
    const icons: Record<string, string> = {
      billing_team: '💳',
      account_team: '👤',
      tech_team: '⚙️',
      support_team: '🙋'
    };
    return icons[team] || '📋';
  };

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div className="header-content">
          <h1>Support Helper</h1>
          <div className="user-section">
            <span className="user-name">👤 {user?.username}</span>
            <button onClick={onLogout} className="logout-btn">Sign Out</button>
          </div>
        </div>
      </header>

      <main className="dashboard-main">
        <div className="container">
          <div className="input-section">
            <h2>Paste your customer messages</h2>
            <p className="section-subtitle">
              Add one message per line. We'll organize, prioritize, and suggest responses.
            </p>

            <form onSubmit={handleAnalyze}>
              <textarea
                value={ticketInput}
                onChange={(e) => setTicketInput(e.target.value)}
                placeholder="e.g., I was charged twice for my subscription&#10;I can't log in after password reset&#10;The app keeps crashing when I export reports"
                rows={6}
                className="input-textarea"
              />

              {error && <div className="error-alert">⚠️ {error}</div>}

              <button 
                type="submit" 
                disabled={loading || !ticketInput.trim()}
                className="analyze-button"
              >
                {loading ? '⏳ Analyzing...' : '✨ Get Suggestions'}
              </button>
            </form>
          </div>

          {results && (
            <div className="results-section">
              <div className="results-header">
                <h2>Here's what we found</h2>
                <div className="metrics">
                  <div className="metric">
                    <span className="metric-label">Messages:</span>
                    <span className="metric-value">{results.metrics.total_tickets}</span>
                  </div>
                  <div className="metric">
                    <span className="metric-label">Urgent:</span>
                    <span className="metric-value" style={{color: '#e74c3c'}}>
                      {results.metrics.high_priority}
                    </span>
                  </div>
                  <div className="metric">
                    <span className="metric-label">Approved:</span>
                    <span className="metric-value" style={{color: '#27ae60'}}>
                      {results.metrics.approved}
                    </span>
                  </div>
                </div>
              </div>

              <div className="results-grid">
                {results.results.map((result: TicketResult, idx: number) => (
                  <div key={idx} className="result-card">
                    <div className="card-header">
                      <span className="ticket-id">Message {idx + 1}</span>
                      <span 
                        className="urgency-badge"
                        style={{backgroundColor: getUrgencyColor(result.urgency)}}
                      >
                        {result.urgency === 'high' ? '🔴' : result.urgency === 'medium' ? '🟡' : '🟢'} 
                        {' '}{result.urgency}
                      </span>
                    </div>

                    <div className="card-body">
                      <div className="info-row">
                        <label>Category:</label>
                        <span className="category-tag">{result.category}</span>
                      </div>

                      <div className="info-row">
                        <label>Send to:</label>
                        <span className="team-tag">
                          {getTeamIcon(result.assigned_team)} {result.assigned_team.replace('_', ' ')}
                        </span>
                      </div>

                      <div className="reply-section">
                        <label>Suggested Response:</label>
                        <p className="draft-reply">{result.draft_reply}</p>
                      </div>

                      <div className="status-row">
                        <span className={`status-badge ${result.qa_status.toLowerCase()}`}>
                          {result.qa_status === 'approved' ? '✅' : '👀'} {result.qa_status}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default Dashboard;
