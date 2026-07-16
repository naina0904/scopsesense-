import { useState, useMemo } from "react";
import { useAudit } from "../context/AuditContext";
import { askDelayAnalysisChat } from "../api/chat";
import { X, Send, AlertTriangle, RefreshCw, Sparkles, HelpCircle, User, Bot, ChevronDown, ChevronUp, Users, Layers } from "lucide-react";
import toast from "react-hot-toast";
import TemporalDriftChart from "./TemporalDriftChart";
import HelpTooltip from "./HelpTooltip";

function DelayAnalysisResults({ results, faqs = [], onScrubFaq }) {
  const { fetchRowIntelligence, showDeveloperPerformance, setShowDeveloperPerformance } = useAudit();
  
  const [localDevModal, setLocalDevModal] = useState(false);
  const isDevModalOpen = showDeveloperPerformance !== undefined ? showDeveloperPerformance : localDevModal;
  const setIsDevModalOpen = setShowDeveloperPerformance || setLocalDevModal;
  const [isVarianceModalOpen, setIsVarianceModalOpen] = useState(false);
  
  // Drawer state
  const [selectedRow, setSelectedRow] = useState(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [drawerLoading, setDrawerLoading] = useState(false);
  const [rowIntelligence, setRowIntelligence] = useState(null);
  const [activeFaq, setActiveFaq] = useState(null);

  // Drawer Chat state
  const [chatMessages, setChatMessages] = useState([]);
  const [chatQuestion, setChatQuestion] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const [auditScopeMode, setAuditScopeMode] = useState(() => localStorage.getItem("auditScopeMode") || "full_lifecycle");

  const tableItems = (table) => Array.isArray(table) ? table : table?.items || [];
  const rawVarianceRows = tableItems(results.variance_table);
  const developerRows = tableItems(results.developer_table);

  const isPhaseRow = (reqName, modName) => {
    const norm = (reqName || "").toLowerCase().trim();
    return modName === "Project Phases" || ["internal testing", "client testing", "deployment", "testing", "qa"].some(p => norm.includes(p));
  };

  const varianceRows = useMemo(() => {
    if (auditScopeMode === "full_lifecycle") return rawVarianceRows;
    return rawVarianceRows.filter(r => !isPhaseRow(r.requirement, r.module));
  }, [rawVarianceRows, auditScopeMode]);

  const activePlannedHours = varianceRows.reduce((sum, r) => sum + (Number(r.planned_hours) || 0), 0);
  const activeActualHours = varianceRows.reduce((sum, r) => sum + (Number(r.actual_hours) || 0), 0);
  const activeVariance = activeActualHours - activePlannedHours;
  const activeRemainingHours = varianceRows.reduce((sum, r) => {
    const planned = Number(r.planned_hours || 0);
    const actual = Number(r.actual_hours || 0);
    const isDone = String(r.status || "").toLowerCase() in { done: 1, completed: 1, closed: 1, resolved: 1 };
    return sum + (isDone ? 0 : Math.max(0, planned - actual));
  }, 0);

  const unmappedBaselineRows = varianceRows.filter(r => (Number(r.planned_hours) > 0) && (Number(r.actual_hours) === 0));
  const unmappedBaselineHours = unmappedBaselineRows.reduce((sum, r) => sum + (Number(r.planned_hours) || 0), 0);

  const handleRowClick = async (row) => {
    setSelectedRow(row);
    setIsDrawerOpen(true);
    setDrawerLoading(true);
    setRowIntelligence(null);
    setChatMessages([]);
    setChatQuestion("");
    setActiveFaq(null);

    try {
      const data = await fetchRowIntelligence(row.requirement);
      setRowIntelligence(data);
      if (data.fallback_used) {
         toast(`Auto-switched to ${data.fallback_used} AI due to primary model rate limits.`, {
             icon: '🔄',
             duration: 5000
         });
      }
    } catch (err) {
      console.error("Failed to load row intelligence", err);
      setRowIntelligence({
        error: "AI analysis is temporarily unavailable."
      });
    } finally {
      setDrawerLoading(false);
    }
  };

  const handleSendChat = async () => {
    if (!chatQuestion.trim()) return;

    const userMsg = { role: "user", text: chatQuestion };
    setChatMessages(prev => [...prev, userMsg]);
    setChatLoading(true);
    const questionToSend = chatQuestion;
    setChatQuestion("");

    try {
      const context = `[Row Context: Module: ${selectedRow.module}, Requirement: ${selectedRow.requirement}, Developer: ${selectedRow.developer}, Planned Hours: ${selectedRow.planned_hours}, Actual Hours: ${selectedRow.actual_hours}, Variance: ${selectedRow.variance}h, Status: ${selectedRow.status}] User Question: ${questionToSend}`;
      
      const response = await askDelayAnalysisChat(
        context,
        results.session_id,
        "groq",
        results.project_key,
        results.platform
      );

      const aiMsg = { role: "ai", text: response.answer };
      setChatMessages(prev => [...prev, aiMsg]);
    } catch (err) {
      setChatMessages(prev => [...prev, { role: "ai", text: "Failed to connect to AI assistant. Please try again." }]);
    } finally {
      setChatLoading(false);
    }
  };

  return (
    <div className="space-y-8 relative pb-20">
      
      <section className="lift-card p-8 md:p-10 grain">
         <div className="flex flex-wrap items-center justify-between gap-4">
           <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-primary">
             <Sparkles className="size-3.5" /> Executive Forensic Summary
           </div>
           <div className="flex items-center gap-2 text-xs font-medium text-subtext bg-card px-3 py-1.5 rounded-full border border-hairline shadow-sm">
             <span className="size-2 rounded-full bg-emerald-500 animate-pulse" />
             <span>Completed on: <strong className="text-ink font-semibold">
               {results.analysis_timestamp 
                 ? new Date(results.analysis_timestamp.replace(' ', 'T') + 'Z').toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' }) 
                 : "Just now"}
             </strong></span>
           </div>
         </div>
         <h2 className="mt-4 font-display text-3xl md:text-4xl font-bold text-ink tracking-tight">
           Project Schedule & Drift Analysis: <span className="text-primary">{results.project_key || "Repository"}</span>
         </h2>
          <p className="mt-2 text-sm md:text-base text-subtext max-w-3xl leading-relaxed">
            AI Forensic Audit: SRS Specs vs. Jira Actuals.
          </p>
          {/* Standardized Industrial Forensic Metrics Table / Grid */}
          <div className="mt-8 border border-hairline rounded-2xl overflow-hidden bg-card shadow-sm">
            <div className="bg-secondary/60 px-6 py-3.5 border-b border-hairline flex flex-wrap items-center justify-between gap-2">
              <span className="text-xs font-bold uppercase tracking-wider text-ink flex items-center gap-2">
                <span className="size-2 rounded-full bg-primary" />
                Audit Scope & Schedule Reconciliation Table
              </span>
              <span className="text-[11px] font-semibold text-subtext bg-background/80 px-3 py-1 rounded-md border border-hairline shadow-2xs">
                {auditScopeMode === "full_lifecycle" ? "Full Lifecycle (Design & Dev + Testing)" : "Design & Dev Only"}
              </span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 divide-y sm:divide-y-0 sm:divide-x divide-hairline bg-card">
              <div className="p-5 flex flex-col justify-between">
                <div className="text-[11px] font-bold text-subtext uppercase tracking-wider flex items-center justify-between">
                  <span>Exact Hours Planned (SRS)</span>
                  <span className="size-2 rounded-full bg-[#3b82f6]" />
                </div>
                <div className="text-2xl font-display font-bold text-info mt-2">
                  {activePlannedHours.toFixed(1)} <span className="text-xs font-semibold text-subtext font-sans">hours</span>
                </div>
                <div className="text-[11px] text-subtext mt-1.5 leading-snug">
                  Budgeted baseline extracted from SRS document
                </div>
              </div>

              <div className="p-5 flex flex-col justify-between">
                <div className="text-[11px] font-bold text-subtext uppercase tracking-wider flex items-center justify-between">
                  <span>Hours Worked On (Jira)</span>
                  <span className="size-2 rounded-full bg-[#10b981]" />
                </div>
                <div className={`text-2xl font-display font-bold mt-2 ${activeVariance > 0 ? "text-risk" : "text-emerald"}`}>
                  {activeActualHours.toFixed(1)} <span className="text-xs font-semibold text-subtext font-sans">hours</span>
                </div>
                <div className="text-[11px] text-subtext mt-1.5 leading-snug">
                  Actual timespent logged across Jira issues
                </div>
              </div>

              <div className="p-5 flex flex-col justify-between">
                <div className="text-[11px] font-bold text-subtext uppercase tracking-wider flex items-center justify-between">
                  <HelpTooltip termKey="Remaining Effort">Remaining Workload</HelpTooltip>
                  <span className="size-2 rounded-full bg-[#8b5cf6]" />
                </div>
                <div className="text-2xl font-display font-bold text-ink mt-2">
                  {activeRemainingHours.toFixed(1)} <span className="text-xs font-semibold text-subtext font-sans">hours</span>
                </div>
                <div className="text-[11px] text-subtext mt-1.5 leading-snug">
                  Estimated effort required to reach completion
                </div>
              </div>

              <div className="p-5 flex flex-col justify-between">
                <div className="text-[11px] font-bold text-subtext uppercase tracking-wider flex items-center justify-between">
                  <HelpTooltip termKey="Forecasted Slip">Forecasted Slip</HelpTooltip>
                  <span className="size-2 rounded-full bg-amber-500" />
                </div>
                <div className="text-2xl font-display font-bold text-amber-600 dark:text-amber-400 mt-2">
                  {Number(results.predicted_delay ?? 0).toFixed(1)} <span className="text-xs font-semibold text-subtext font-sans">weeks</span>
                </div>
                <div className="text-[11px] text-subtext mt-1.5 leading-snug">
                  AI predicted schedule drift based on velocity
                </div>
              </div>

              <div className="p-5 flex flex-col justify-between">
                <div className="text-[11px] font-bold text-subtext uppercase tracking-wider flex items-center justify-between">
                  <HelpTooltip termKey="Ghost Scope Creep">Ghost Scope Creep</HelpTooltip>
                  <span className="size-2 rounded-full bg-rose-500" />
                </div>
                <div className="text-2xl font-display font-bold text-rose-600 dark:text-rose-400 mt-2">
                  {results.ghost_hours > 0 ? '+' : ''}{Number(results.ghost_hours ?? 0).toFixed(1)} <span className="text-xs font-semibold text-subtext font-sans">hours</span>
                </div>
                <div className="text-[11px] text-subtext mt-1.5 leading-snug">
                  Unbudgeted Jira effort logged outside SRS baseline
                </div>
              </div>
            </div>
          </div>
       </section>



      {results.freshness_penalty_applied && (
        <div className="bg-warning/20 border border-warning/30 rounded-3xl p-6 flex items-start gap-4 shadow-sm">
          <AlertTriangle className="size-6 text-warning mt-0.5" />
          <div>
            <h3 className="text-warning font-bold text-lg flex items-center gap-2">
              <HelpTooltip termKey="Stale Data Warning">Stale Data Warning</HelpTooltip>
            </h3>
            <p className="text-ink/80 mt-1">
              The repository data is older than 24 hours. A freshness penalty modifier of <strong>{results.freshness_penalty_factor}</strong> has been applied to all severity scores.
            </p>
          </div>
        </div>
      )}

      <TemporalDriftChart
        varianceRows={varianceRows}
        faqs={faqs}
        onScrubFaq={onScrubFaq}
        onSelectRow={handleRowClick}
      />

      {/* Sleek Clickable Card for SRS vs Actual Variance */}
      <div className="bg-card border border-hairline rounded-3xl p-6 md:p-8 shadow-sm relative overflow-hidden transition-all duration-300">
        <div className="absolute -top-32 -right-32 size-96 bg-info/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-32 -left-32 size-96 bg-emerald/10 rounded-full blur-3xl pointer-events-none" />

        <div 
          onClick={() => setIsVarianceModalOpen(true)}
          className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 relative z-10 cursor-pointer select-none group"
        >
          <div>
            <div className="flex flex-wrap items-center gap-3">
              <h3 className="font-display text-2xl md:text-3xl text-ink tracking-tight flex items-center gap-2.5 group-hover:text-info transition-colors">
                <Sparkles className="size-7 text-info shrink-0 animate-pulse" />
                SRS vs Actual Variance
              </h3>
              <span className="chip border text-xs font-extrabold px-3.5 py-1 rounded-full flex items-center gap-1.5 shadow-sm bg-secondary text-ink border-hairline">
                <Layers className="size-3.5 text-info" />
                {varianceRows.length} Requirements
              </span>
              <span className="text-xs font-extrabold text-info bg-info/10 border border-info/30 px-3.5 py-1.5 rounded-full flex items-center gap-1.5 shadow-sm group-hover:bg-info group-hover:text-white transition-all">
                <Sparkles className="size-3.5" />
                Click to Launch Requirement Variance Modal
              </span>
            </div>
            <p className="text-xs text-subtext mt-2 max-w-xl">
              Schedule deviation analysis mapped row-by-row to software requirements and Jira execution.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <div className="px-5 py-2.5 rounded-2xl bg-info/10 border border-info/30 font-bold text-xs text-info flex items-center gap-2 group-hover:bg-info group-hover:text-white transition-all shadow-sm shrink-0">
              <span>View Reconciliation</span>
            </div>
          </div>
        </div>
      </div>

      {/* Glassmorphic Cinematic Pop-up Modal for SRS vs Actual Variance */}
      {isVarianceModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 md:p-10 bg-ink/80 backdrop-blur-md animate-in fade-in duration-300">
          <div 
            onClick={(e) => e.stopPropagation()}
            className="bg-background border border-hairline/80 rounded-3xl shadow-2xl w-full max-w-6xl max-h-[90vh] flex flex-col overflow-hidden animate-in zoom-in-95 duration-300"
          >
            {/* Modal Header */}
            <div className="px-8 py-6 border-b border-hairline flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-card">
              <div className="flex items-center gap-3">
                <Sparkles className="size-7 text-info shrink-0 animate-pulse" />
                <div>
                  <h3 className="font-display text-2xl text-ink font-bold">SRS vs Actual Variance</h3>
                  <p className="text-xs text-subtext mt-0.5">Schedule deviation analysis mapped to requirements. Click any row to launch AI deep-dive analysis.</p>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <button
                  onClick={() => setIsVarianceModalOpen(false)}
                  className="size-10 rounded-full bg-secondary hover:bg-rose/20 hover:text-risk flex items-center justify-center text-subtext font-bold transition-all cursor-pointer"
                  title="Close Modal"
                >
                  ✕
                </button>
              </div>
            </div>

            {/* Modal Body (Table) */}
            <div className="p-8 overflow-y-auto flex-1 bg-background">
              <div className="soft-card overflow-hidden border border-hairline">
                <div className="overflow-x-auto">
                  <div className="min-w-[900px]">
                     <div className="grid grid-cols-12 px-8 py-3.5 text-[11px] uppercase tracking-wider text-subtext bg-beige/40 border-b border-hairline items-center font-bold">
                       <div className="col-span-2">Module</div>
                       <div className="col-span-4">Requirement</div>
                       <div className="col-span-1 text-center">Planned</div>
                       <div className="col-span-1 text-center">Actual</div>
                       <div className="col-span-1 text-center">Variance</div>
                       <div className="col-span-2 text-center">
                         <HelpTooltip termKey="Schedule Status">Schedule Status</HelpTooltip>
                       </div>
                       <div className="col-span-1 text-right">FAQs</div>
                     </div>
                     <div className="divide-y divide-hairline">
                       {varianceRows.map((row, index) => {
                         const statusLower = (row.status || "").toLowerCase();
                         const isDone = statusLower === "done" || statusLower === "completed" || statusLower === "resolved";
                         
                         let scheduleStatus = "On Track";
                         let statusColor = "bg-lavender/40 text-ink";
                         
                         if (row.variance > 0) {
                           scheduleStatus = "Delayed";
                           statusColor = "bg-rose/20 text-risk";
                         } else if (row.variance < 0) {
                           const remaining = isDone ? 0 : Math.max(0, Number(row.planned_hours || 0) - Number(row.actual_hours || 0));
                           if (isDone && remaining === 0 && Number(row.actual_hours || 0) > 0) {
                             scheduleStatus = "Advanced";
                             statusColor = "bg-pista text-ink";
                           } else if (row.actual_hours === 0) {
                             scheduleStatus = "Pending";
                             statusColor = "bg-slate-100 text-slate-500";
                           } else {
                             scheduleStatus = "On Track";
                             statusColor = "bg-lavender/40 text-ink";
                           }
                         }
                         
                         return (
                         <div 
                           key={`${row.requirement}-${index}`} 
                           onClick={() => {
                             setIsVarianceModalOpen(false);
                             handleRowClick(row);
                           }}
                           className="grid grid-cols-12 px-8 py-4 items-center hover:bg-secondary/50 cursor-pointer transition group"
                         >
                           <div className="col-span-2 text-sm text-subtext">{row.module}</div>
                           <div className="col-span-4 text-sm font-medium text-ink pr-4">{row.requirement}</div>
                           <div className="col-span-1 text-center text-sm">{Number(row.planned_hours || 0).toFixed(1).replace(/\.0$/, '')}h</div>
                           <div className="col-span-1 text-center text-sm">{Number(row.actual_hours || 0).toFixed(1).replace(/\.0$/, '')}h</div>
                           <div className={`col-span-1 text-center text-sm font-bold ${row.variance > 0 ? "text-risk" : row.variance < 0 ? "text-success" : "text-subtext"}`}>
                             {row.variance > 0 ? `+${Number(row.variance).toFixed(1).replace(/\.0$/, '')}` : Number(row.variance || 0).toFixed(1).replace(/\.0$/, '')}h
                           </div>
                           <div className="col-span-2 flex justify-center">
                             <span className={`px-3 py-1 text-xs font-medium rounded-full min-w-[85px] text-center inline-block ${statusColor}`}>
                               {scheduleStatus}
                             </span>
                           </div>
                           <div className="col-span-1 flex justify-end">
                             <span className="flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider text-ink/40 group-hover:text-info transition-colors">
                               <Sparkles size={12} /> AI Insights
                             </span>
                           </div>
                         </div>
                       )})}
                       {!varianceRows.length && <div className="p-8 text-center text-subtext">No variance rows available.</div>}
                     </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Sleek Clickable Card for Developer Performance */}
      <div className="bg-card border border-hairline rounded-3xl p-6 md:p-8 shadow-sm relative overflow-hidden transition-all duration-300">
        <div className="absolute -top-32 -right-32 size-96 bg-info/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-32 -left-32 size-96 bg-emerald/10 rounded-full blur-3xl pointer-events-none" />

        <div 
          onClick={() => setIsDevModalOpen(true)}
          className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 relative z-10 cursor-pointer select-none group"
        >
          <div>
            <div className="flex flex-wrap items-center gap-3">
              <h3 className="font-display text-2xl md:text-3xl text-ink tracking-tight flex items-center gap-2.5 group-hover:text-info transition-colors">
                <Users className="size-7 text-info shrink-0 animate-pulse" />
                Developer Performance
              </h3>
              <span className="chip border text-xs font-extrabold px-3.5 py-1 rounded-full flex items-center gap-1.5 shadow-sm bg-secondary text-ink border-hairline">
                <Users className="size-3.5 text-info" />
                {developerRows.length} Contributors
              </span>
              <span className="text-xs font-extrabold text-info bg-info/10 border border-info/30 px-3.5 py-1.5 rounded-full flex items-center gap-1.5 shadow-sm group-hover:bg-info group-hover:text-white transition-all">
                <Sparkles className="size-3.5" />
                Click to Launch Developer Velocity Modal
              </span>
            </div>
            <p className="text-xs text-subtext mt-2 max-w-xl">
              Individual developer velocity, hours allocation, and schedule variance across assigned requirements.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <div className="px-5 py-2.5 rounded-2xl bg-info/10 border border-info/30 font-bold text-xs text-info flex items-center gap-2 group-hover:bg-info group-hover:text-white transition-all shadow-sm shrink-0">
              <span>View Performance</span>
            </div>
          </div>
        </div>
      </div>

      {/* Glassmorphic Cinematic Pop-up Modal for Developer Performance */}
      {isDevModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 md:p-10 bg-ink/80 backdrop-blur-md animate-in fade-in duration-300">
          <div 
            onClick={(e) => e.stopPropagation()}
            className="bg-background border border-hairline/80 rounded-3xl shadow-2xl w-full max-w-6xl max-h-[90vh] flex flex-col overflow-hidden animate-in zoom-in-95 duration-300"
          >
            {/* Modal Header */}
            <div className="px-8 py-6 border-b border-hairline flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-card">
              <div className="flex items-center gap-3">
                <Users className="size-7 text-info shrink-0 animate-pulse" />
                <div>
                  <h3 className="font-display text-2xl text-ink font-bold">Developer Performance & Velocity</h3>
                  <p className="text-xs text-subtext mt-0.5">Individual efficiency metrics and workload breakdown.</p>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <button
                  onClick={() => setIsDevModalOpen(false)}
                  className="size-10 rounded-full bg-secondary hover:bg-rose/20 hover:text-risk flex items-center justify-center text-subtext font-bold transition-all cursor-pointer"
                  title="Close Modal"
                >
                  ✕
                </button>
              </div>
            </div>

            {/* Modal Body (Table) */}
            <div className="p-8 overflow-y-auto flex-1 bg-background">
              <div className="soft-card overflow-hidden border border-hairline">
                <div className="overflow-x-auto">
                  <div className="min-w-[800px]">
                     <div className="grid grid-cols-12 px-8 py-3.5 text-[11px] uppercase tracking-wider text-subtext bg-beige/40 border-b border-hairline font-bold">
                       <div className="col-span-3">Developer</div>
                       <div className="col-span-4">Assigned Modules</div>
                       <div className="col-span-1 text-center">Planned</div>
                       <div className="col-span-1 text-center">Actual</div>
                       <div className="col-span-2 text-center">Variance</div>
                       <div className="col-span-1 text-center">
                         <HelpTooltip termKey="Developer Efficiency">Efficiency</HelpTooltip>
                       </div>
                     </div>
                     <div className="divide-y divide-hairline">
                       {developerRows.map((row, index) => (
                         <div key={`${row.developer}-${index}`} className="grid grid-cols-12 px-8 py-4 items-center hover:bg-secondary/40 transition">
                           <div className="col-span-3 text-sm font-bold text-ink flex items-center gap-2">
                             <div className="size-8 rounded-full bg-info/10 text-info border border-info/30 grid place-items-center font-display font-bold text-xs shrink-0">
                               {(row.developer || "U").charAt(0).toUpperCase()}
                             </div>
                             <span className="truncate">{row.developer}</span>
                           </div>
                           <div className="col-span-4 text-sm text-subtext pr-4">
                             {(row.assigned_modules || []).slice(0, 3).join(", ")}
                             {(row.assigned_modules && row.assigned_modules.length > 3) ? `, +${row.assigned_modules.length - 3} more` : ""}
                           </div>
                           <div className="col-span-1 text-center text-sm font-semibold">{Number(row.planned_hours || 0).toFixed(1).replace(/\.0$/, '')}h</div>
                           <div className="col-span-1 text-center text-sm font-semibold">{Number(row.actual_hours || 0).toFixed(1).replace(/\.0$/, '')}h</div>
                           <div className={`col-span-2 text-center text-sm font-bold ${row.variance > 0 ? "text-risk" : row.variance < 0 ? "text-success" : "text-subtext"}`}>
                             {row.variance > 0 ? `+${Number(row.variance).toFixed(1).replace(/\.0$/, '')}` : Number(row.variance || 0).toFixed(1).replace(/\.0$/, '')}h
                           </div>
                           <div className="col-span-1 text-center text-sm font-bold">
                             <span className={`px-2.5 py-1 rounded-full text-xs ${
                               (row.efficiency || 0) >= 100 ? "bg-emerald/15 text-emerald" : (row.efficiency || 0) >= 80 ? "bg-amber-500/15 text-amber-600 dark:text-amber-400" : "bg-rose/15 text-risk"
                             }`}>
                               {Math.round(row.efficiency || 0)}%
                             </span>
                           </div>
                         </div>
                       ))}
                       {!developerRows.length && <div className="p-8 text-center text-subtext">No developer rows available.</div>}
                     </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Row-Level Intelligence Drawer */}
      {isDrawerOpen && selectedRow && (
        <div className="fixed inset-0 z-[100] flex justify-end bg-ink/40 backdrop-blur-sm transition duration-300">
          <div className="w-full max-w-xl bg-background border-l border-hairline h-full flex flex-col shadow-2xl relative animate-in slide-in-from-right duration-300">
            {/* Header */}
            <div className="p-6 border-b border-hairline flex justify-between items-center bg-card">
              <div>
                <span className="text-[10px] font-bold text-subtext uppercase tracking-widest">{selectedRow.module}</span>
                <h3 className="text-xl font-display text-ink mt-1 break-words leading-tight">{selectedRow.requirement}</h3>
              </div>
              <button 
                onClick={() => setIsDrawerOpen(false)}
                className="p-2 text-subtext hover:text-ink rounded-full hover:bg-secondary transition ml-4 shrink-0"
              >
                <X size={20} />
              </button>
            </div>

            {/* Content Body */}
            <div className="flex-1 overflow-y-auto p-6 space-y-8">
              {drawerLoading ? (
                <div className="flex flex-col items-center justify-center py-20 text-subtext space-y-4">
                  <RefreshCw size={32} className="animate-spin text-ink/40" />
                  <p className="text-sm font-medium">Generating row intelligence...</p>
                </div>
              ) : (
                <>
                  <div className="grid grid-cols-3 gap-3">
                    <div className="bg-card border border-hairline p-4 rounded-2xl">
                      <p className="text-[10px] uppercase tracking-wider text-subtext">Planned</p>
                      <p className="text-xl font-display mt-1">{Number(selectedRow.planned_hours || 0).toFixed(1).replace(/\.0$/, '')}h</p>
                    </div>
                    <div className="bg-card border border-hairline p-4 rounded-2xl">
                      <p className="text-[10px] uppercase tracking-wider text-subtext">Actual</p>
                      <p className="text-xl font-display mt-1">{Number(selectedRow.actual_hours || 0).toFixed(1).replace(/\.0$/, '')}h</p>
                    </div>
                    <div className={`border p-4 rounded-2xl ${selectedRow.variance > 0 ? "bg-rose/10 border-rose/30" : "bg-pista/10 border-pista/30"}`}>
                      <p className="text-[10px] uppercase tracking-wider text-subtext">Variance</p>
                      <p className={`text-xl font-display mt-1 ${selectedRow.variance > 0 ? "text-risk" : "text-success"}`}>
                        {selectedRow.variance > 0 ? `+${Number(selectedRow.variance).toFixed(1).replace(/\.0$/, '')}` : Number(selectedRow.variance || 0).toFixed(1).replace(/\.0$/, '')}h
                      </p>
                    </div>
                  </div>

                  {selectedRow.evidence && (
                    <div className="bg-beige/40 border border-hairline rounded-2xl p-4 text-xs font-mono text-ink/80 leading-relaxed break-words">
                      <div className="font-sans font-bold text-[11px] uppercase tracking-wider text-subtext mb-1 flex items-center gap-1.5">
                        <Sparkles className="size-3.5 text-primary" /> Audit Traceability & Mapped Tickets
                      </div>
                      {selectedRow.evidence}
                    </div>
                  )}

                  {rowIntelligence && rowIntelligence.error && (
                    <div className="bg-warning/20 border border-warning/30 rounded-2xl p-5 flex items-start gap-3">
                      <AlertTriangle className="size-5 text-warning shrink-0" />
                      <p className="text-sm font-medium text-warning mt-0.5">{rowIntelligence.error}</p>
                    </div>
                  )}

                  {rowIntelligence && !rowIntelligence.error && (
                    <div className="space-y-6">
                      <div className="bg-lavender/10 border border-lavender/30 rounded-2xl p-5">
                        <div className="flex items-center gap-2 mb-2">
                          <Sparkles size={16} className="text-ink/60" />
                          <h4 className="font-semibold text-sm">AI Root Cause Analysis</h4>
                        </div>
                        <p className="text-sm text-ink/80 leading-relaxed">{rowIntelligence.root_cause}</p>
                      </div>

                      <div className="space-y-3">
                        <h4 className="text-sm font-semibold flex items-center gap-2">
                          <HelpCircle size={16} className="text-subtext" />
                          Contextual FAQs
                        </h4>
                        <div className="space-y-2">
                          {(rowIntelligence.faqs || [])
                            .filter((faq, idx, self) =>
                              idx === self.findIndex(f => (f.question || "").trim().toLowerCase() === (faq.question || "").trim().toLowerCase())
                            )
                            .map((faq, idx) => (
                            <div key={idx} className="border border-hairline bg-card rounded-2xl overflow-hidden">
                              <button
                                className="w-full text-left px-4 py-3 flex justify-between items-center text-sm font-medium hover:bg-secondary/50 transition"
                                onClick={() => setActiveFaq(activeFaq === idx ? null : idx)}
                              >
                                <span>{faq.question}</span>
                                {activeFaq === idx ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                              </button>
                              {activeFaq === idx && (
                                <div className="px-4 pb-3 pt-2 text-sm text-subtext bg-card/50 whitespace-pre-wrap font-sans">
                                  {faq.answer}
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* AI Chat Area inside Drawer */}
                  <div className="border-t border-hairline pt-6 mt-8">
                    <h4 className="text-sm font-semibold flex items-center gap-2 mb-4">
                      <Sparkles size={16} className="text-subtext" />
                      Deep Dive Analysis
                    </h4>
                    
                    <div className="space-y-4 mb-4">
                      {chatMessages.map((msg, idx) => (
                        <div key={idx} className={`flex gap-3 ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                          {msg.role === "ai" && <div className="size-8 rounded-full bg-lavender/40 grid place-items-center shrink-0"><Bot size={14} /></div>}
                          <div className={`p-3 rounded-2xl text-sm max-w-[85%] ${
                            msg.role === "user" ? "bg-ink text-background rounded-tr-sm" : "bg-card border border-hairline rounded-tl-sm text-ink/90"
                          }`}>
                            {msg.text}
                          </div>
                          {msg.role === "user" && <div className="size-8 rounded-full bg-secondary grid place-items-center shrink-0"><User size={14} /></div>}
                        </div>
                      ))}
                      {chatLoading && (
                         <div className="flex gap-3 justify-start">
                           <div className="size-8 rounded-full bg-lavender/40 grid place-items-center shrink-0"><Bot size={14} /></div>
                           <div className="p-3 rounded-2xl bg-card border border-hairline rounded-tl-sm text-sm text-subtext flex items-center gap-2">
                             <div className="flex space-x-1">
                               <div className="w-1.5 h-1.5 bg-ink/40 rounded-full animate-bounce"></div>
                               <div className="w-1.5 h-1.5 bg-ink/40 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                               <div className="w-1.5 h-1.5 bg-ink/40 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                             </div>
                           </div>
                         </div>
                      )}
                    </div>

                    <div className="relative">
                      <input
                        type="text"
                        value={chatQuestion}
                        onChange={(e) => setChatQuestion(e.target.value)}
                        onKeyDown={(e) => e.key === "Enter" && handleSendChat()}
                        placeholder="Ask about this specific delay..."
                        className="w-full bg-background border border-hairline rounded-full py-3 pl-4 pr-12 text-sm focus:outline-none focus:ring-1 focus:ring-ring shadow-sm"
                        disabled={chatLoading}
                      />
                      <button
                        onClick={handleSendChat}
                        disabled={!chatQuestion.trim() || chatLoading}
                        className="absolute right-2 top-1.5 bottom-1.5 aspect-square rounded-full bg-ink text-background grid place-items-center disabled:opacity-50 transition"
                      >
                        <Send size={14} />
                      </button>
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function Headline({ tone, label, value, sub }) {
  return (
    <div className={`rounded-3xl p-6 border border-hairline ${tone}`}>
      <div className="text-[11px] uppercase tracking-wider text-ink/60">{label}</div>
      <div className="mt-3 flex items-baseline gap-2">
        <span className="font-display text-5xl">{value}</span>
        <span className="text-sm text-ink/60">{sub}</span>
      </div>
    </div>
  );
}

export default DelayAnalysisResults;
