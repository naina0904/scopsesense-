import { useEffect, useState } from "react";
import DelayAnalysisResults from "../components/DelayAnalysisResults";
import AIChatPanel from "../components/AIChatPanel";
import ModelSelector from "./ModelSelector";
import { useAudit } from "../context/AuditContext";
import { PageHeader, PageBody } from "../components/ui/PageChrome";
import { Download, Share2, Loader2, HelpCircle, Sparkles } from "lucide-react";

function ResultsDashboard() {
  const [provider, setProvider] = useState("groq");
  const { auditResult, auditSession, loading, error, fetchAuditResult } = useAudit();
  
  const faqs = auditResult?.faqs || auditResult?.faq_table?.items || [];

  useEffect(() => {
    if (!auditResult) {
      fetchAuditResult(auditSession?.status === "COMPLETED" ? auditSession.id : null);
    }
  }, [auditResult, auditSession, fetchAuditResult]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] space-y-4">
        <Loader2 className="size-8 text-ink animate-spin" />
        <div className="text-xl font-display text-ink">Loading audit results...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8">
         <div className="bg-rose/20 border border-rose text-ink px-4 py-3 rounded-xl text-sm font-medium">
            Error: {error}
         </div>
      </div>
    );
  }

  if (!auditResult) {
    return (
      <div className="p-8 text-center text-subtext">
         No audit result available. Run an audit first.
      </div>
    );
  }

  return (
    <>
      <PageHeader
        eyebrow={`Audit complete · ${auditResult.project_key || "Project"}`}
        title="Executive Audit Report"
        lede="A board-ready story of what was planned, what was delivered, and why the project drifted."
        primary={{ 
          label: "Export PDF", 
          icon: Download,
          onClick: () => window.print()
        }}
        secondary={{ 
          label: "Share link", 
          icon: Share2,
          onClick: () => {
            navigator.clipboard.writeText(window.location.href);
            alert("Link copied to clipboard!");
          }
        }}
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
        </div>
      </PageBody>
    </>
  );
}

export default ResultsDashboard;
