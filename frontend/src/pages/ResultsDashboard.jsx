import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import DelayAnalysisResults from "../components/DelayAnalysisResults";
import AIChatPanel from "../components/AIChatPanel";
import ModelSelector from "./ModelSelector";
import { useAudit } from "../context/AuditContext";
import { PageHeader, PageBody } from "../components/ui/PageChrome";
import { Loader2, HelpCircle, Sparkles, ArrowLeft, RotateCcw } from "lucide-react";

function ResultsDashboard() {
  const navigate = useNavigate();
  const [provider, setProvider] = useState("groq");
  const { auditResult, auditSession, loading, error, fetchAuditResult, registerStepAction } = useAudit();
  
  const faqs = auditResult?.faqs || auditResult?.faq_table?.items || [];

  useEffect(() => {
    if (!auditResult) {
      fetchAuditResult(auditSession?.status === "COMPLETED" ? auditSession.id : null);
    }
  }, [auditResult, auditSession, fetchAuditResult]);

  useEffect(() => {
    registerStepAction({
      onPrev: () => navigate("/execute")
    });
  });

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] space-y-4">
        <Loader2 className="size-8 animate-spin text-ink" />
        <p className="text-sm font-mono text-subtext">Loading audit intelligence report...</p>
      </div>
    );
  }

  if (error || !auditResult) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] space-y-4">
        <p className="text-risk font-semibold">{error || "No audit results available."}</p>
        <button 
          onClick={() => navigate("/execute")} 
          className="px-4 py-2 bg-ink text-background rounded-lg text-xs font-semibold hover:opacity-90 transition"
        >
          Back to Execution
        </button>
      </div>
    );
  }

  return (
    <>
      <PageHeader
        eyebrow={`Audit complete · ${auditResult.project_key || "Project"}`}
        title="Executive Audit Report"
        lede="A board-ready story of what was planned, what was delivered, and why the project drifted."
      />
      
      <PageBody>
        <DelayAnalysisResults results={auditResult} />
        
        <div className="mt-12 space-y-8">
          <div className="px-8 py-6">
            <h3 className="font-display text-2xl mb-1">AI Audit Copilot</h3>
            <p className="text-subtext text-sm">Chat with your audit data. Explore FAQs or dive deep with contextual AI queries.</p>
          </div>
                    <div className="lift-card p-8">
            <div className="flex items-center gap-3 mb-6 border-b border-hairline pb-4">
              <HelpCircle className="size-6 text-subtext" />
              <div>
                 <h2 className="text-xl font-display">Frequently Asked Questions</h2>
                 <p className="text-sm text-subtext">{faqs.length} anticipated questions based on audit variance.</p>
              </div>
            </div>
            <div className="grid gap-4">
              {faqs.map((faq, index) => (
                <div key={`${faq.question}-${index}`} className="bg-secondary/40 border border-hairline rounded-2xl p-5 hover:bg-secondary/60 transition">
                  <p className="font-medium text-ink flex items-start gap-2">
                     <Sparkles className="size-4 text-lavender shrink-0 mt-0.5" />
                     {faq.question}
                  </p>
                  <p className="text-sm text-subtext mt-2 pl-6">{faq.answer}</p>
                </div>
              ))}
              {!faqs.length && <p className="text-subtext italic">No FAQs are available for the latest audit.</p>}
            </div>
          </div>

          <div className="mt-8">
             <AIChatPanel
               provider={provider}
               sessionId={auditResult?.session_id}
               projectKey={auditResult?.project_key}
               platform={auditResult?.platform}
             />
          </div>

          {/* Workflow Navigation Footer */}
          <div className="flex flex-col sm:flex-row justify-between items-center p-6 border border-hairline rounded-3xl bg-card/60 backdrop-blur-sm mt-12 gap-4">
             <button
               onClick={() => navigate("/execute")}
               className="h-12 px-6 rounded-full border border-hairline bg-secondary text-ink text-sm font-medium inline-flex items-center hover:bg-secondary/80 transition gap-2 w-full sm:w-auto justify-center"
             >
               <ArrowLeft size={16} />
               <span>Back to Execute Audit</span>
             </button>

             <button
               onClick={() => navigate("/matches")}
               className="h-12 px-6 rounded-full border border-hairline bg-card text-subtext text-sm font-medium inline-flex items-center hover:text-ink hover:bg-secondary/50 transition gap-2 w-full sm:w-auto justify-center"
             >
               <RotateCcw size={15} />
               <span>Re-review Semantic Matches</span>
             </button>

             <button
               onClick={() => navigate("/upload-srs")}
               className="h-12 px-6 rounded-full bg-ink text-background text-sm font-medium inline-flex items-center hover:opacity-90 transition gap-2 shadow-sm w-full sm:w-auto justify-center"
             >
               <span>Start New Project Audit</span>
             </button>
          </div>
        </div>
      </PageBody>
    </>
  );
}

export default ResultsDashboard;
