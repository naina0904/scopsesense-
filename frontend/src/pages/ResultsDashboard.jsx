import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import DelayAnalysisResults from "../components/DelayAnalysisResults";
import AIChatPanel from "../components/AIChatPanel";
import { useAudit } from "../context/AuditContext";
import { PageHeader, PageBody } from "../components/ui/PageChrome";
import { Loader2, HelpCircle, Sparkles, ArrowLeft, ChevronDown, ChevronUp, X, RotateCcw } from "lucide-react";

function ResultsDashboard() {
  const navigate = useNavigate();
  const [provider, setProvider] = useState("groq");
  const [openFaq, setOpenFaq] = useState(null);
  const [highlightedFaqIndex, setHighlightedFaqIndex] = useState(null);
  const { auditResult, auditSession, loading, error, fetchAuditResult, registerStepAction, showFaqs, setShowFaqs, showCopilot, setShowCopilot } = useAudit();
  
  const rawFaqs = auditResult?.faqs || auditResult?.faq_table?.items || [];
  const faqs = rawFaqs.filter((faq, idx, self) =>
    idx === self.findIndex(f => (f.question || "").trim().toLowerCase() === (faq.question || "").trim().toLowerCase())
  );

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
        title="Intelligence Report"
        lede="Executive analysis, row-level investigations, and predictive drift forecasting."
      />
      
      <PageBody>
        {showCopilot && (
          <div className="fixed inset-0 z-50 bg-ink/60 backdrop-blur-md flex items-center justify-center p-4 lg:p-8 animate-in fade-in duration-300">
            <div className="bg-card border border-hairline rounded-3xl max-w-4xl w-full max-h-[85vh] flex flex-col shadow-2xl overflow-hidden animate-in zoom-in-95 duration-300">
              <AIChatPanel 
                provider={provider} 
                sessionId={auditSession?.id}
                projectKey={auditResult?.project_key}
                onClose={() => setShowCopilot(false)}
                defaultExpanded={true}
              />
            </div>
          </div>
        )}

        <DelayAnalysisResults 
          results={auditResult} 
          onFaqClick={(idx) => {
            setHighlightedFaqIndex(idx);
            if (idx !== null) {
              setShowFaqs(true);
              if (openFaq === null) {
                setOpenFaq(idx);
              }
            }
          }}
        />
        
        {showFaqs && (
          <div className="fixed inset-0 z-50 bg-ink/60 backdrop-blur-md flex items-center justify-center p-4 lg:p-8 animate-in fade-in duration-300">
            <div className="bg-card border border-hairline rounded-3xl max-w-4xl w-full max-h-[85vh] flex flex-col shadow-2xl overflow-hidden animate-in zoom-in-95 duration-300">
              {/* Modal Header */}
              <div className="px-8 py-6 border-b border-hairline flex items-center justify-between bg-card/80 sticky top-0 z-10">
                <div className="flex items-center gap-3">
                  <div className="size-10 rounded-2xl bg-lavender/10 border border-lavender/30 flex items-center justify-center text-lavender shadow-sm">
                    <HelpCircle className="size-5" />
                  </div>
                  <div>
                     <h2 className="text-xl font-display font-bold text-ink">Frequently Asked Questions</h2>
                     <p className="text-xs text-subtext">{faqs.length} anticipated executive questions based on audit variance.</p>
                  </div>
                </div>
                <button
                  onClick={() => setShowFaqs(false)}
                  className="size-9 rounded-full bg-secondary/80 hover:bg-secondary text-subtext hover:text-ink flex items-center justify-center transition shadow-sm cursor-pointer"
                >
                  <X className="size-5" />
                </button>
              </div>

              {/* Modal Body */}
              <div className="p-8 overflow-y-auto space-y-3 flex-1 bg-secondary/10">
                {faqs.map((faq, index) => {
                  const isOpen = openFaq === index;
                  const isHighlighted = highlightedFaqIndex === index;
                  return (
                    <div 
                      key={`${faq.question}-${index}`} 
                      onClick={() => setOpenFaq(isOpen ? null : index)}
                      className={`bg-card border rounded-2xl overflow-hidden transition-all duration-300 shadow-sm cursor-pointer ${
                        isHighlighted 
                          ? "border-lavender shadow-[0_0_25px_rgba(168,85,247,0.4)] ring-2 ring-lavender/60 bg-lavender/5" 
                          : "border-hairline hover:bg-secondary/40"
                      }`}
                    >
                      <div className="w-full text-left p-5 flex items-center justify-between gap-4 hover:bg-secondary/40 transition">
                        <span className="font-semibold text-ink flex items-center gap-3 text-base">
                           <Sparkles className="size-4 text-lavender shrink-0" />
                           {faq.question}
                        </span>
                        <div className="size-8 rounded-full bg-secondary/50 flex items-center justify-center shrink-0 text-subtext shadow-2xs">
                          {isOpen ? <ChevronUp className="size-4" /> : <ChevronDown className="size-4" />}
                        </div>
                      </div>
                      {isOpen && (
                        <div 
                          onClick={(e) => e.stopPropagation()}
                          className="px-5 pb-5 pt-3 text-sm text-subtext pl-12 border-t border-hairline/50 bg-secondary/20 leading-relaxed whitespace-pre-wrap font-sans"
                        >
                          {faq.answer}
                        </div>
                      )}
                    </div>
                  );
                })}
                {!faqs.length && <p className="text-subtext italic text-center py-10">No FAQs are available for the latest audit.</p>}
              </div>

              {/* Modal Footer */}
              <div className="px-8 py-4 border-t border-hairline bg-card/80 flex justify-end">
                <button
                  onClick={() => setShowFaqs(false)}
                  className="px-6 py-2.5 rounded-full bg-ink text-background text-xs font-bold hover:opacity-90 transition shadow-sm cursor-pointer"
                >
                  Close FAQs
                </button>
              </div>
            </div>
          </div>
        )}
        
        <div id="faq-section" className="mt-16 space-y-8">
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
