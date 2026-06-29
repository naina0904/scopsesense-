import { useState } from "react";
import { useAudit } from "../context/AuditContext";
import { askDelayAnalysisChat } from "../api/chat";
import { X, Send, AlertTriangle, RefreshCw, Sparkles, HelpCircle, User, Bot, ChevronDown, ChevronUp } from "lucide-react";
import toast from "react-hot-toast";

function DelayAnalysisResults({ results }) {
  const { fetchRowIntelligence } = useAudit();
  
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

  const tableItems = (table) => Array.isArray(table) ? table : table?.items || [];
  const varianceRows = tableItems(results.variance_table);
  const developerRows = tableItems(results.developer_table);

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
      
      <section className="lift-card p-10 grain">
         <div className="flex items-center gap-2 text-xs text-subtext"><Sparkles className="size-3.5" /> Executive summary</div>
         <h2 className="mt-3 font-display text-4xl leading-tight max-w-3xl">
           Audit for <em className="not-italic text-ink font-medium">{results.project_key}</em> completed on <em className="not-italic text-ink font-medium">
             {results.analysis_timestamp 
                ? new Date(results.analysis_timestamp.replace(' ', 'T') + 'Z').toLocaleDateString(undefined, { month: 'long', day: 'numeric', year: 'numeric', hour: 'numeric', minute: '2-digit' }) 
                : "recently"}
           </em>.
         </h2>
         <div className="mt-10 grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
           <Headline tone="bg-info/40" label="SRS Roadmap Variance" value={`${results.srs_schedule_variance ?? results.schedule_variance ?? 0}h`} sub="Pure baseline slip" />
           <Headline tone="bg-rose/20" label="Ghost Scope Creep" value={`${results.ghost_hours > 0 ? '+' : ''}${results.ghost_hours ?? 0}h`} sub="Unbudgeted drift" />
           <Headline tone="bg-emerald/30" label="Remaining Work" value={`${results.remaining_effort ?? 0}h`} sub="Open tasks" />
           <Headline tone="bg-beige" label="Predicted Delay" value={`${results.predicted_delay ?? 0}w`} sub="Forecasted slip" />
         </div>
      </section>

      {results.freshness_penalty_applied && (
        <div className="bg-warning/20 border border-warning/30 rounded-3xl p-6 flex items-start gap-4 shadow-sm">
          <AlertTriangle className="size-6 text-warning mt-0.5" />
          <div>
            <h3 className="text-warning font-bold text-lg">Stale Data Warning</h3>
            <p className="text-ink/80 mt-1">
              The repository data is older than 24 hours. A freshness penalty modifier of <strong>{results.freshness_penalty_factor}</strong> has been applied to all severity scores.
            </p>
          </div>
        </div>
      )}





      <div className="soft-card overflow-hidden">
        <div className="px-8 py-6 border-b border-hairline flex justify-between items-center">
          <div>
            <h3 className="font-display text-2xl">SRS vs Actual Variance</h3>
            <p className="text-subtext text-sm mt-1">Schedule deviation analysis mapped to requirements.</p>
          </div>
        </div>
        <div className="overflow-x-auto">
          <div className="min-w-[900px]">
             <div className="grid grid-cols-12 px-8 py-3 text-[11px] uppercase tracking-wider text-subtext bg-beige/40 border-b border-hairline items-center">
               <div className="col-span-2">Module</div>
               <div className="col-span-4">Requirement</div>
               <div className="col-span-1 text-center">Planned</div>
               <div className="col-span-1 text-center">Actual</div>
               <div className="col-span-1 text-center">Variance</div>
               <div className="col-span-2 text-center">Schedule Status</div>
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
                   if (isDone) {
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
                   onClick={() => handleRowClick(row)}
                   className="grid grid-cols-12 px-8 py-4 items-center hover:bg-secondary/50 cursor-pointer transition group"
                 >
                   <div className="col-span-2 text-sm text-subtext">{row.module}</div>
                   <div className="col-span-4 text-sm font-medium text-ink pr-4">{row.requirement}</div>
                   <div className="col-span-1 text-center text-sm">{row.planned_hours}h</div>
                   <div className="col-span-1 text-center text-sm">{row.actual_hours}h</div>
                   <div className={`col-span-1 text-center text-sm font-bold ${row.variance > 0 ? "text-risk" : row.variance < 0 ? "text-success" : "text-subtext"}`}>
                     {row.variance > 0 ? `+${row.variance}` : row.variance}h
                   </div>
                   <div className="col-span-2 flex justify-center">
                     <span className={`px-3 py-1 text-xs font-medium rounded-full min-w-[85px] text-center inline-block ${statusColor}`}>
                       {scheduleStatus}
                     </span>
                   </div>
                   <div className="col-span-1 flex justify-end">
                     <span className="flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider text-ink/0 group-hover:text-ink/40 transition-colors">
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

      <div className="soft-card overflow-hidden">
        <div className="px-8 py-6 border-b border-hairline">
          <h3 className="font-display text-2xl">Developer Performance</h3>
        </div>
        <div className="overflow-x-auto">
          <div className="min-w-[800px]">
             <div className="grid grid-cols-12 px-8 py-3 text-[11px] uppercase tracking-wider text-subtext bg-beige/40 border-b border-hairline">
               <div className="col-span-3">Developer</div>
               <div className="col-span-4">Assigned Modules</div>
               <div className="col-span-1 text-center">Planned</div>
               <div className="col-span-1 text-center">Actual</div>
               <div className="col-span-2 text-center">Variance</div>
               <div className="col-span-1 text-center">Efficiency</div>
             </div>
             <div className="divide-y divide-hairline">
               {developerRows.map((row, index) => (
                 <div key={`${row.developer}-${index}`} className="grid grid-cols-12 px-8 py-4 items-center">
                   <div className="col-span-3 text-sm font-medium text-ink">{row.developer}</div>
                   <div className="col-span-4 text-sm text-subtext pr-4">
                     {(row.assigned_modules || []).slice(0, 3).join(", ")}
                     {(row.assigned_modules && row.assigned_modules.length > 3) ? `, +${row.assigned_modules.length - 3} more` : ""}
                   </div>
                   <div className="col-span-1 text-center text-sm">{row.planned_hours}h</div>
                   <div className="col-span-1 text-center text-sm">{row.actual_hours}h</div>
                   <div className={`col-span-2 text-center text-sm font-bold ${row.variance > 0 ? "text-risk" : row.variance < 0 ? "text-success" : "text-subtext"}`}>
                     {row.variance > 0 ? `+${row.variance}` : row.variance}h
                   </div>
                   <div className="col-span-1 text-center text-sm font-medium">
                     {Math.round(row.efficiency || 0)}%
                   </div>
                 </div>
               ))}
               {!developerRows.length && <div className="p-8 text-center text-subtext">No developer rows available.</div>}
             </div>
          </div>
        </div>
      </div>

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
                      <p className="text-xl font-display mt-1">{selectedRow.planned_hours}h</p>
                    </div>
                    <div className="bg-card border border-hairline p-4 rounded-2xl">
                      <p className="text-[10px] uppercase tracking-wider text-subtext">Actual</p>
                      <p className="text-xl font-display mt-1">{selectedRow.actual_hours}h</p>
                    </div>
                    <div className={`border p-4 rounded-2xl ${selectedRow.variance > 0 ? "bg-rose/10 border-rose/30" : "bg-pista/10 border-pista/30"}`}>
                      <p className="text-[10px] uppercase tracking-wider text-subtext">Variance</p>
                      <p className={`text-xl font-display mt-1 ${selectedRow.variance > 0 ? "text-risk" : "text-success"}`}>
                        {selectedRow.variance > 0 ? `+${selectedRow.variance}` : selectedRow.variance}h
                      </p>
                    </div>
                  </div>

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
                          {rowIntelligence.faqs?.map((faq, idx) => (
                            <div key={idx} className="border border-hairline bg-card rounded-2xl overflow-hidden">
                              <button
                                className="w-full text-left px-4 py-3 flex justify-between items-center text-sm font-medium hover:bg-secondary/50 transition"
                                onClick={() => setActiveFaq(activeFaq === idx ? null : idx)}
                              >
                                <span>{faq.question}</span>
                                {activeFaq === idx ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                              </button>
                              {activeFaq === idx && (
                                <div className="px-4 pb-3 pt-1 text-sm text-subtext bg-card/50">
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
