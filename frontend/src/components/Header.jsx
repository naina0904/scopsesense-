import { useState, useEffect } from "react";
import axios from "axios";
import { API_BASE_URL } from "../config";
import { Search, Bell, ChevronRight, X, Sparkles, AlertTriangle, CheckCircle, Clock, User, ShieldCheck, Zap, Layers, Users, FileText } from "lucide-react";
import { useLocation, Link, useNavigate } from "react-router-dom";
import { useAudit } from "../context/AuditContext";

// Mapping routes to clean names for Breadcrumbs
const ROUTE_NAMES = {
  "/upload-srs": "Upload SRS",
  "/requirements": "Planned Requirements",
  "/configuration": "Platform Configuration",
  "/normalization": "Normalization",
  "/matches": "Semantic Matches",
  "/execute": "Execute Audit",
  "/results": "Results",
  "/audit-intelligence": "Audit Intelligence"
};

function Breadcrumb({ pathname }) {
  const seg = pathname.split("/").filter(Boolean);
  const matchedName = ROUTE_NAMES[pathname] || (seg.length > 0 ? seg[0] : "Dashboard");

  return (
    <nav className="flex items-center gap-2 text-sm">
      <Link to="/" className="text-subtext hover:text-ink transition-colors">Workspace</Link>
      {seg.length > 0 && (
        <span className="flex items-center gap-2">
          <ChevronRight className="size-3.5 text-subtext" />
          <span className="text-ink font-medium">{matchedName}</span>
        </span>
      )}
    </nav>
  );
}

function Header() {
  const location = useLocation();
  const navigate = useNavigate();
  const { auditResult, setShowDeveloperPerformance } = useAudit();
  const [role, setRole] = useState(localStorage.getItem("scopesense_role") || "manager");

  // Search & Command Palette State
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  // Notifications Popover State
  const [isNotificationsOpen, setIsNotificationsOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);

  const handleRoleChange = async (newRole) => {
    setRole(newRole);
    localStorage.setItem("scopesense_role", newRole);
    try {
      const response = await axios.post(`${API_BASE_URL}/api/v1/auth/login`, {
        user_id: 1,
        role: newRole
      });
      localStorage.setItem("scopesense_token", response.data.access_token);
    } catch (err) {
      console.error("Login failed", err);
    }
  };

  useEffect(() => {
    handleRoleChange(role);
  }, []);

  // Keyboard shortcut listener (Cmd+K or Ctrl+K / Escape)
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setIsSearchOpen((prev) => !prev);
        setIsNotificationsOpen(false);
      }
      if (e.key === "Escape") {
        setIsSearchOpen(false);
        setIsNotificationsOpen(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  // Extract data from auditResult for global search & alerts
  const varianceRows = Array.isArray(auditResult?.variance_table) ? auditResult.variance_table : (auditResult?.variance_table?.items || []);
  const developerRows = Array.isArray(auditResult?.developer_table) ? auditResult.developer_table : (auditResult?.developer_table?.items || []);

  // Filtered lists for search query
  const filteredRequirements = varianceRows.filter(r => 
    (r.requirement || "").toLowerCase().includes(searchQuery.toLowerCase()) ||
    (r.module || "").toLowerCase().includes(searchQuery.toLowerCase())
  ).slice(0, 5);

  const filteredDevelopers = developerRows.filter(d => 
    (d.developer || "").toLowerCase().includes(searchQuery.toLowerCase()) ||
    (d.role || "").toLowerCase().includes(searchQuery.toLowerCase())
  ).slice(0, 4);

  const pages = [
    { name: "Upload SRS Document", path: "/upload-srs", desc: "Upload and parse software requirement specifications" },
    { name: "Planned Requirements", path: "/requirements", desc: "Review baseline effort and module breakdown" },
    { name: "Platform Configuration", path: "/configuration", desc: "Connect Jira and GitHub project trackers" },
    { name: "Normalization & Reconciliation", path: "/normalization", desc: "Reconcile planned specs and actual work items" },
    { name: "Semantic Matches", path: "/matches", desc: "AI-driven mapping between SRS and Jira tickets" },
    { name: "Execute Audit", path: "/execute", desc: "Run multi-model delay analysis and drift engine" },
    { name: "Results Dashboard", path: "/results", desc: "Executive schedule variance and drift reports" }
  ];

  const filteredPages = pages.filter(p => 
    p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    p.desc.toLowerCase().includes(searchQuery.toLowerCase())
  ).slice(0, 4);

  // Generate dynamic system alerts
  const alerts = [];
  if (auditResult) {
    if (Number(auditResult.ghost_hours || 0) > 0) {
      alerts.push({
        id: "ghost",
        type: "risk",
        title: "Ghost Scope Creep Detected",
        desc: `+${Number(auditResult.ghost_hours).toFixed(1)}h unbudgeted Jira work logged outside SRS baseline.`,
        time: "Active"
      });
    }
    if (auditResult.freshness_penalty_applied) {
      alerts.push({
        id: "stale",
        type: "warning",
        title: "Stale Repository Data",
        desc: `Freshness penalty modifier (${auditResult.freshness_penalty_factor}) applied to severity scores.`,
        time: "Active"
      });
    }
    const delayedReqs = [...varianceRows].filter(r => r.variance > 0).sort((a, b) => b.variance - a.variance);
    if (delayedReqs.length > 0) {
      alerts.push({
        id: "delay",
        type: "risk",
        title: "High Schedule Variance Alert",
        desc: `${delayedReqs[0].requirement} is delayed by +${Number(delayedReqs[0].variance).toFixed(1)}h.`,
        time: "Active"
      });
    }
  }
  alerts.push({
    id: "system",
    type: "success",
    title: "ScopeSense AI Engine Ready",
    desc: "Connected to multi-agent backend engine (Groq / Gemini). All systems operational.",
    time: "Live"
  });

  useEffect(() => {
    setUnreadCount(alerts.length);
  }, [auditResult]);

  return (
    <header className="h-16 border-b border-hairline bg-background/80 backdrop-blur sticky top-0 z-30 flex items-center gap-4 px-6 lg:px-10">
      <Breadcrumb pathname={location.pathname} />
      <div className="flex-1" />
      
      {/* Interactive Command Palette Trigger Bar */}
      <div 
        onClick={() => { setIsSearchOpen(true); setIsNotificationsOpen(false); }}
        className="hidden md:flex items-center gap-2.5 h-10 px-4 rounded-full border border-hairline bg-card hover:border-info/40 hover:bg-info/5 cursor-pointer transition-all w-80 max-w-full group shadow-sm"
      >
        <Search className="size-4 text-subtext group-hover:text-info transition-colors shrink-0" />
        <span className="text-subtext text-sm flex-1 select-none group-hover:text-ink transition-colors truncate">Search requirements, issues, people…</span>
        <span className="text-[10px] text-subtext font-mono bg-secondary px-1.5 py-0.5 rounded border border-hairline group-hover:text-info group-hover:border-info/30 transition-colors shrink-0">⌘K</span>
      </div>

      {/* Interactive Bell Icon & Notifications Popover */}
      <div className="relative">
        <button 
          onClick={() => { setIsNotificationsOpen(!isNotificationsOpen); setIsSearchOpen(false); }}
          className="size-10 rounded-full border border-hairline bg-card hover:border-info/40 hover:bg-info/5 grid place-items-center text-ink relative cursor-pointer transition-all shadow-sm"
          title="System & Risk Alerts"
        >
          <Bell className="size-4" />
          {unreadCount > 0 && (
            <span className="absolute -top-1 -right-1 size-5 bg-rose-500 text-white font-bold text-[10px] rounded-full flex items-center justify-center animate-pulse border-2 border-background shadow-sm">
              {unreadCount}
            </span>
          )}
        </button>

        {/* Dropdown Popover */}
        {isNotificationsOpen && (
          <div className="absolute right-0 top-12 w-80 sm:w-96 bg-card border border-hairline rounded-3xl shadow-2xl overflow-hidden z-50 animate-in fade-in zoom-in-95 duration-200">
            <div className="px-5 py-4 border-b border-hairline flex items-center justify-between bg-secondary/30">
              <div className="flex items-center gap-2">
                <Bell className="size-4 text-info" />
                <h4 className="font-display font-bold text-sm text-ink">System & Risk Alerts</h4>
              </div>
              {unreadCount > 0 && (
                <button 
                  onClick={() => setUnreadCount(0)}
                  className="text-[11px] font-bold text-info hover:underline cursor-pointer"
                >
                  Mark all read
                </button>
              )}
            </div>

            <div className="max-h-80 overflow-y-auto divide-y divide-hairline">
              {alerts.map((alert) => (
                <div key={alert.id} className="p-4 hover:bg-secondary/40 transition-colors flex items-start gap-3.5">
                  {alert.type === "risk" && <div className="size-8 rounded-full bg-rose/10 border border-rose/30 grid place-items-center text-risk shrink-0 mt-0.5"><AlertTriangle className="size-4" /></div>}
                  {alert.type === "warning" && <div className="size-8 rounded-full bg-amber-500/10 border border-amber-500/30 grid place-items-center text-amber-500 shrink-0 mt-0.5"><Clock className="size-4" /></div>}
                  {alert.type === "success" && <div className="size-8 rounded-full bg-emerald/10 border border-emerald/30 grid place-items-center text-emerald shrink-0 mt-0.5"><ShieldCheck className="size-4" /></div>}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2">
                      <h5 className="text-xs font-bold text-ink truncate">{alert.title}</h5>
                      <span className="text-[10px] text-subtext shrink-0">{alert.time}</span>
                    </div>
                    <p className="text-xs text-subtext mt-1 leading-relaxed">{alert.desc}</p>
                  </div>
                </div>
              ))}
            </div>

            <div className="p-3 bg-secondary/30 border-t border-hairline text-center">
              <span className="text-[11px] font-medium text-subtext flex items-center justify-center gap-1">
                <Sparkles className="size-3 text-info" />
                Automated by ScopeSense Intelligence Engine
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Global Command Palette Modal (⌘K) */}
      {isSearchOpen && (
        <div className="fixed inset-0 z-50 flex items-start justify-center pt-16 sm:pt-24 px-4 bg-ink/80 backdrop-blur-md animate-in fade-in duration-200">
          <div 
            onClick={(e) => e.stopPropagation()}
            className="bg-background border border-hairline/80 rounded-3xl shadow-2xl w-full max-w-2xl overflow-hidden animate-in zoom-in-95 duration-200 flex flex-col max-h-[80vh]"
          >
            {/* Search Input Bar */}
            <div className="p-4 sm:p-5 border-b border-hairline flex items-center gap-3 bg-card">
              <Search className="size-5 text-info shrink-0" />
              <input 
                autoFocus
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search requirements, developers, or jump to page..." 
                className="bg-transparent text-ink outline-none text-base font-medium flex-1 pr-4 placeholder:text-subtext"
              />
              {searchQuery && (
                <button 
                  onClick={() => setSearchQuery("")}
                  className="text-subtext hover:text-ink text-xs font-bold px-2 py-1 rounded bg-secondary cursor-pointer"
                >
                  Clear
                </button>
              )}
              <button 
                onClick={() => setIsSearchOpen(false)}
                className="size-8 rounded-full bg-secondary hover:bg-rose/20 hover:text-risk flex items-center justify-center text-subtext font-bold transition-all cursor-pointer text-xs"
              >
                ✕
              </button>
            </div>

            {/* Results Body */}
            <div className="p-5 overflow-y-auto flex-1 space-y-6 bg-background">
              {/* Requirements Section */}
              {filteredRequirements.length > 0 && (
                <div>
                  <div className="text-[11px] font-bold text-subtext uppercase tracking-wider mb-3 flex items-center gap-1.5">
                    <Layers className="size-3.5 text-info" />
                    <span>Requirements & Variances</span>
                  </div>
                  <div className="space-y-2">
                    {filteredRequirements.map((req, idx) => (
                      <div 
                        key={idx}
                        onClick={() => {
                          setIsSearchOpen(false);
                          navigate("/results");
                        }}
                        className="p-3.5 rounded-2xl bg-card border border-hairline hover:border-info/40 hover:bg-info/5 cursor-pointer transition-all flex items-center justify-between group"
                      >
                        <div className="min-w-0 pr-4">
                          <h5 className="text-sm font-bold text-ink group-hover:text-info transition-colors truncate">{req.requirement}</h5>
                          <span className="text-xs text-subtext">{req.module}</span>
                        </div>
                        <div className="flex items-center gap-3 shrink-0">
                          <span className={`text-xs font-bold px-2.5 py-1 rounded-full ${req.variance > 0 ? "bg-rose/15 text-risk" : req.variance < 0 ? "bg-info/15 text-info" : "bg-secondary text-subtext"}`}>
                            {req.variance > 0 ? `+${req.variance}h delay` : `${req.variance || 0}h variance`}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Developers Section */}
              {filteredDevelopers.length > 0 && (
                <div>
                  <div className="text-[11px] font-bold text-subtext uppercase tracking-wider mb-3 flex items-center gap-1.5">
                    <Users className="size-3.5 text-info" />
                    <span>Team Contributors</span>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                    {filteredDevelopers.map((dev, idx) => (
                      <div 
                        key={idx}
                        onClick={() => {
                          setIsSearchOpen(false);
                          navigate("/results");
                          if (setShowDeveloperPerformance) setShowDeveloperPerformance(true);
                        }}
                        className="p-3.5 rounded-2xl bg-card border border-hairline hover:border-info/40 hover:bg-info/5 cursor-pointer transition-all flex items-center justify-between group"
                      >
                        <div className="flex items-center gap-3 min-w-0">
                          <div className="size-8 rounded-full bg-info/15 text-info font-bold text-xs flex items-center justify-center shrink-0">
                            {(dev.developer || "U").charAt(0).toUpperCase()}
                          </div>
                          <div className="min-w-0">
                            <h5 className="text-sm font-bold text-ink group-hover:text-info transition-colors truncate">{dev.developer}</h5>
                            <span className="text-xs text-subtext">{dev.role || "Developer"}</span>
                          </div>
                        </div>
                        <span className="text-xs font-bold text-subtext font-mono shrink-0">{dev.total_hours || 0}h</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Navigation Pages */}
              <div>
                <div className="text-[11px] font-bold text-subtext uppercase tracking-wider mb-3 flex items-center gap-1.5">
                  <FileText className="size-3.5 text-subtext" />
                  <span>Platform Navigation</span>
                </div>
                <div className="space-y-2">
                  {filteredPages.map((p, idx) => (
                    <div 
                      key={idx}
                      onClick={() => {
                        setIsSearchOpen(false);
                        navigate(p.path);
                      }}
                      className="p-3.5 rounded-2xl bg-card border border-hairline hover:border-ink/20 hover:bg-secondary/40 cursor-pointer transition-all flex items-center justify-between group"
                    >
                      <div>
                        <h5 className="text-sm font-bold text-ink group-hover:text-info transition-colors">{p.name}</h5>
                        <p className="text-xs text-subtext">{p.desc}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Empty State */}
              {filteredRequirements.length === 0 && filteredDevelopers.length === 0 && filteredPages.length === 0 && (
                <div className="p-8 text-center text-subtext">
                  <p className="text-sm">No results found for &ldquo;<span className="text-ink font-bold">{searchQuery}</span>&rdquo;</p>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="px-5 py-3 bg-card border-t border-hairline flex items-center justify-between text-[11px] text-subtext">
              <span className="flex items-center gap-1.5"><kbd className="px-1.5 py-0.5 rounded bg-secondary border border-hairline font-mono font-bold">⌘K</kbd> or <kbd className="px-1.5 py-0.5 rounded bg-secondary border border-hairline font-mono font-bold">Ctrl+K</kbd> to toggle</span>
              <span className="flex items-center gap-1.5"><kbd className="px-1.5 py-0.5 rounded bg-secondary border border-hairline font-mono font-bold">ESC</kbd> to close</span>
            </div>
          </div>
        </div>
      )}
    </header>
  );
}

export default Header;
