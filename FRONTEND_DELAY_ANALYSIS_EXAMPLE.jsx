"""
Example frontend implementation for multi-platform delay analysis.
Shows how to integrate the delay analysis API with React frontend.
"""

# This would be in frontend/src/pages/DelayAnalysisPage.jsx

import React, { useState } from 'react';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1/delay-analysis';

export const DelayAnalysisPage = () => {
  const [platform, setPlatform] = useState('github'); // 'github' or 'jira'
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState(null);
  const [chatHistory, setChatHistory] = useState([]);
  const [chatInput, setChatInput] = useState('');

  // GitHub credentials
  const [githubOwner, setGithubOwner] = useState('');
  const [githubRepo, setGithubRepo] = useState('');
  const [githubPAT, setGithubPAT] = useState('');

  // JIRA credentials
  const [jiraProjectKey, setJiraProjectKey] = useState('');
  const [jiraDomain, setJiraDomain] = useState('');
  const [jiraAPIToken, setJiraAPIToken] = useState('');
  const [jiraEmail, setJiraEmail] = useState('');

  const handleAnalyze = async () => {
    setLoading(true);
    try {
      const credentials =
        platform === 'github'
          ? {
              platform: 'github',
              owner: githubOwner,
              repo: githubRepo,
              github_pat: githubPAT,
            }
          : {
              platform: 'jira',
              project_key: jiraProjectKey,
              jira_domain: jiraDomain,
              jira_api_token: jiraAPIToken,
              jira_email: jiraEmail,
            };

      const response = await axios.post(`${API_BASE_URL}/analyze`, {
        credentials,
        srs_features: [], // Could load from file
      });

      setAnalysis(response.data);
      setChatHistory([]);
    } catch (error) {
      alert(`Analysis failed: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleChat = async () => {
    if (!chatInput.trim() || !analysis) return;

    const userMessage = chatInput;
    setChatInput('');

    // Add user message to history
    setChatHistory([
      ...chatHistory,
      { role: 'user', message: userMessage },
    ]);

    try {
      const response = await axios.post(`${API_BASE_URL}/chat`, {
        question: userMessage,
        project_key: analysis.project_key,
        platform: analysis.platform,
      });

      setChatHistory((prev) => [
        ...prev,
        { role: 'assistant', message: response.data.answer },
      ]);
    } catch (error) {
      setChatHistory((prev) => [
        ...prev,
        {
          role: 'assistant',
          message: `Error: ${error.response?.data?.detail || error.message}`,
        },
      ]);
    }
  };

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '20px' }}>
      <h1>🔍 Project Delay Analysis</h1>

      {!analysis ? (
        // STEP 1: CHOOSE PLATFORM & ENTER CREDENTIALS
        <div>
          <h2>Step 1: Choose Platform</h2>
          <div style={{ marginBottom: '20px' }}>
            <label>
              <input
                type="radio"
                value="github"
                checked={platform === 'github'}
                onChange={(e) => setPlatform(e.target.value)}
              />
              {' '}GitHub Repository
            </label>
            <label style={{ marginLeft: '20px' }}>
              <input
                type="radio"
                value="jira"
                checked={platform === 'jira'}
                onChange={(e) => setPlatform(e.target.value)}
              />
              {' '}JIRA Project
            </label>
          </div>

          <h2>Step 2: Enter Credentials</h2>

          {platform === 'github' ? (
            <div style={{ border: '1px solid #ccc', padding: '15px' }}>
              <div style={{ marginBottom: '10px' }}>
                <label>
                  Repository Owner:
                  <input
                    type="text"
                    value={githubOwner}
                    onChange={(e) => setGithubOwner(e.target.value)}
                    placeholder="e.g., facebook"
                    style={{ marginLeft: '10px', width: '300px' }}
                  />
                </label>
              </div>
              <div style={{ marginBottom: '10px' }}>
                <label>
                  Repository Name:
                  <input
                    type="text"
                    value={githubRepo}
                    onChange={(e) => setGithubRepo(e.target.value)}
                    placeholder="e.g., react"
                    style={{ marginLeft: '10px', width: '300px' }}
                  />
                </label>
              </div>
              <div style={{ marginBottom: '10px' }}>
                <label>
                  GitHub Personal Access Token:
                  <input
                    type="password"
                    value={githubPAT}
                    onChange={(e) => setGithubPAT(e.target.value)}
                    placeholder="ghp_..."
                    style={{ marginLeft: '10px', width: '300px' }}
                  />
                </label>
              </div>
            </div>
          ) : (
            <div style={{ border: '1px solid #ccc', padding: '15px' }}>
              <div style={{ marginBottom: '10px' }}>
                <label>
                  Project Key:
                  <input
                    type="text"
                    value={jiraProjectKey}
                    onChange={(e) => setJiraProjectKey(e.target.value)}
                    placeholder="e.g., PROJ"
                    style={{ marginLeft: '10px', width: '300px' }}
                  />
                </label>
              </div>
              <div style={{ marginBottom: '10px' }}>
                <label>
                  JIRA Domain:
                  <input
                    type="text"
                    value={jiraDomain}
                    onChange={(e) => setJiraDomain(e.target.value)}
                    placeholder="company.atlassian.net"
                    style={{ marginLeft: '10px', width: '300px' }}
                  />
                </label>
              </div>
              <div style={{ marginBottom: '10px' }}>
                <label>
                  API Token:
                  <input
                    type="password"
                    value={jiraAPIToken}
                    onChange={(e) => setJiraAPIToken(e.target.value)}
                    placeholder="your-api-token"
                    style={{ marginLeft: '10px', width: '300px' }}
                  />
                </label>
              </div>
              <div style={{ marginBottom: '10px' }}>
                <label>
                  Email:
                  <input
                    type="email"
                    value={jiraEmail}
                    onChange={(e) => setJiraEmail(e.target.value)}
                    placeholder="user@company.com"
                    style={{ marginLeft: '10px', width: '300px' }}
                  />
                </label>
              </div>
            </div>
          )}

          <button
            onClick={handleAnalyze}
            disabled={loading}
            style={{
              marginTop: '20px',
              padding: '10px 20px',
              fontSize: '16px',
              cursor: loading ? 'not-allowed' : 'pointer',
            }}
          >
            {loading ? 'Analyzing...' : 'Analyze Delays'}
          </button>
        </div>
      ) : (
        // STEP 2: VIEW ANALYSIS & CHAT
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <h2>Analysis Results</h2>
            <button onClick={() => setAnalysis(null)}>← Back</button>
          </div>

          {/* SEVERITY SCORE */}
          <div
            style={{
              backgroundColor: '#f0f0f0',
              padding: '15px',
              borderRadius: '5px',
              marginBottom: '20px',
            }}
          >
            <h3>Project Health</h3>
            <div>
              <strong>Severity Score:</strong>{' '}
              <span
                style={{
                  fontSize: '24px',
                  color: analysis.severity_score > 0.7 ? 'red' : 'orange',
                }}
              >
                {(analysis.severity_score * 100).toFixed(0)}%
              </span>
            </div>
            <div style={{ marginTop: '10px' }}>
              <strong>Primary Causes:</strong>
              <ul>
                {analysis.primary_causes.map((cause) => (
                  <li key={cause}>{cause.replace(/_/g, ' ').toUpperCase()}</li>
                ))}
              </ul>
            </div>
          </div>

          {/* FEATURE BREAKDOWN */}
          <div
            style={{
              backgroundColor: '#f9f9f9',
              padding: '15px',
              borderRadius: '5px',
              marginBottom: '20px',
            }}
          >
            <h3>Feature Status Breakdown</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
              <div>
                <strong>Total Features:</strong> {analysis.total_features}
              </div>
              <div>
                <strong>Completed:</strong> {analysis.completed_features}
              </div>
              <div>
                <strong>In Progress:</strong> {analysis.in_progress_features}
              </div>
              <div>
                <strong>Blocked:</strong> {analysis.blocked_features}
              </div>
              <div>
                <strong>Unassigned:</strong> {analysis.unassigned_features}
              </div>
            </div>
          </div>

          {/* FAQs */}
          <div
            style={{
              backgroundColor: '#fffbf0',
              padding: '15px',
              borderRadius: '5px',
              marginBottom: '20px',
            }}
          >
            <h3>Frequently Asked Questions (Auto-Generated)</h3>
            {analysis.faqs.map((faq, index) => (
              <div
                key={index}
                style={{
                  marginBottom: '20px',
                  borderLeft: '4px solid #ff9800',
                  paddingLeft: '15px',
                }}
              >
                <h4 style={{ margin: '0 0 10px 0' }}>
                  Q{index + 1}: {faq.question}
                </h4>
                <p style={{ whiteSpace: 'pre-wrap', color: '#555' }}>
                  {faq.answer}
                </p>
                <small style={{ color: '#999' }}>
                  Category: {faq.category} | Relevance:{' '}
                  {(faq.relevance_score * 100).toFixed(0)}%
                </small>
              </div>
            ))}
          </div>

          {/* CHATBOT */}
          <div
            style={{
              border: '1px solid #ddd',
              borderRadius: '5px',
              padding: '15px',
            }}
          >
            <h3>💬 Ask AI About This Project</h3>
            <div
              style={{
                height: '300px',
                overflowY: 'auto',
                backgroundColor: '#f5f5f5',
                padding: '10px',
                borderRadius: '3px',
                marginBottom: '10px',
              }}
            >
              {chatHistory.map((msg, idx) => (
                <div
                  key={idx}
                  style={{
                    marginBottom: '10px',
                    textAlign: msg.role === 'user' ? 'right' : 'left',
                  }}
                >
                  <div
                    style={{
                      display: 'inline-block',
                      backgroundColor: msg.role === 'user' ? '#007bff' : '#e8e8e8',
                      color: msg.role === 'user' ? 'white' : 'black',
                      padding: '10px',
                      borderRadius: '5px',
                      maxWidth: '70%',
                      wordWrap: 'break-word',
                      whiteSpace: 'pre-wrap',
                    }}
                  >
                    {msg.message}
                  </div>
                </div>
              ))}
            </div>
            <div style={{ display: 'flex', gap: '10px' }}>
              <input
                type="text"
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleChat()}
                placeholder="Ask about delays, developers, features..."
                style={{
                  flex: 1,
                  padding: '10px',
                  border: '1px solid #ddd',
                  borderRadius: '3px',
                }}
              />
              <button
                onClick={handleChat}
                disabled={!chatInput.trim()}
                style={{
                  padding: '10px 20px',
                  cursor: chatInput.trim() ? 'pointer' : 'not-allowed',
                }}
              >
                Send
              </button>
            </div>
            <small style={{ color: '#999', marginTop: '10px', display: 'block' }}>
              Try: "Who caused the delay?", "Which features are blocked?",
              "Which developer started feature X?"
            </small>
          </div>
        </div>
      )}
    </div>
  );
};

export default DelayAnalysisPage;
