import { useEffect, useState } from "react";
import { useSRS } from "../context/SRSContext";
import { useAudit } from "../context/AuditContext";
import { useNavigate } from "react-router-dom";
import { UploadCloud, CheckCircle, Save, Plus, Trash2, ArrowUpRight, Sparkles, ShieldCheck, FileText } from "lucide-react";
import { PageHeader, PageBody } from "../components/ui/PageChrome";
import { ScopeBadge } from "../components/ui/ScopeBadge";

function SRSUploadPage() {
  const { setSRSFile, setExtractionConfirmed } = useSRS();
  const { auditSession, fetchActiveSession, uploadSRSFile, getPlannedFeatures, savePlannedData, sessionLoading, error, setError } = useAudit();
  const navigate = useNavigate();

  const [features, setFeatures] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [fileName, setFileName] = useState("");

  useEffect(() => {
    fetchActiveSession().catch(() => {});
  }, [fetchActiveSession]);

  useEffect(() => {
    if (auditSession?.srs_result_id) {
      getPlannedFeatures()
        .then((res) => {
          if (res && res.features) {
            setFeatures(res.features);
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

  const addRow = () => {
    setFeatures([
      ...features,
      {
        module: "General",
        requirement: `New Requirement ${features.length + 1}`,
        planned_hours: 0.0,
        assigned_developer: "Unassigned",
        priority: "Medium"
      }
    ]);
  };

  const deleteRow = (index) => {
    const updated = features.filter((_, i) => i !== index);
    setFeatures(updated);
  };

  const handleSaveAndApprove = async () => {
    try {
      setSaving(true);
      setError(null);
      const cleanedFeatures = features.map(({ dependencies, ...rest }) => rest);
      await savePlannedData(cleanedFeatures);
      setExtractionConfirmed(true);
      navigate("/configuration");
    } catch (err) {
      setError(err.response?.data?.detail || err.message || "Failed to save planned features.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <>
      <PageHeader
        eyebrow="Steps 1 & 2 · Audit workflow"
        title="Upload SRS & Review Requirements."
        lede="Drop in the requirements specification. ScopeSense will parse every requirement, owner, and acceptance criterion."
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
          <div className="flex items-center gap-2 bg-pista/30 border border-pista text-ink px-4 py-3 rounded-xl text-sm font-semibold">
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
              {fileName && <p className="mt-4 text-ink text-sm font-medium">Selected: <span className="opacity-70">{fileName}</span></p>}
            </div>
          </div>

          <div className="space-y-5">
            <div className="soft-card p-6 bg-lavender/40">
              <div className="flex items-center gap-2 text-xs text-ink/60"><Sparkles className="size-3.5" /> AI parsing</div>
              <h4 className="mt-2 font-display text-xl">Smart extraction</h4>
              <p className="text-sm text-ink/70 mt-2">We identify requirements, owners, dependencies and acceptance criteria automatically.</p>
            </div>
            <div className="soft-card p-6">
              <div className="flex items-center gap-2 text-xs text-subtext"><ShieldCheck className="size-3.5" /> Privacy</div>
              <h4 className="mt-2 font-display text-xl">Your data stays yours</h4>
              <p className="text-sm text-subtext mt-2">Documents are encrypted at rest, processed in your region, and never used for model training.</p>
            </div>
          </div>
        </div>

        {features.length > 0 && (
          <div className="mt-10">
            <div className="flex justify-between items-center mb-4">
              <div>
                <h3 className="font-display text-2xl">Table 1: Planned Requirements Review</h3>
                <p className="text-subtext text-sm">Confirm each requirement parsed from your SRS.</p>
              </div>
              <button
                onClick={addRow}
                className="h-10 px-4 rounded-full border border-hairline bg-card text-sm hover:bg-secondary transition flex items-center gap-2"
              >
                <Plus size={16} /> Add Feature
              </button>
            </div>

            <div className="soft-card overflow-hidden">
                <div className="grid grid-cols-12 px-6 py-3 text-[11px] uppercase tracking-wider text-subtext bg-beige/40 border-b border-hairline">
                  <div className="col-span-2">Module / Epic</div>
                  <div className="col-span-4">Requirement</div>
                  <div className="col-span-2">Owner</div>
                  <div className="col-span-2">Priority</div>
                  <div className="col-span-1">Hours</div>
                  <div className="col-span-1 text-right">Actions</div>
                </div>
                
                <div className="divide-y divide-hairline">
                  {features.map((item, index) => (
                    <div key={index} className="grid grid-cols-12 px-6 py-3 items-center hover:bg-secondary/50 transition gap-2">
                      <div className="col-span-2">
                         <input
                          type="text"
                          value={item.module || ""}
                          onChange={(e) => handleFieldChange(index, "module", e.target.value)}
                          className="bg-card border border-hairline rounded-lg px-2 py-1 text-sm text-ink w-full focus:outline-none focus:ring-1 focus:ring-ring"
                        />
                      </div>
                      <div className="col-span-4">
                        <input
                          type="text"
                          value={item.requirement || ""}
                          onChange={(e) => handleFieldChange(index, "requirement", e.target.value)}
                          className="bg-card border border-hairline rounded-lg px-2 py-1 text-sm font-medium text-ink w-full focus:outline-none focus:ring-1 focus:ring-ring"
                        />
                      </div>
                      <div className="col-span-2">
                         <input
                          type="text"
                          value={item.assigned_developer || ""}
                          onChange={(e) => handleFieldChange(index, "assigned_developer", e.target.value)}
                          className="bg-card border border-hairline rounded-lg px-2 py-1 text-sm text-subtext w-full focus:outline-none focus:ring-1 focus:ring-ring"
                        />
                      </div>
                      <div className="col-span-2">
                         <select
                          value={item.priority || "Medium"}
                          onChange={(e) => handleFieldChange(index, "priority", e.target.value)}
                          className="bg-card border border-hairline rounded-lg px-2 py-1 text-sm text-ink w-full focus:outline-none focus:ring-1 focus:ring-ring"
                        >
                          <option value="Low">Low</option>
                          <option value="Medium">Medium</option>
                          <option value="High">High</option>
                          <option value="Critical">Critical</option>
                        </select>
                      </div>
                      <div className="col-span-1">
                         <input
                          type="number"
                          step="0.5"
                          value={item.planned_hours || 0}
                          onChange={(e) => handleFieldChange(index, "planned_hours", parseFloat(e.target.value) || 0)}
                          className="bg-card border border-hairline rounded-lg px-2 py-1 text-sm text-ink w-full focus:outline-none focus:ring-1 focus:ring-ring"
                        />
                      </div>
                      <div className="col-span-1 flex justify-end">
                        <button
                          onClick={() => deleteRow(index)}
                          className="text-risk hover:text-red-700 p-1.5 rounded-lg hover:bg-rose/30 transition"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
                <div className="px-6 py-3 text-xs text-subtext bg-beige/30 border-t border-hairline">
                  Showing {features.length} requirements
                </div>
            </div>
            
            <div className="flex justify-end mt-6">
              <button
                  onClick={handleSaveAndApprove}
                  disabled={saving}
                  className="h-12 px-6 rounded-full bg-ink text-background text-sm font-medium inline-flex items-center hover:opacity-90 transition disabled:opacity-50"
              >
                  {saving ? "Saving..." : "Confirm & continue to platform setup →"}
              </button>
            </div>
          </div>
        )}
      </PageBody>
    </>
  );
}

export default SRSUploadPage;
