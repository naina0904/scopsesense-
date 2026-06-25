import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAudit } from "../context/AuditContext";
import { PlayCircle, Sparkles, Check, AlertTriangle, RefreshCw, XCircle } from "lucide-react";
import { PageHeader, PageBody } from "../components/ui/PageChrome";

function AuditPage() {
  const { auditResult, loading, progress, error, setError, runDelayAnalysis, auditSession, fetchActiveSession } = useAudit();
  const navigate = useNavigate();
  const [provider, setProvider] = useState("groq");

  useEffect(() => {
    fetchActiveSession().catch(() => {});
  }, [fetchActiveSession]);

  const approvalSteps = [
    { name: "Planned Requirements confirmed", approved: auditSession?.planned_data_approved, link: "/upload-srs" },
    { name: "Platform Ingestion confirmed", approved: auditSession?.actual_data_approved, link: "/configuration" },
    { name: "Capacity Profile confirmed", approved: auditSession?.capacity_approved, link: "/configuration" },
    { name: "Merged Normalization approved", approved: auditSession?.normalized_data_approved, link: "/normalization" },
    { name: "Semantic Matches approved", approved: auditSession?.matches_approved, link: "/matches" },
  ];

  const allStepsApproved = approvalSteps.every(step => step.approved);

  const startAnalysis = async () => {
    if (!allStepsApproved) {
      setError("Cannot execute audit. All 5 steps must be reviewed and approved by the manager first.");
      return;
    }

    try {
      await runDelayAnalysis(provider);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || "Failed to start analysis.");
    }
  };

  useEffect(() => {
    if (auditResult) {
      navigate("/results");
    }
  }, [auditResult, navigate]);

  return (
    <>
      <PageHeader
        eyebrow="Step 8 · Audit workflow"
        title="Execute the audit."
        lede="One decision. ScopeSense will reconcile every planned requirement against delivered work and synthesize an executive report."
      />
      
      <PageBody>
        {error && (
          <div className="bg-rose/20 border border-rose text-ink px-4 py-3 rounded-xl text-sm font-medium flex items-center justify-between mb-6">
             <div className="flex items-center gap-2">
                <AlertTriangle className="size-4 text-risk" />
                <span>{error}</span>
             </div>
             <button onClick={() => setError(null)} className="opacity-50 hover:opacity-100">&times;</button>
          </div>
        )}

        <div className="lift-card overflow-hidden">
          <div className="grid lg:grid-cols-2">
            <div className="p-10 bg-beige/40">
              <h2 className="font-display text-3xl leading-tight">Ready to audit {auditSession?.project_key || "Project"}.</h2>
              <p className="mt-3 text-subtext">Review inputs and configure inference. Estimated runtime: ~2 minutes.</p>
              
              <ul className="mt-8 space-y-3 text-sm">
                {approvalSteps.map((step, idx) => (
                  <li key={idx} className="flex items-center justify-between gap-3">
                    <div className="flex items-center gap-3">
                      <div className={`size-6 rounded-full grid place-items-center ${step.approved ? "bg-pista/60 text-ink" : "bg-rose/30 text-risk"}`}>
                         {step.approved ? <Check className="size-3.5" /> : <XCircle className="size-3.5" />}
                      </div>
                      <span className={step.approved ? "text-ink" : "text-subtext font-medium"}>{step.name}</span>
                    </div>
                    {!step.approved && (
                      <button onClick={() => navigate(step.link)} className="text-xs text-ink underline hover:no-underline">Complete step</button>
                    )}
                  </li>
                ))}
              </ul>

              <div className="mt-8 space-y-2">
                 <label className="text-xs font-medium uppercase tracking-wider text-subtext">AI Provider for Inference</label>
                 <select
                   value={provider}
                   onChange={(e) => setProvider(e.target.value)}
                   className="w-full bg-card border border-hairline rounded-lg p-2.5 text-sm text-ink focus:outline-none focus:ring-1 focus:ring-ring"
                 >
                   <option value="groq">Groq (Llama-3 - Fast)</option>
                   <option value="gemini">Google Gemini (Recommended)</option>
                 </select>
              </div>

              <div className="mt-10">
                {loading ? (
                   <div className="space-y-3">
                     <div className="w-full bg-secondary h-3 rounded-full overflow-hidden">
                       <div 
                         className="bg-ink h-full transition-all duration-300"
                         style={{ width: `${progress}%` }}
                       />
                     </div>
                     <span className="text-sm text-subtext font-medium flex items-center gap-2">
                       <RefreshCw className="size-4 animate-spin" /> {progress}% - Running AI calculations...
                     </span>
                   </div>
                ) : (
                   <button 
                     onClick={startAnalysis}
                     disabled={!allStepsApproved || loading}
                     className="inline-flex h-14 items-center gap-3 px-8 rounded-full bg-ink text-background font-medium hover:opacity-90 transition shadow-[0_8px_24px_-8px_rgba(31,41,55,0.4)] disabled:opacity-50 disabled:shadow-none"
                   >
                     <PlayCircle className="size-5" /> Execute Audit
                   </button>
                )}
              </div>
            </div>
            
            <div className="p-10 bg-lavender/30">
              <div className="flex items-center gap-2 text-xs text-ink/60"><Sparkles className="size-3.5" /> What you'll get</div>
              <h3 className="mt-3 font-display text-2xl">An executive audit intelligence report</h3>
              <div className="mt-6 space-y-3">
                {[
                  { t: "Schedule Variance", d: "Planned vs delivered, mapped to requirements" },
                  { t: "Remaining Work", d: "Open tasks and their estimated completion" },
                  { t: "Predicted Delay", d: "Forecasted timeline slip based on current velocity" },
                  { t: "SRS vs Actual Breakdown", d: "Row-by-row variance analysis" },
                  { t: "Developer Performance", d: "Efficiency metrics for individual contributors" },
                  { t: "Deep Dive AI Drawer", d: "Row-level intelligence, RCA, and chat" },
                ].map(i => (
                  <div key={i.t} className="rounded-2xl bg-card border border-hairline p-4">
                    <div className="font-medium text-sm">{i.t}</div>
                    <div className="text-xs text-subtext mt-0.5">{i.d}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </PageBody>
    </>
  );
}

export default AuditPage;
