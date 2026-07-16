import { useEffect, useState } from "react";
import { useAudit } from "../context/AuditContext";
import { useNavigate } from "react-router-dom";
import { CheckCircle, Save, ArrowRight, Loader2, ArrowLeft } from "lucide-react";
import { PageHeader, PageBody } from "../components/ui/PageChrome";
import { StageGuideCard } from "../components/ui/StageGuideCard";

function NormalizationPage() {
  const { auditSession, fetchActiveSession, getNormalizationData, saveNormalization, sessionLoading, error, setError, registerStepAction, openHelp } = useAudit();
  const navigate = useNavigate();

  const [normData, setNormData] = useState([]);
  const [loadingNorm, setLoadingNorm] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    registerStepAction({
      onPrev: () => navigate("/configuration"),
      onNext: normData.length > 0 ? handleSaveAndApprove : () => navigate("/matches")
    });
  });

  useEffect(() => {
    fetchActiveSession().catch(() => {});
  }, [fetchActiveSession]);

  const isTestingRow = (row) => {
    const mod = (row?.module || "").toLowerCase().trim();
    const req = (row?.requirement || "").toLowerCase().trim();
    return mod === "project phases" || req.includes("internal testing");
  };

  useEffect(() => {
    if (auditSession?.id) {
      setLoadingNorm(true);
      getNormalizationData()
        .then((res) => {
          if (res && res.normalization_data) {
            const scopeMode = localStorage.getItem("auditScopeMode") || "full_lifecycle";
            const processedData = res.normalization_data.map(item => {
              if (scopeMode === "core_dev" && isTestingRow(item)) {
                const planned = 0.0;
                const actual = parseFloat(item.actual_hours) || 0.0;
                let reqName = item.requirement || "";
                if (!reqName.startsWith("[Excluded Phase]")) {
                  reqName = "[Excluded Phase] " + reqName.replace(/^\[(Drift|Excluded Phase)\]\s*/i, "");
                }
                return {
                  ...item,
                  requirement: reqName,
                  planned_hours: planned,
                  hours_remaining: planned - actual
                };
              }
              return item;
            });
            setNormData(processedData);
          }
        })
        .catch((err) => {
          const detail = err.response?.data?.detail;
          setError(typeof detail === 'string' ? detail : (detail ? JSON.stringify(detail) : err.message || "Failed to load normalization data."));
        })
        .finally(() => {
          setLoadingNorm(false);
        });
    }
  }, [auditSession, getNormalizationData, setError]);

  const handleFieldChange = (index, field, value) => {
    const updated = [...normData];
    const row = { ...updated[index], [field]: value };
    
    // Recalculate hours_remaining if hours change
    if (field === "planned_hours" || field === "actual_hours") {
      const planned = parseFloat(row.planned_hours) || 0.0;
      const actual = parseFloat(row.actual_hours) || 0.0;
      row.hours_remaining = planned - actual;
    }
    
    updated[index] = row;
    setNormData(updated);
  };

  const handleSaveAndApprove = async () => {
    try {
      setSaving(true);
      setError(null);
      await saveNormalization(normData);
      navigate("/matches");
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : (detail ? JSON.stringify(detail) : err.message || "Failed to save normalization data."));
    } finally {
      setSaving(false);
    }
  };

  return (
    <>
      <PageHeader
        title="Merged Normalization Dataset."
        lede="Review the consolidated planned requirements and actual development hours before committing to calculations."
        primary={normData.length > 0 && !loadingNorm && !sessionLoading ? { label: saving ? "Saving..." : "Save & Confirm Dataset", onClick: handleSaveAndApprove } : undefined}
      />
      
      <PageBody>
        {error && (
          <div className="bg-rose/20 border border-rose text-ink px-4 py-3 rounded-xl text-sm font-medium flex items-center justify-between">
             <span>{error}</span>
             <button onClick={() => setError(null)} className="opacity-50 hover:opacity-100">&times;</button>
          </div>
        )}

        {auditSession?.normalized_data_approved && (
          <div className="flex items-center gap-2 bg-pista/30 border border-pista text-ink px-4 py-3 rounded-xl text-sm font-semibold w-max mb-6">
            <CheckCircle size={18} />
            <span>Dataset Approved</span>
          </div>
        )}

        {loadingNorm || sessionLoading ? (
          <div className="soft-card p-12 text-center flex flex-col items-center justify-center space-y-4">
            <Loader2 className="size-8 text-ink animate-spin" />
            <div className="text-xl font-display text-ink">Merging and loading dataset...</div>
            <p className="text-subtext">Translating planned vs actual platforms into a shared semantic structure.</p>
          </div>
        ) : (
          <div className="soft-card overflow-hidden">
            <div className="px-6 py-5 border-b border-hairline flex items-center justify-between">
              <div>
                <h3 className="font-display text-2xl">Merged Canonical Audit Dataset</h3>
                <p className="text-subtext text-sm flex items-center gap-2 mt-1">
                  Make direct overrides to hours, status, or assignees.
                  {(localStorage.getItem("auditScopeMode") === "core_dev") && (
                    <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-primary/10 text-primary font-bold text-[11px] border border-primary/20">
                      ⚡ Core Dev Scope Active: QA Testing phases excluded from baseline
                    </span>
                  )}
                </p>
              </div>
            </div>

            <div className="overflow-x-auto">
              <div className="min-w-[800px]">
                <div className="grid grid-cols-12 px-6 py-3 text-[11px] uppercase tracking-wider text-subtext bg-beige/40 border-b border-hairline">
                  <div className="col-span-2">Module</div>
                  <div className="col-span-5">Requirement</div>
                  <div className="col-span-2 text-center">Planned Hours</div>
                  <div className="col-span-2 text-center">Actual Hours</div>
                  <div className="col-span-1 text-center">Remaining</div>
                </div>
                
                <div className="divide-y divide-hairline">
                  {normData.map((item, index) => {
                    const isDrift = item.requirement?.startsWith("[Drift]");
                    const isExcluded = item.requirement?.startsWith("[Excluded Phase]");
                    return (
                      <div key={index} className="grid grid-cols-12 px-6 py-3 items-center hover:bg-secondary/50 transition gap-4">
                        <div className="col-span-2">
                           <input
                            type="text"
                            value={item.module || ""}
                            onChange={(e) => handleFieldChange(index, "module", e.target.value)}
                            className="bg-card border border-hairline rounded-lg px-2 py-1.5 text-xs text-ink w-full focus:outline-none focus:ring-1 focus:ring-ring"
                          />
                        </div>
                        <div className="col-span-5">
                          <input
                            type="text"
                            value={item.requirement || ""}
                            onChange={(e) => handleFieldChange(index, "requirement", e.target.value)}
                            className={`bg-card border border-hairline rounded-lg px-2 py-1.5 text-xs font-medium w-full focus:outline-none focus:ring-1 focus:ring-ring ${isDrift ? "text-risk" : isExcluded ? "text-subtext italic" : "text-ink"}`}
                          />
                        </div>
                        <div className="col-span-2">
                          <input
                            type="number"
                            step="0.5"
                            value={item.planned_hours || 0}
                            onChange={(e) => handleFieldChange(index, "planned_hours", parseFloat(e.target.value) || 0)}
                            className="bg-card border border-hairline rounded-lg px-2 py-1.5 text-xs text-ink w-full text-center focus:outline-none focus:ring-1 focus:ring-ring disabled:opacity-50 disabled:bg-secondary"
                            disabled={isDrift || isExcluded}
                          />
                        </div>
                        <div className="col-span-2">
                          <input
                            type="number"
                            step="0.5"
                            value={item.actual_hours || 0}
                            onChange={(e) => handleFieldChange(index, "actual_hours", parseFloat(e.target.value) || 0)}
                            className="bg-card border border-hairline rounded-lg px-2 py-1.5 text-xs text-ink w-full text-center focus:outline-none focus:ring-1 focus:ring-ring"
                          />
                        </div>
                        <div className="col-span-1 text-center font-medium text-sm">
                          {item.hours_remaining !== undefined ? (
                            <span className={item.hours_remaining < 0 ? "text-risk" : "text-success"}>
                              {item.hours_remaining > 0 ? "+" : ""}{item.hours_remaining}
                            </span>
                          ) : ''}
                        </div>
                      </div>
                    );
                  })}
                  {normData.length === 0 && (
                     <div className="p-12 text-center text-subtext space-y-4">
                       <p className="text-xl font-bold text-ink">No normalized data to display.</p>
                       <p className="text-sm text-subtext">Please ensure Table 1 and Table 2 are approved before normalizing.</p>
                       <StageGuideCard
                         sectionId="stage-4-normalization"
                         title="📖 Complete Stage 4 Guide & Task Normalization Walkthrough"
                         description="See how commits, PRs, and tickets are standardized into the UnifiedTaskSchema."
                       />
                     </div>
                  )}
                </div>
              </div>
            </div>

          </div>
        )}
      </PageBody>
    </>
  );
}

export default NormalizationPage;
