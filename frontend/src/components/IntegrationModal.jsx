import { useState, useEffect } from "react";
import { X, CheckCircle2, AlertCircle, RefreshCw, Trash2, Plus } from "lucide-react";
import api from "../api/client";

function IntegrationModal({ isOpen, onClose, platformName = "jira", onConnectionChange }) {
  const [activeTab, setActiveTab] = useState(platformName);
  
  // Jira Form State
  const [jiraDomain, setJiraDomain] = useState("");
  const [projectKey, setProjectKey] = useState("");
  const [jiraEmail, setJiraEmail] = useState("");
  const [jiraApiToken, setJiraApiToken] = useState("");
  const [jiraUsername, setJiraUsername] = useState("");

  // GitHub Form State
  const [githubOwner, setGithubOwner] = useState("");
  const [githubRepo, setGithubRepo] = useState("");
  const [githubToken, setGithubToken] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  
  const [connections, setConnections] = useState([]);
  const [showForm, setShowForm] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setActiveTab(platformName);
      fetchConnections();
      setShowForm(false);
    }
  }, [isOpen, platformName]);

  const fetchConnections = async () => {
    try {
      const res = await api.get(`/api/v1/confirm/integrations/connections`);
      setConnections(res.data.connections || []);
    } catch (err) {
      console.error("Failed to fetch connections", err);
    }
  };

  const handleSaveConnection = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      let payload = { platform: activeTab };
      
      if (activeTab === "jira") {
        if (!jiraDomain || !projectKey || !jiraApiToken) {
          throw new Error("Domain, Project Key, and API Token are required for Jira.");
        }
        payload = {
          ...payload,
          jira_domain: jiraDomain,
          project_key: projectKey,
          jira_email: jiraEmail,
          jira_api_token: jiraApiToken,
          jira_username: jiraUsername
        };
      } else if (activeTab === "github") {
        if (!githubOwner || !githubRepo || !githubToken) {
          throw new Error("Owner, Repo, and Token are required for GitHub.");
        }
        payload = {
          ...payload,
          owner: githubOwner,
          repo: githubRepo,
          github_pat: githubToken
        };
      }

      await api.post(`/api/v1/confirm/integrations/connections`, payload);
      
      setSuccess(`${activeTab === "jira" ? "Jira" : "GitHub"} connected successfully!`);
      await fetchConnections();
      if (onConnectionChange) onConnectionChange();
      
      // Auto close after 2s
      setTimeout(() => {
        onClose();
        setSuccess(null);
      }, 2000);
      
    } catch (err) {
      setError(err.response?.data?.detail || err.message || "Failed to save connection.");
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteConnection = async (connId) => {
    try {
      await api.delete(`/api/v1/confirm/integrations/connections/${connId}`);
      await fetchConnections();
    } catch (err) {
      setError("Failed to delete connection.");
    }
  };

  if (!isOpen) return null;

  const activeConnections = connections.filter(c => c.platform === activeTab);
  const isConnected = activeConnections.length > 0 && !showForm;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-ink/40 backdrop-blur-sm" 
        onClick={onClose}
      />
      
      {/* Modal */}
      <div className="relative bg-background border border-hairline rounded-2xl shadow-xl w-full max-w-lg overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-hairline bg-card">
          <h2 className="font-display text-lg text-ink font-semibold">Platform Integrations</h2>
          <button 
            onClick={onClose}
            className="text-subtext hover:text-ink transition rounded-full p-1 hover:bg-secondary"
          >
            <X size={20} />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-hairline bg-card/50">
          <button
            className={`flex-1 py-3 text-sm font-medium transition-colors ${activeTab === "jira" ? "text-primary border-b-2 border-primary bg-primary/5" : "text-subtext hover:text-ink hover:bg-secondary/50"}`}
            onClick={() => setActiveTab("jira")}
          >
            Jira / Atlassian
          </button>
          <button
            className={`flex-1 py-3 text-sm font-medium transition-colors ${activeTab === "github" ? "text-primary border-b-2 border-primary bg-primary/5" : "text-subtext hover:text-ink hover:bg-secondary/50"}`}
            onClick={() => setActiveTab("github")}
          >
            GitHub
          </button>
        </div>

        {/* Content */}
        <div className="p-6 max-h-[70vh] overflow-y-auto">
          
          {error && (
            <div className="mb-6 p-4 bg-error/10 border border-error/20 rounded-xl flex items-start gap-3 text-error">
              <AlertCircle size={18} className="shrink-0 mt-0.5" />
              <div className="text-sm">{error}</div>
            </div>
          )}

          {success && (
            <div className="mb-6 p-4 bg-success/10 border border-success/20 rounded-xl flex items-start gap-3 text-success">
              <CheckCircle2 size={18} className="shrink-0 mt-0.5" />
              <div className="text-sm">{success}</div>
            </div>
          )}

          {isConnected ? (
            <div className="flex flex-col items-center justify-center py-4 text-center">
              <div className="size-16 bg-success/10 rounded-full flex items-center justify-center mb-4">
                <CheckCircle2 className="size-8 text-success" />
              </div>
              <h3 className="text-lg font-medium text-ink mb-2">
                {activeTab === "jira" ? "Jira Projects Connected" : "GitHub Repos Connected"}
              </h3>
              <p className="text-subtext text-sm mb-6 max-w-sm">
                Select from your saved projects when running a new audit.
              </p>
              
              <div className="w-full space-y-3 mb-6">
                {activeConnections.map(conn => (
                  <div key={conn.id} className="bg-card border border-hairline rounded-xl p-4 text-left text-sm flex justify-between items-center group">
                    <div>
                      {activeTab === "jira" && (
                        <>
                          <div className="font-medium text-ink">{conn.credentials.project_key}</div>
                          <div className="text-subtext text-xs">{conn.credentials.jira_domain}</div>
                        </>
                      )}
                      {activeTab === "github" && (
                        <>
                          <div className="font-medium text-ink">{conn.credentials.repo}</div>
                          <div className="text-subtext text-xs">{conn.credentials.owner}</div>
                        </>
                      )}
                    </div>
                    <button 
                      onClick={() => handleDeleteConnection(conn.id)}
                      className="text-error/60 hover:text-error opacity-0 group-hover:opacity-100 transition"
                      title="Delete Connection"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                ))}
              </div>
              
              <button 
                onClick={() => setShowForm(true)}
                className="flex items-center gap-2 text-primary hover:text-primary/80 transition text-sm font-medium"
              >
                <Plus size={16} /> Add Another {activeTab === "jira" ? "Project" : "Repository"}
              </button>
            </div>
          ) : (
            <form onSubmit={handleSaveConnection} className="space-y-4">
              {activeConnections.length > 0 && (
                <button type="button" onClick={() => setShowForm(false)} className="text-sm text-subtext hover:text-ink underline mb-4 block">
                  &larr; Back to saved connections
                </button>
              )}
              {activeTab === "jira" ? (
                <>
                  <div>
                    <label className="block text-xs font-semibold tracking-wider text-subtext uppercase mb-1.5">Jira Domain</label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. example.atlassian.net"
                      value={jiraDomain}
                      onChange={(e) => setJiraDomain(e.target.value)}
                      className="w-full bg-card border border-hairline rounded-xl px-4 py-2.5 text-sm text-ink focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-semibold tracking-wider text-subtext uppercase mb-1.5">Project Key</label>
                      <input
                        type="text"
                        required
                        placeholder="e.g. PROJ"
                        value={projectKey}
                        onChange={(e) => setProjectKey(e.target.value)}
                        className="w-full bg-card border border-hairline rounded-xl px-4 py-2.5 text-sm text-ink focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-semibold tracking-wider text-subtext uppercase mb-1.5">Email</label>
                      <input
                        type="email"
                        placeholder="admin@org.com"
                        value={jiraEmail}
                        onChange={(e) => setJiraEmail(e.target.value)}
                        className="w-full bg-card border border-hairline rounded-xl px-4 py-2.5 text-sm text-ink focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition"
                      />
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-semibold tracking-wider text-subtext uppercase mb-1.5">API Token</label>
                      <input
                        type="password"
                        required
                        value={jiraApiToken}
                        onChange={(e) => setJiraApiToken(e.target.value)}
                        className="w-full bg-card border border-hairline rounded-xl px-4 py-2.5 text-sm text-ink focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-semibold tracking-wider text-subtext uppercase mb-1.5">Username (Optional)</label>
                      <input
                        type="text"
                        value={jiraUsername}
                        onChange={(e) => setJiraUsername(e.target.value)}
                        className="w-full bg-card border border-hairline rounded-xl px-4 py-2.5 text-sm text-ink focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition"
                      />
                    </div>
                  </div>
                </>
              ) : (
                <>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-semibold tracking-wider text-subtext uppercase mb-1.5">Owner / Org</label>
                      <input
                        type="text"
                        required
                        value={githubOwner}
                        onChange={(e) => setGithubOwner(e.target.value)}
                        className="w-full bg-card border border-hairline rounded-xl px-4 py-2.5 text-sm text-ink focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-semibold tracking-wider text-subtext uppercase mb-1.5">Repository</label>
                      <input
                        type="text"
                        required
                        value={githubRepo}
                        onChange={(e) => setGithubRepo(e.target.value)}
                        className="w-full bg-card border border-hairline rounded-xl px-4 py-2.5 text-sm text-ink focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-xs font-semibold tracking-wider text-subtext uppercase mb-1.5">Personal Access Token</label>
                    <input
                      type="password"
                      required
                      value={githubToken}
                      onChange={(e) => setGithubToken(e.target.value)}
                      className="w-full bg-card border border-hairline rounded-xl px-4 py-2.5 text-sm text-ink focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition"
                    />
                  </div>
                </>
              )}

              <div className="pt-4">
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full h-11 bg-primary text-background rounded-xl font-medium hover:bg-primary/90 transition disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {loading ? <RefreshCw className="size-4 animate-spin" /> : "Save Connection"}
                </button>
              </div>
            </form>
          )}

        </div>
      </div>
    </div>
  );
}

export default IntegrationModal;
