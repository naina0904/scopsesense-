import { useEffect, useState, useMemo } from "react";
import { useAudit } from "../context/AuditContext";
import { useNavigate } from "react-router-dom";
import { CheckCircle, Save, ArrowRight, Loader2, X, Check } from "lucide-react";
import { PageHeader, PageBody } from "../components/ui/PageChrome";

function MatchApprovalPage() {
  const { auditSession, fetchActiveSession, getMatchesList, getActualFeatures, saveMatchesList, sessionLoading, error, setError } = useAudit();
  const navigate = useNavigate();

  const [matches, setMatches] = useState([]);
  const [actuals, setActuals] = useState([]);
  const [loadingMatches, setLoadingMatches] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchActiveSession().catch(() => {});
  }, [fetchActiveSession]);

  useEffect(() => {
    if (auditSession?.id) {
      setLoadingMatches(true);
      // Fetch matches and actuals concurrently
      Promise.all([getMatchesList(), getActualFeatures()])
        .then(([mRes, aRes]) => {
          if (mRes && mRes.matches) {
            setMatches(mRes.matches);
          }
          if (aRes && aRes.features) {
            setActuals(aRes.features);
          }
        })
        .catch((err) => {
          setError(err.response?.data?.detail || err.message || "Failed to load matches list.");
        })
        .finally(() => {
          setLoadingMatches(false);
        });
    }
  }, [auditSession, getMatchesList, getActualFeatures, setError]);

  const handleStatusChange = (index, status) => {
    const updated = [...matches];
    updated[index] = { ...updated[index], approval_status: status };
    setMatches(updated);
  };

  const handleLinkChange = (index, actualIdx) => {
    const updated = [...matches];
    const actIdx = parseInt(actualIdx);
    
    if (actIdx === -1) {
      // Unlink
      updated[index] = { 
        ...updated[index], 
        feature_id: -1, 
        matched_story: "Unmatched", 
        confidence_score: 0.0,
        approval_status: "REJECTED"
      };
    } else {
      const act = actuals[actIdx];
      updated[index] = { 
        ...updated[index], 
        feature_id: actIdx, 
        matched_story: act.requirement || act.name,
        confidence_score: 1.0, // Forced user link = 100% confidence
        approval_status: "APPROVED" 
      };
    }
    
    setMatches(updated);
  };

  const handleSaveAndApprove = async () => {
    try {
      setSaving(true);
      setError(null);
      // Format matches back to MatchItem schema for saving
      const payload = matches.map(m => ({
        srs_node_id: m.srs_node_id,
        feature_id: m.feature_id,
        confidence_score: m.confidence_score,
        approval_status: m.approval_status
      }));
      
      await saveMatchesList(payload);
      navigate("/execute");
    } catch (err) {
      setError(err.response?.data?.detail || err.message || "Failed to save matches checklist.");
    } finally {
      setSaving(false);
    }
  };

  const handleApproveAll = () => {
    const updated = matches.map(m => {
       if (m.confidence_score >= 0.7 && m.feature_id >= 0) {
           return { ...m, approval_status: "APPROVED" };
       }
       return m;
    });
    setMatches(updated);
  };

  const kpis = useMemo(() => {
     let auto = 0, sugg = 0, needs = 0, unmatch = 0;
     matches.forEach(m => {
        if (m.feature_id < 0) { unmatch++; return; }
        if (m.confidence_score >= 0.9) auto++;
        else if (m.confidence_score >= 0.7) sugg++;
        else needs++;
     });
     return { auto, sugg, needs, unmatch };
  }, [matches]);

  return (
    <>
      <PageHeader
        eyebrow="Step 7 · Audit workflow"
        title="Approve semantic matches."
        lede="ScopeSense proposes how each planned requirement maps to delivered work. Approve, adjust, or reject."
        primary={matches.length > 0 && !loadingMatches && !sessionLoading ? { label: "Approve all confident", onClick: handleApproveAll } : undefined}
      />

      <PageBody>
        {error && (
          <div className="bg-rose/20 border border-rose text-ink px-4 py-3 rounded-xl text-sm font-medium flex items-center justify-between">
             <span>{error}</span>
             <button onClick={() => setError(null)} className="opacity-50 hover:opacity-100">&times;</button>
          </div>
        )}

        {auditSession?.matches_approved && (
          <div className="flex items-center gap-2 bg-pista/30 border border-pista text-ink px-4 py-3 rounded-xl text-sm font-semibold w-max mb-6">
            <CheckCircle size={18} />
            <span>Matches Approved</span>
          </div>
        )}

        {loadingMatches || sessionLoading ? (
          <div className="soft-card p-12 text-center flex flex-col items-center justify-center space-y-4">
            <Loader2 className="size-8 text-ink animate-spin" />
            <div className="text-xl font-display text-ink">Generating semantic matches...</div>
            <p className="text-subtext">Mapping planned requirements to delivered platform issues via AI graph.</p>
          </div>
        ) : (
          <>
            <div className="grid lg:grid-cols-4 gap-5 mb-8">
              <KPI t="bg-pista/50" k={kpis.auto.toString()} l="Auto-matched · ≥ 90%" />
              <KPI t="bg-lavender/50" k={kpis.sugg.toString()} l="Suggested · 70-89%" />
              <KPI t="bg-warning/50" k={kpis.needs.toString()} l="Needs review · < 70%" />
              <KPI t="bg-rose/50" k={kpis.unmatch.toString()} l="Unmatched" />
            </div>

            <div className="space-y-4">
              {matches.map((item, index) => {
                let tone = "bg-card";
                if (item.approval_status === "APPROVED") tone = "bg-pista/20 border-pista/50";
                else if (item.approval_status === "REJECTED") tone = "bg-rose/10 border-rose/30";
                else if (item.confidence_score >= 0.9) tone = "bg-pista/10 border-pista/30";
                else if (item.confidence_score >= 0.7) tone = "bg-lavender/10 border-lavender/30";
                else tone = "bg-warning/10 border-warning/30";

                return (
                  <div key={index} className={`lift-card p-5 grid lg:grid-cols-12 gap-4 items-center border ${tone} transition-all`}>
                    <div className="lg:col-span-3">
                      <div className="text-[10px] uppercase tracking-wider text-subtext">Planned</div>
                      <div className="font-mono text-xs text-subtext mt-0.5">{item.module}</div>
                      <div className="font-medium mt-1 text-ink">{item.requirement}</div>
                    </div>
                    
                    <div className="lg:col-span-1 grid place-items-center">
                       <ArrowRight className="size-5 text-subtext" />
                    </div>
                    
                    <div className="lg:col-span-4">
                      <div className="text-[10px] uppercase tracking-wider text-subtext">Delivered</div>
                      {item.feature_id >= 0 ? (
                         <div className="font-medium mt-1.5 text-ink">{item.matched_story}</div>
                      ) : (
                         <div className="font-medium mt-1.5 text-subtext italic">Unmatched</div>
                      )}
                      <div className="mt-2.5">
                        <select
                          value={item.feature_id}
                          onChange={(e) => handleLinkChange(index, e.target.value)}
                          className="w-full bg-background border border-hairline rounded-lg p-2 text-xs text-ink focus:outline-none focus:ring-1 focus:ring-ring"
                        >
                          <option value={item.feature_id}>{item.matched_story}</option>
                          <option value="-1">-- Unlink (Unmatched) --</option>
                          {actuals.map((act, actIdx) => (
                            <option key={actIdx} value={actIdx}>{act.requirement || act.name}</option>
                          ))}
                        </select>
                      </div>
                    </div>
                    
                    <div className="lg:col-span-1 text-center">
                      {item.feature_id >= 0 ? (
                        <>
                          <div className="font-display text-2xl text-ink">{(item.confidence_score * 100).toFixed(0)}%</div>
                          <div className="text-[10px] text-subtext">confidence</div>
                        </>
                      ) : (
                         <div className="font-display text-xl text-subtext">-</div>
                      )}
                    </div>
                    
                    <div className="lg:col-span-3 flex flex-wrap gap-2 justify-end items-center">
                      <span className={`chip hidden sm:inline-block ${
                          item.approval_status === "APPROVED" ? "bg-pista text-ink" : 
                          item.approval_status === "REJECTED" ? "bg-rose/40 text-risk" : 
                          "bg-warning/40 text-ink"
                      }`}>
                         {item.approval_status === "PENDING" ? "REVIEW" : item.approval_status}
                      </span>
                      
                      <button 
                        onClick={() => handleStatusChange(index, "REJECTED")} 
                        className={`size-11 rounded-full border border-hairline grid place-items-center transition ${item.approval_status === "REJECTED" ? "bg-rose/30 text-risk border-rose/50" : "bg-card hover:bg-secondary text-subtext"}`}
                        title="Reject Link"
                      >
                         <X className="size-4" />
                      </button>
                      
                      <button 
                        onClick={() => handleStatusChange(index, "APPROVED")} 
                        className={`h-11 px-4 sm:px-5 rounded-full text-sm font-medium inline-flex items-center gap-2 transition ${item.approval_status === "APPROVED" ? "bg-ink text-background" : "bg-card border border-hairline hover:bg-secondary text-ink"}`}
                        title="Approve Link"
                      >
                         <Check className="size-4" /> <span className="hidden sm:inline">Approve</span>
                      </button>
                    </div>
                  </div>
                );
              })}
              
              {matches.length === 0 && (
                <div className="p-8 text-center text-subtext border border-hairline rounded-2xl bg-card">
                   No matches found. Ensure the dataset is merged.
                </div>
              )}
            </div>

            <div className="flex justify-end mt-8">
               <button
                  onClick={handleSaveAndApprove}
                  disabled={saving}
                  className="h-12 px-6 rounded-full bg-ink text-background text-sm font-medium inline-flex items-center hover:opacity-90 transition disabled:opacity-50"
               >
                  {saving ? "Saving..." : "Save Checklist & Continue to Audit →"}
               </button>
            </div>
          </>
        )}
      </PageBody>
    </>
  );
}

function KPI({ t, k, l }) {
  return (
    <div className={`rounded-3xl p-6 border border-hairline ${t}`}>
      <div className="font-display text-4xl text-ink">{k}</div>
      <div className="text-xs text-subtext mt-1">{l}</div>
    </div>
  );
}

export default MatchApprovalPage;
