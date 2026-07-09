import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAudit } from "../context/AuditContext";
import { PlayCircle, Sparkles, Check, AlertTriangle, RefreshCw, XCircle, ArrowLeft, ArrowRight, Cpu, Zap, Brain, ShieldCheck } from "lucide-react";
import { PageHeader, PageBody } from "../components/ui/PageChrome";

function AuditPage() {
  const { auditResult, loading, progress, error, setError, runDelayAnalysis, auditSession, fetchActiveSession, registerStepAction } = useAudit();
  const navigate = useNavigate();
  const [provider, setProvider] = useState("groq");
  const [executing, setExecuting] = useState(false);

  useEffect(() => {
    fetchActiveSession().catch(() => {});
  }, [fetchActiveSession]);

  useEffect(() => {
    registerStepAction({
      onPrev: () => navigate("/matches"),
      onNext: auditResult ? () => navigate("/results") : startAnalysis
    });
  });

  useEffect(() => {
    if (executing && !loading && auditResult && !error) {
      navigate("/results");
    }
  }, [executing, loading, auditResult, error, navigate]);

  const approvalSteps = [
    { name: "Planned Requirements confirmed", approved: auditSession?.planned_data_approved, link: "/upload-srs" },
    { name: "Platform Ingestion confirmed", approved: auditSession?.actual_data_approved, link: "/configuration" },
    { name: "Developer Workload confirmed", approved: auditSession?.capacity_approved, link: "/configuration" },
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
      setExecuting(true);
      await runDelayAnalysis(provider);
    } catch (err) {
      setExecuting(false);
      setError(err.response?.data?.detail || err.message || "Failed to start analysis.");
    }
  };

  return (
    <>
      <PageHeader
        title="Execute the audit."
        lede="Reconcile planned specs vs. actual deliverables into an executive AI forensic audit."
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

        {!allStepsApproved && (
          <div className="bg-amber-500/10 border border-amber-500/30 text-ink px-5 py-3.5 rounded-2xl text-sm font-medium flex items-center justify-between mb-8">
             <div className="flex items-center gap-3">
                <AlertTriangle className="size-5 text-amber-600" />
                <span>Please ensure all previous audit workflow steps (Upload SRS, Connect Platform, Normalization, and Matching) are approved before executing.</span>
             </div>
          </div>
        )}

        <div className="grid lg:grid-cols-12 gap-8 mb-12 items-start">
          {/* Left Column: Title & What You'll Get */}
          <div className="lg:col-span-7 space-y-8">
            <div className="soft-card p-8 bg-beige/40 border border-hairline">
              <h2 className="font-display text-4xl text-ink font-bold tracking-tight">
                Ready to audit {auditSession?.project_key || "Project"}.
              </h2>
              <p className="mt-2 text-subtext text-base">
                Review inputs and configure inference. Estimated runtime: ~2 minutes.
              </p>

              <div className="mt-8 pt-8 border-t border-hairline">
                <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider bg-lavender/30 text-ink border border-lavender mb-3">
                  <Sparkles className="size-3.5 text-primary" /> What You'll Get
                </div>
                <h3 className="font-display text-2xl text-ink font-bold">
                  An Executive AI Forensic Audit Report
                </h3>

                <div className="grid sm:grid-cols-2 gap-4 mt-6">
                  {[
                    { t: "AI Forensic Audit & Drift Analysis", d: "Reconciles planned SRS engineering specs against actual Jira/GitHub deliverables & time logs" },
                    { t: "Executive Waveform Timeline", d: "Cinematic modal tracking 3 stages: Delayed, On Track, and Advanced (Under Budget)" },
                    { t: "Scope & Testing Rule Reconciliation", d: "Dynamic filtering for Core Design & Development vs. Full Lifecycle (20% testing allocation)" },
                    { t: "Row-Level Root Cause Analysis (RCA)", d: "Deep-dive forensic AI intelligence, delay classification, and interactive chat per requirement" },
                    { t: "Developer & Module Velocity Metrics", d: "Granular efficiency tracking, contributor workload breakdown, and module drift analysis" },
                    { t: "Executive Synthesis & Action Roadmap", d: "Automated AI report summarizing project health, schedule risk, and remediation roadmaps" },
                  ].map((i, idx) => (
                    <div key={idx} className="rounded-2xl bg-card border border-hairline p-5 hover:border-ink/30 hover:shadow-md transition-all flex flex-col justify-between group">
                      <div className="font-display font-bold text-base text-ink group-hover:text-primary transition-colors">
                        {i.t}
                      </div>
                      <div className="text-xs text-subtext mt-2 leading-relaxed">
                        {i.d}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Right Column: AI Provider Selection & Execution Control Panel */}
          <div className="lg:col-span-5 sticky top-24">
            <div className="soft-card p-8 bg-card border border-hairline shadow-xl space-y-6">
              <div className="flex items-center gap-3 pb-5 border-b border-hairline">
                <div className="size-10 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary">
                  <Cpu className="size-5" />
                </div>
                <div>
                  <h3 className="font-display text-xl text-ink font-bold">Configure AI Engine</h3>
                  <p className="text-xs text-subtext">Select model for multi-stage forensic inference</p>
                </div>
              </div>

              <div className="space-y-3">
                <label className="text-xs font-bold uppercase tracking-wider text-ink/80 block">
                  Choose YOUR AI Engine
                </label>

                <div className="space-y-3">
                  <div 
                    onClick={() => setProvider("groq")}
                    className={`p-4 rounded-2xl border-2 cursor-pointer transition-all flex items-start gap-3.5 ${
                      provider === "groq" 
                        ? "bg-pista/20 border-pista shadow-sm" 
                        : "bg-secondary/40 border-hairline hover:border-ink/20"
                    }`}
                  >
                    <div className={`mt-0.5 size-5 rounded-full border-2 flex items-center justify-center shrink-0 ${
                      provider === "groq" ? "border-ink bg-ink text-background" : "border-subtext"
                    }`}>
                      {provider === "groq" && <Check className="size-3 stroke-[3]" />}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-sm text-ink">Groq (Llama-3 - Fast)</span>
                        <span className="text-[10px] font-bold uppercase tracking-wider bg-pista/50 text-ink px-2 py-0.5 rounded-full">
                          Ultra-Fast
                        </span>
                      </div>
                      <p className="text-xs text-subtext mt-1">
                        High-speed inference optimized for rapid schedule variance and drift detection.
                      </p>
                    </div>
                  </div>

                  <div 
                    onClick={() => setProvider("gemini")}
                    className={`p-4 rounded-2xl border-2 cursor-pointer transition-all flex items-start gap-3.5 ${
                      provider === "gemini" 
                        ? "bg-lavender/30 border-lavender shadow-sm" 
                        : "bg-secondary/40 border-hairline hover:border-ink/20"
                    }`}
                  >
                    <div className={`mt-0.5 size-5 rounded-full border-2 flex items-center justify-center shrink-0 ${
                      provider === "gemini" ? "border-ink bg-ink text-background" : "border-subtext"
                    }`}>
                      {provider === "gemini" && <Check className="size-3 stroke-[3]" />}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-sm text-ink">Google Gemini</span>
                        <span className="text-[10px] font-bold uppercase tracking-wider bg-lavender text-ink px-2 py-0.5 rounded-full">
                          Recommended
                        </span>
                      </div>
                      <p className="text-xs text-subtext mt-1">
                        State-of-the-art reasoning for complex forensic root-cause investigations and roadmaps.
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="pt-6 border-t border-hairline">
                {loading ? (
                  <div className="space-y-4 py-2">
                    <div className="w-full bg-secondary h-3 rounded-full overflow-hidden">
                      <div 
                        className="bg-ink h-full transition-all duration-300"
                        style={{ width: `${progress}%` }}
                      />
                    </div>
                    <div className="flex items-center justify-between text-sm font-medium text-ink">
                      <span className="flex items-center gap-2">
                        <RefreshCw className="size-4 animate-spin text-primary" /> Running AI calculations...
                      </span>
                      <span className="font-bold">{progress}%</span>
                    </div>
                  </div>
                ) : (
                  <button 
                    onClick={startAnalysis}
                    disabled={!allStepsApproved || loading}
                    className="w-full h-14 rounded-full bg-ink text-background font-bold text-base hover:opacity-90 transition shadow-xl inline-flex items-center justify-center gap-3 disabled:opacity-50 disabled:shadow-none"
                  >
                    <PlayCircle className="size-6" /> Execute AI Forensic Audit
                  </button>
                )}
                {!allStepsApproved && !loading && (
                  <p className="text-center text-xs text-risk mt-3">
                    Please approve previous workflow steps to enable execution.
                  </p>
                )}
              </div>
            </div>
          </div>
        </div>
      </PageBody>
    </>
  );
}

export default AuditPage;
