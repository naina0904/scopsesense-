import { useEffect, useState } from "react";
import { useSRS } from "../context/SRSContext";
import { useAudit } from "../context/AuditContext";
import { useNavigate } from "react-router-dom";
import { UploadCloud, CheckCircle, Save, Plus, Trash2, ArrowUpRight, Sparkles, ShieldCheck, FileText, ArrowRight, ChevronDown, ChevronRight } from "lucide-react";
import { PageHeader, PageBody } from "../components/ui/PageChrome";
import { ScopeBadge } from "../components/ui/ScopeBadge";
import { StageGuideCard } from "../components/ui/StageGuideCard";

function SRSUploadPage() {
  const { setSRSFile, setExtractionConfirmed } = useSRS();
  const { auditSession, fetchActiveSession, uploadSRSFile, getPlannedFeatures, savePlannedData, sessionLoading, error, setError, registerStepAction, openHelp } = useAudit();
  const navigate = useNavigate();

  const [features, setFeatures] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [fileName, setFileName] = useState("");
  const [showTablesModal, setShowTablesModal] = useState(false);
  const [activeTab, setActiveTab] = useState("table1");
  const [projectDevelopers, setProjectDevelopers] = useState([]);
  const [showScopeModal, setShowScopeModal] = useState(false);
  const [selectedScope, setSelectedScope] = useState(() => localStorage.getItem("auditScopeMode") || "full_lifecycle");

  useEffect(() => {
    fetchActiveSession().catch(() => {});
  }, [fetchActiveSession]);

  useEffect(() => {
    if (auditSession?.srs_result_id) {
      getPlannedFeatures()
        .then((res) => {
          if (res && res.features) {
            setFeatures(res.features);
            if (res.project_developers) {
              setProjectDevelopers(res.project_developers);
            }
          }
        })
        .catch(() => {});
    }
  }, [auditSession, getPlannedFeatures]);

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setFileName(file.name);
    setSRSFile(file);
    setError(null);

    try {
      setUploading(true);
      const res = await uploadSRSFile(file);
      if (res && res.features) {
        setFeatures(res.features);
        if (res.project_developers) {
          setProjectDevelopers(res.project_developers);
        }
        setShowTablesModal(true);
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message || "Failed to upload and parse SRS file.");
    } finally {
      setUploading(false);
    }
  };

  const handleFieldChange = (index, field, value) => {
    const updated = [...features];
    updated[index] = { ...updated[index], [field]: value };
    setFeatures(updated);
  };

  const isIgnoredRow = () => false;

  const isPhaseRow = (reqName, modName) => {
    const norm = (reqName || "").toLowerCase().trim();
    return modName === "Project Phases" || ["internal testing", "client testing", "deployment", "testing", "qa"].some(p => norm.includes(p));
  };
  const isSummaryHeader = (reqName) => {
    const norm = (reqName || "").toLowerCase().trim();
    return ["design and development", "design and deployment", "total estimated hours", "total"].includes(norm);
  };

  const addFeatureRow = () => {
    setFeatures([
      ...features,
      {
        module: "General",
        requirement: `New Feature ${features.length + 1}`,
        planned_hours: 0.0,
        assigned_developer: "S2 (Mid-Level Developer)",
        priority: "Medium"
      }
    ]);
  };

  const addPhaseRow = () => {
    setFeatures([
      ...features,
      {
        module: "Project Phases",
        requirement: `New Phase`,
        planned_hours: 0.0,
        assigned_developer: "S3 (Senior Developer)",
        priority: "Medium"
      }
    ]);
  };

  const deleteRow = (index) => {
    const updated = features.filter((_, i) => i !== index);
    setFeatures(updated);
  };

  const executeSaveAndNavigate = async () => {
    try {
      setSaving(true);
      setError(null);
      const isDevOnly = selectedScope === "core_dev" || localStorage.getItem("auditScopeMode") === "core_dev";
      const cleanedFeatures = features
        .filter(f => !isIgnoredRow(f.requirement) && (!isDevOnly || !isPhaseRow(f.requirement, f.module)))
        .map(({ dependencies, ...rest }) => rest);
      await savePlannedData(cleanedFeatures);
      setExtractionConfirmed(true);
      navigate("/configuration");
    } catch (err) {
      setError(err.response?.data?.detail || err.message || "Failed to save planned features.");
    } finally {
      setSaving(false);
    }
  };

  const handleSaveAndApprove = async () => {
    if (!showScopeModal) {
      setShowScopeModal(true);
      return;
    }
    await executeSaveAndNavigate();
  };

  useEffect(() => {
    registerStepAction({
      onNext: async () => {
        if (features.length > 0) {
          setShowScopeModal(true);
        } else {
          navigate("/configuration");
        }
      }
    });
  });

  return (
    <>
      <PageHeader
        title="Upload SRS & Review Requirements."
        primary={features.length > 0 ? { label: saving ? "Saving..." : "Confirm & continue", onClick: handleSaveAndApprove } : undefined}
      />
      <PageBody>
        {error && (
          <div className="bg-rose/20 border border-rose text-ink px-4 py-3 rounded-xl text-sm font-medium flex items-center justify-between">
            <span>{error}</span>
            <button onClick={() => setError(null)} className="opacity-50 hover:opacity-100">&times;</button>
          </div>
        )}

        {auditSession?.planned_data_approved && (
          <div className="flex items-center gap-2 bg-pista/30 border border-pista text-ink px-4 py-3 rounded-xl text-sm font-semibold mb-6">
            <CheckCircle size={18} />
            <span>Planned Data Approved</span>
          </div>
        )}

        <div className="grid lg:grid-cols-3 gap-5">
          <div className="lg:col-span-2 lift-card p-10">
            <div className="border-2 border-dashed border-hairline rounded-3xl bg-beige/40 p-14 text-center">
              <div className="size-16 rounded-2xl bg-card border border-hairline grid place-items-center mx-auto">
                <UploadCloud className="size-7 text-ink" />
              </div>
              <h2 className="mt-6 font-display text-3xl">Drop your SRS here</h2>
              <p className="mt-2 text-subtext">PDF, DOCX, XLSX, TXT or Markdown · Max 10MB</p>
              <div className="mt-8 flex justify-center gap-3 relative">
                <label className="cursor-pointer h-12 px-6 rounded-full bg-ink text-background text-sm font-medium hover:opacity-90 transition flex items-center justify-center">
                  {uploading ? "Extracting features..." : "Upload document"}
                  <input 
                      type="file" 
                      accept=".pdf,.docx,.xlsx,.txt,.md" 
                      onChange={handleFileChange} 
                      className="hidden" 
                      disabled={uploading || sessionLoading} 
                  />
                </label>
              </div>
              {fileName && <p className="mt-4 text-xs font-mono text-subtext">Uploaded: {fileName}</p>}
            </div>
          </div>

          <div className="space-y-5">
            <div className="soft-card p-6 bg-lavender/40">
               <div className="flex items-center gap-2 text-xs text-ink/60"><Sparkles className="size-3.5" /> AI parsing</div>
               <h4 className="mt-2 font-display text-xl">Smart extraction</h4>
               <p className="text-sm text-ink/70 mt-2">We identify requirements, owners, dependencies and acceptance criteria automatically.</p>
               <button
                 type="button"
                 onClick={() => openHelp("stage-1-upload-srs")}
                 className="mt-4 px-4 py-2.5 rounded-xl bg-info/15 text-info font-bold text-sm inline-flex items-center gap-2 hover:bg-info/25 transition-colors cursor-pointer shadow-xs"
               >
                 <span>📖 View Complete Stage Guide & How This Works →</span>
               </button>
             </div>
            <div className="soft-card p-6">
              <div className="flex items-center gap-2 text-xs text-subtext"><ShieldCheck className="size-3.5" /> Privacy</div>
              <h4 className="mt-2 font-display text-xl">Your data stays yours</h4>
              <p className="text-sm text-subtext mt-2">Documents are encrypted at rest, processed in your region, and never used for model training.</p>
            </div>
          </div>
        </div>

        <StageGuideCard
          sectionId="stage-1-upload-srs"
          title="📖 Complete Stage 1 Guide & Requirements Parsing Walkthrough"
          description="Click to open the interactive manual, see how AI converts unstructured text into tasks, and understand budget estimations."
        />

        {features.length > 0 && (() => {
          const table1Items = features
            .map((item, masterIndex) => ({ ...item, masterIndex }))
            .filter(item => !isPhaseRow(item.requirement, item.module) && !isSummaryHeader(item.requirement) && !isIgnoredRow(item.requirement));

          const table2Items = features
            .map((item, masterIndex) => ({ ...item, masterIndex }))
            .filter(item => isPhaseRow(item.requirement, item.module) && !isIgnoredRow(item.requirement));

          const table1TotalHours = table1Items.reduce((acc, curr) => acc + (parseFloat(curr.planned_hours) || 0), 0);
          const table2TotalHours = table2Items.reduce((acc, curr) => acc + (parseFloat(curr.planned_hours) || 0), 0);
          const uniqueDevelopers = Array.from(new Set([
            "S1 (Junior Developer)",
            "S2 (Mid-Level Developer)",
            "S3 (Senior Developer)",
            ...projectDevelopers,
            ...features.map(f => f.assigned_developer).filter(d => d && d !== "Unassigned")
          ]));

          return (
            <>
              {/* Clean Summary Banner instead of huge scrolling tables */}
              <div className="mt-8 soft-card p-6 bg-card border border-hairline flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6 shadow-md bg-gradient-to-r from-card to-lavender/10">
                <div className="flex items-center gap-4">
                  <div className="size-14 rounded-2xl bg-primary/10 border border-primary/20 text-primary grid place-items-center font-display text-2xl font-bold shadow-sm shrink-0">
                    <FileText className="size-7" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="font-display text-xl font-bold text-ink">SRS Requirements Parsed Successfully</h3>
                      <span className="px-2.5 py-0.5 rounded-full bg-success/20 text-success text-xs font-bold border border-success/30 flex items-center gap-1">
                        <CheckCircle size={12} /> Ready
                      </span>
                    </div>
                    <p className="text-subtext text-xs mt-1">
                      {table1Items.length} Core Dev Features ({table1TotalHours.toFixed(1)} hrs) · {table2Items.length} QA & Testing Phases ({table2TotalHours.toFixed(1)} hrs) · <span className="font-semibold text-ink">Total: {(table1TotalHours + table2TotalHours).toFixed(1)} hrs</span>
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3 w-full sm:w-auto justify-end">
                  <button
                    onClick={() => setShowTablesModal(true)}
                    className="h-11 px-6 rounded-full border border-hairline bg-card hover:bg-secondary text-ink font-semibold text-sm transition flex items-center gap-2 shadow-sm cursor-pointer"
                  >
                    <Sparkles className="size-4 text-primary" />
                    <span>Review & Edit Tables</span>
                    <ArrowUpRight className="size-4" />
                  </button>
                  <button
                    onClick={handleSaveAndApprove}
                    disabled={saving}
                    className="h-11 px-6 rounded-full bg-ink text-background hover:opacity-90 font-bold text-sm transition flex items-center gap-2 shadow-sm cursor-pointer"
                  >
                    <span>{saving ? "Saving..." : "Confirm & continue"}</span>
                    <ArrowRight className="size-4" />
                  </button>
                </div>
              </div>

              {/* Cinematic Pop-Up Slider Modal with Blurred Background */}
              {showTablesModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink/60 backdrop-blur-md p-4 sm:p-6 md:p-10 animate-in fade-in duration-200">
                  <div className="bg-background border border-hairline rounded-3xl w-full max-w-6xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
                    {/* Modal Header */}
                    <div className="px-8 py-5 border-b border-hairline flex items-center justify-between bg-card/50">
                      <div>
                        <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-primary">
                          <Sparkles className="size-4" /> AI Extraction Review · Cinematic Slider Workspace
                        </div>
                        <h3 className="font-display text-2xl font-bold text-ink mt-1">Extracted SRS Requirements & Project Phases</h3>
                      </div>
                      <div className="flex items-center gap-3">
                        <div className="hidden sm:flex bg-secondary p-1 rounded-full border border-hairline">
                          <button
                            onClick={() => setActiveTab("table1")}
                            className={`px-4 py-1.5 rounded-full text-xs font-bold transition flex items-center gap-2 cursor-pointer ${
                              activeTab === "table1" ? "bg-ink text-background shadow-sm" : "text-subtext hover:text-ink"
                            }`}
                          >
                            <span>Table 1: Design & Deployment</span>
                            <span className={`px-1.5 py-0.5 rounded-full text-[10px] ${activeTab === "table1" ? "bg-background/20 text-background" : "bg-card text-ink"}`}>
                              {table1Items.length}
                            </span>
                          </button>
                          <button
                            onClick={() => setActiveTab("table2")}
                            className={`px-4 py-1.5 rounded-full text-xs font-bold transition flex items-center gap-2 cursor-pointer ${
                              activeTab === "table2" ? "bg-ink text-background shadow-sm" : "text-subtext hover:text-ink"
                            }`}
                          >
                            <span>Table 2: Project Phases</span>
                            <span className={`px-1.5 py-0.5 rounded-full text-[10px] ${activeTab === "table2" ? "bg-background/20 text-background" : "bg-card text-ink"}`}>
                              {table2Items.length}
                            </span>
                          </button>
                        </div>
                        <button 
                          onClick={() => setShowTablesModal(false)}
                          className="size-10 rounded-full border border-hairline bg-card hover:bg-secondary grid place-items-center text-subtext hover:text-ink transition text-lg font-bold cursor-pointer"
                          title="Close Modal"
                        >
                          &times;
                        </button>
                      </div>
                    </div>

                    {/* Mobile Tab Switcher */}
                    <div className="sm:hidden px-6 py-3 border-b border-hairline bg-secondary flex gap-2">
                      <button
                        onClick={() => setActiveTab("table1")}
                        className={`flex-1 py-2 rounded-xl text-xs font-bold transition cursor-pointer ${
                          activeTab === "table1" ? "bg-ink text-background shadow-sm" : "bg-card text-subtext"
                        }`}
                      >
                        Table 1 ({table1Items.length})
                      </button>
                      <button
                        onClick={() => setActiveTab("table2")}
                        className={`flex-1 py-2 rounded-xl text-xs font-bold transition cursor-pointer ${
                          activeTab === "table2" ? "bg-ink text-background shadow-sm" : "bg-card text-subtext"
                        }`}
                      >
                        Table 2 ({table2Items.length})
                      </button>
                    </div>

                    {/* Modal Body / Slider */}
                    <div className="flex-1 overflow-y-auto p-6 sm:p-8 bg-background/50">
                      {activeTab === "table1" ? (
                        /* Table 1 Content */
                        <div className="soft-card overflow-hidden border border-hairline bg-card shadow-sm">
                          <div className="flex justify-between items-center px-6 py-4 bg-lavender/25 border-b border-hairline border-l-4 border-l-primary">
                            <div>
                              <h3 className="font-display text-xl font-bold text-ink">Table 1: Design and Deployment</h3>
                              <p className="text-subtext text-xs mt-0.5">Core software feature requirements parsed from SRS ({table1Items.length} Features)</p>
                            </div>
                            <div className="flex items-center gap-4">
                              <div className="px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-primary text-xs font-mono font-semibold">
                                TOTAL ESTIMATED HOURS: {table1TotalHours.toFixed(1)} hrs
                              </div>
                              <button
                                onClick={addFeatureRow}
                                className="h-8 px-3 rounded-full border border-hairline bg-card text-xs font-medium hover:bg-secondary transition flex items-center gap-1.5 shadow-sm cursor-pointer"
                              >
                                <Plus size={14} /> Add Feature
                              </button>
                            </div>
                          </div>

                          <div className="grid grid-cols-12 px-6 py-2.5 text-[11px] uppercase tracking-wider text-subtext bg-beige/40 border-b border-hairline">
                            <div className="col-span-2">Module / Epic</div>
                            <div className="col-span-3">Requirement</div>
                            <div className="col-span-3">Owner</div>
                            <div className="col-span-2">Priority</div>
                            <div className="col-span-1 text-center">Hours</div>
                            <div className="col-span-1 text-right">Actions</div>
                          </div>
                          
                          <div className="divide-y divide-hairline">
                            {table1Items.map((feature) => (
                              <div key={feature.masterIndex} className="grid grid-cols-12 px-6 py-2.5 items-center hover:bg-secondary/40 transition gap-4">
                                <div className="col-span-2">
                                  <input
                                    type="text"
                                    value={feature.module || ""}
                                    onChange={(e) => handleFieldChange(feature.masterIndex, "module", e.target.value)}
                                    className="bg-card border border-hairline rounded px-2 py-1 text-xs text-ink w-full focus:outline-none focus:ring-1 focus:ring-primary"
                                  />
                                </div>
                                <div className="col-span-3">
                                  <input
                                    type="text"
                                    value={feature.requirement || ""}
                                    onChange={(e) => handleFieldChange(feature.masterIndex, "requirement", e.target.value)}
                                    className="bg-card border border-hairline rounded px-2 py-1 text-xs font-medium text-ink w-full focus:outline-none focus:ring-1 focus:ring-primary"
                                  />
                                </div>
                                <div className="col-span-3">
                                  <select
                                    value={feature.assigned_developer || "Unassigned"}
                                    onChange={(e) => handleFieldChange(feature.masterIndex, "assigned_developer", e.target.value)}
                                    className="bg-card border border-hairline rounded pl-2.5 pr-7 py-1 text-xs text-ink w-full focus:outline-none focus:ring-1 focus:ring-primary truncate cursor-pointer shadow-2xs"
                                  >
                                    <option value="Unassigned">Unassigned</option>
                                    {uniqueDevelopers.map((dev, idx) => (
                                      <option key={idx} value={dev}>{dev}</option>
                                    ))}
                                  </select>
                                </div>
                                <div className="col-span-2">
                                  <select
                                    value={feature.priority || "Medium"}
                                    onChange={(e) => handleFieldChange(feature.masterIndex, "priority", e.target.value)}
                                    className="bg-card border border-hairline rounded pl-2.5 pr-7 py-1 text-xs text-ink w-full focus:outline-none focus:ring-1 focus:ring-primary truncate cursor-pointer shadow-2xs"
                                  >
                                    <option value="High">High</option>
                                    <option value="Medium">Medium</option>
                                    <option value="Low">Low</option>
                                  </select>
                                </div>
                                <div className="col-span-1">
                                  <input
                                    type="number"
                                    step="0.5"
                                    value={feature.planned_hours || 0}
                                    onChange={(e) => handleFieldChange(feature.masterIndex, "planned_hours", parseFloat(e.target.value) || 0)}
                                    className="bg-card border border-hairline rounded px-2 py-1 text-xs text-ink w-full focus:outline-none focus:ring-1 focus:ring-primary text-center font-mono"
                                  />
                                </div>
                                <div className="col-span-1 text-right">
                                  <button
                                    onClick={() => deleteRow(feature.masterIndex)}
                                    className="text-risk hover:text-red-700 p-1 rounded hover:bg-rose/30 transition cursor-pointer"
                                  >
                                    <Trash2 size={15} />
                                  </button>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      ) : (
                        /* Table 2 Content */
                        <div className="soft-card overflow-hidden border border-hairline bg-card shadow-sm">
                          <div className="flex justify-between items-center px-6 py-4 bg-lavender/25 border-b border-hairline border-l-4 border-l-primary">
                            <div>
                              <h3 className="font-display text-xl font-bold text-ink">Table 2: Project Phases</h3>
                              <p className="text-subtext text-xs mt-0.5">Internal testing, client testing, and deployment schedule ({table2Items.length} Phases)</p>
                            </div>
                            <div className="flex items-center gap-4">
                              <div className="px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-primary font-mono text-xs font-semibold">
                                TOTAL HOURS: {table2TotalHours.toFixed(1)} hrs
                              </div>
                              <button
                                onClick={addPhaseRow}
                                className="h-8 px-3 rounded-full border border-hairline bg-card text-xs font-medium hover:bg-secondary transition flex items-center gap-1.5 shadow-sm cursor-pointer"
                              >
                                <Plus size={14} /> Add Phase
                              </button>
                            </div>
                          </div>

                          <div className="grid grid-cols-12 px-6 py-2.5 text-[11px] uppercase tracking-wider text-subtext bg-beige/40 border-b border-hairline">
                            <div className="col-span-5">Requirement (Phase Name)</div>
                            <div className="col-span-4">Owner (Assigned Developer)</div>
                            <div className="col-span-2 text-center">Estimated Hours</div>
                            <div className="col-span-1 text-right">Actions</div>
                          </div>
                          
                          <div className="divide-y divide-hairline">
                            {table2Items.map((phase) => (
                              <div key={phase.masterIndex} className="grid grid-cols-12 px-6 py-3 items-center hover:bg-secondary/40 transition gap-4">
                                <div className="col-span-5">
                                  <input
                                    type="text"
                                    value={phase.requirement || ""}
                                    onChange={(e) => handleFieldChange(phase.masterIndex, "requirement", e.target.value)}
                                    className="bg-card border border-hairline rounded px-3 py-1.5 text-xs font-medium text-ink w-full focus:outline-none focus:ring-1 focus:ring-primary"
                                  />
                                </div>
                                <div className="col-span-4">
                                  <select
                                    value={phase.assigned_developer || "Unassigned"}
                                    onChange={(e) => handleFieldChange(phase.masterIndex, "assigned_developer", e.target.value)}
                                    className="bg-card border border-hairline rounded pl-3 pr-7 py-1.5 text-xs text-ink w-full focus:outline-none focus:ring-1 focus:ring-primary truncate cursor-pointer shadow-2xs"
                                  >
                                    <option value="Unassigned">Unassigned</option>
                                    {uniqueDevelopers.map((dev, idx) => (
                                      <option key={idx} value={dev}>{dev}</option>
                                    ))}
                                  </select>
                                </div>
                                <div className="col-span-2">
                                  <input
                                    type="number"
                                    step="0.5"
                                    value={phase.planned_hours || 0}
                                    onChange={(e) => handleFieldChange(phase.masterIndex, "planned_hours", parseFloat(e.target.value) || 0)}
                                    className="bg-card border border-hairline rounded px-3 py-1.5 text-xs text-ink w-full focus:outline-none focus:ring-1 focus:ring-primary text-center font-mono font-semibold"
                                  />
                                </div>
                                <div className="col-span-1 text-right">
                                  <button
                                    onClick={() => deleteRow(phase.masterIndex)}
                                    className="text-risk hover:text-red-700 p-1.5 rounded hover:bg-rose/30 transition cursor-pointer"
                                  >
                                    <Trash2 size={16} />
                                  </button>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Modal Footer */}
                    <div className="px-8 py-4 border-t border-hairline bg-card flex items-center justify-between">
                      <div className="text-xs text-subtext">
                        Make any inline edits above. Changes are saved automatically to your workspace.
                      </div>
                      <div className="flex items-center gap-3">
                        <button
                          onClick={() => setShowTablesModal(false)}
                          className="h-10 px-5 rounded-full border border-hairline bg-card hover:bg-secondary text-ink font-semibold text-xs transition cursor-pointer"
                        >
                          Close & Review Summary
                        </button>
                        <button
                          onClick={() => { setShowTablesModal(false); handleSaveAndApprove(); }}
                          disabled={saving}
                          className="h-10 px-6 rounded-full bg-ink text-background hover:opacity-90 font-bold text-xs transition flex items-center gap-2 shadow-sm cursor-pointer"
                        >
                          <span>{saving ? "Saving..." : "Confirm & continue"}</span>
                          <ArrowRight size={14} />
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </>
          );
        })()}

        {showScopeModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink/40 backdrop-blur-sm p-4">
            <div className="bg-card border border-hairline rounded-3xl p-8 max-w-xl w-full shadow-2xl space-y-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-primary">
                  <Sparkles className="size-4" /> Audit Scope Configuration
                </div>
                <button onClick={() => setShowScopeModal(false)} className="text-subtext hover:text-ink text-lg font-bold">&times;</button>
              </div>
              <div>
                <h3 className="font-display text-2xl text-ink">Choose Your Audit Evaluation Scope</h3>
              </div>
              <div className="grid grid-cols-1 gap-4 pt-2">
                <div 
                  onClick={() => setSelectedScope("core_dev")}
                  className={`p-5 rounded-2xl border-2 cursor-pointer transition flex items-start gap-4 ${
                    selectedScope === "core_dev" 
                      ? "border-primary bg-primary/5 shadow-md" 
                      : "border-hairline hover:border-subtext bg-card"
                  }`}
                >
                  <div className={`mt-0.5 size-5 rounded-full border flex items-center justify-center shrink-0 ${
                    selectedScope === "core_dev" ? "border-primary bg-primary text-background" : "border-subtext"
                  }`}>
                    {selectedScope === "core_dev" && <div className="size-2 rounded-full bg-background" />}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <span className="font-display font-bold text-base text-ink">Core Design & Development Only</span>
                      <span className="px-2.5 py-0.5 rounded-full bg-ink/10 text-ink font-mono text-xs font-semibold">
                        {features.filter(f => !isPhaseRow(f.requirement, f.module) && !isIgnoredRow(f.requirement)).reduce((s,f) => s+(parseFloat(f.planned_hours)||0),0).toFixed(1)} hrs
                      </span>
                    </div>
                    <p className="text-xs text-subtext mt-1">
                      Evaluates strictly coding features. Internal Testing hours are hidden from baseline variance and delay math so QA tasks don't skew developer velocity.
                    </p>
                  </div>
                </div>

                <div 
                  onClick={() => setSelectedScope("full_lifecycle")}
                  className={`p-5 rounded-2xl border-2 cursor-pointer transition flex items-start gap-4 ${
                    selectedScope === "full_lifecycle" 
                      ? "border-primary bg-primary/5 shadow-md" 
                      : "border-hairline hover:border-subtext bg-card"
                  }`}
                >
                  <div className={`mt-0.5 size-5 rounded-full border flex items-center justify-center shrink-0 ${
                    selectedScope === "full_lifecycle" ? "border-primary bg-primary text-background" : "border-subtext"
                  }`}>
                    {selectedScope === "full_lifecycle" && <div className="size-2 rounded-full bg-background" />}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <span className="font-display font-bold text-base text-ink">Full Lifecycle (Design & Dev + Testing)</span>
                      <span className="px-2.5 py-0.5 rounded-full bg-primary/10 text-primary font-mono text-xs font-semibold">
                        {features.filter(f => !isIgnoredRow(f.requirement)).reduce((s,f) => s+(parseFloat(f.planned_hours)||0),0).toFixed(1)} hrs
                      </span>
                    </div>
                    <p className="text-xs text-subtext mt-1">
                      Evaluates both engineering feature coding and internal QA verification against the complete project baseline.
                    </p>
                  </div>
                </div>
              </div>
              <div className="flex justify-end gap-3 pt-4 border-t border-hairline">
                <button
                  onClick={() => setShowScopeModal(false)}
                  className="px-5 py-2.5 rounded-full text-xs font-semibold text-subtext hover:text-ink transition"
                >
                  Cancel
                </button>
                <button
                  onClick={async () => {
                    localStorage.setItem("auditScopeMode", selectedScope);
                    setShowScopeModal(false);
                    await executeSaveAndNavigate();
                  }}
                  disabled={saving}
                  className="px-6 py-2.5 rounded-full bg-primary text-background text-xs font-semibold hover:opacity-90 transition shadow-sm flex items-center gap-2"
                >
                  {saving ? "Saving..." : "Confirm Scope & Continue"}
                  <ArrowRight size={14} />
                </button>
              </div>
            </div>
          </div>
        )}
      </PageBody>
    </>
  );
}

export default SRSUploadPage;
