import { useEffect, useState } from "react";
import { useProject } from "../context/ProjectContext";
import { useAudit } from "../context/AuditContext";
import { useNavigate } from "react-router-dom";
import { CheckCircle, Database, Plus, RefreshCw, Plug, Trash2, ArrowUpRight, Check, Save } from "lucide-react";
import { PageHeader, PageBody } from "../components/ui/PageChrome";
import api from "../api/client";

function ProjectSetupPage() {
  const {
    setProjectDataConfirmed,
  } = useProject();

  const { auditSession, fetchActiveSession, fetchPlatform, getActualFeatures, saveActualData, confirmCalendar, getCapacityPreview, error, setError, sessionLoading } = useAudit();
  const navigate = useNavigate();

  const [actualFeatures, setActualFeatures] = useState([]);
  const [fetching, setFetching] = useState(false);
  const [hasFetched, setHasFetched] = useState(false);
  const [savingActual, setSavingActual] = useState(false);
  const [forceFullSync, setForceFullSync] = useState(false);

  const [connections, setConnections] = useState([]);
  const [selectedConnectionId, setSelectedConnectionId] = useState(null);
  const [loadingConnections, setLoadingConnections] = useState(true);

  const [workingDays, setWorkingDays] = useState(["Monday","Tuesday","Wednesday","Thursday","Friday"]);
  const [hoursPerDay, setHoursPerDay] = useState(8);
  const [timezone, setTimezone] = useState("UTC");
  const [holidays, setHolidays] = useState([]);
  const [newHoliday, setNewHoliday] = useState("");
  const [savingCalendar, setSavingCalendar] = useState(false);

  const [capacityMetrics, setCapacityMetrics] = useState(null);

  useEffect(() => {
    fetchActiveSession().catch(() => {});
    
    const fetchConnections = async () => {
      try {
        const res = await api.get(`/api/v1/confirm/integrations/connections`);
        setConnections(res.data.connections || []);
        if (res.data.connections?.length > 0) {
            setSelectedConnectionId(res.data.connections[0].id);
        }
      } catch (err) {
        console.error("Failed to fetch connections", err);
      } finally {
        setLoadingConnections(false);
      }
    };
    fetchConnections();

    const handleConnectionsUpdated = () => {
      fetchConnections();
    };

    window.addEventListener("connectionsUpdated", handleConnectionsUpdated);
    window.addEventListener("loginComplete", handleConnectionsUpdated);
    
    return () => {
      window.removeEventListener("connectionsUpdated", handleConnectionsUpdated);
      window.removeEventListener("loginComplete", handleConnectionsUpdated);
    };
  }, [fetchActiveSession]);

  useEffect(() => {
    if (auditSession?.platform_fetch_result_id) {
      api.get("/api/v1/confirm/integrations/connections")
        .then(res => {
          const fetchedConnections = res.data.connections || [];
          setConnections(fetchedConnections);
          if (fetchedConnections.length > 0 && !selectedConnectionId) {
            setSelectedConnectionId(fetchedConnections[0].id);
          }
        })
        .catch(() => {});
      getActualFeatures()
        .then((res) => {
          if (res && res.features) {
            setActualFeatures(res.features);
            setHasFetched(true);
          }
        })
        .catch(() => {});
    }
  }, [auditSession, getActualFeatures, selectedConnectionId]);


  const handleFetchPlatform = async () => {
    if (!auditSession) return;
    setError(null);
    setFetching(true);
    setHasFetched(false);
    try {
      const activeConnection = connections.find(c => c.id === selectedConnectionId) || connections[0];
      const activePlatform = activeConnection ? activeConnection.platform : "jira";
      const credentials = { platform: activePlatform };
      
      const res = await fetchPlatform(credentials, forceFullSync, selectedConnectionId);
      if (res && res.features) {
        setActualFeatures(res.features);
        setHasFetched(true);
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message || "Failed to fetch platform data. Please check your credentials.");
    } finally {
      setFetching(false);
    }
  };

  useEffect(() => {
    if (!auditSession) return;
    const debouncer = setTimeout(async () => {
      try {
        const res = await getCapacityPreview({
          working_days: workingDays,
          hours_per_day: Number(hoursPerDay) || 8,
          holidays,
          timezone,
          workday_start: "09:00",
          workday_end: "17:00",
        });
        setCapacityMetrics(res);
      } catch (err) {
        console.error(err);
      }
    }, 400);

    return () => clearTimeout(debouncer);
  }, [workingDays, hoursPerDay, holidays, timezone, auditSession, getCapacityPreview]);

  const handleFieldChange = (index, field, value) => {
    const updated = [...actualFeatures];
    updated[index] = { ...updated[index], [field]: value };
    setActualFeatures(updated);
  };

  const addActualRow = () => {
    setActualFeatures([
      ...actualFeatures,
      {
        module: "General",
        requirement: `New Activity ${actualFeatures.length + 1}`,
        assigned_developer: "Unassigned",
        actual_hours: 0.0,
        status: "Todo"
      }
    ]);
  };

  const deleteActualRow = (index) => {
    setActualFeatures(actualFeatures.filter((_, i) => i !== index));
  };

  const addHoliday = () => {
    if (newHoliday && !holidays.includes(newHoliday)) {
      setHolidays([...holidays, newHoliday]);
      setNewHoliday("");
    }
  };

  const removeHoliday = (hDate) => {
    setHolidays(holidays.filter(d => d !== hDate));
  };

  const handleSaveAndApprove = async () => {
    try {
      setSavingActual(true);
      setSavingCalendar(true);
      setError(null);

      const cleanedFeatures = actualFeatures.map(({ dependencies, name, ...rest }) => ({
        ...rest,
        requirement: rest.requirement || name || ""
      }));
      await saveActualData(cleanedFeatures);

      await confirmCalendar(auditSession.id, {
        working_days: workingDays,
        hours_per_day: Number(hoursPerDay),
        holidays: holidays,
        timezone,
        workday_start: "09:00",
        workday_end: "17:00",
      });

      setProjectDataConfirmed(true);
      navigate("/normalization");
    } catch (err) {
      setError(err.response?.data?.detail || err.message || "Failed to confirm project credentials or calendar.");
    } finally {
      setSavingActual(false);
      setSavingCalendar(false);
    }
  };

  const isPlatformValid = connections.length > 0;

  return (
    <>
      <PageHeader
        eyebrow="Steps 3, 4 & 5 · Audit workflow"
        title="Connect Platform & Confirm Capacity."
        lede="Connect to Jira or GitHub to fetch actual work items, and customize developer working capacity."
        primary={actualFeatures.length > 0 ? { label: savingActual ? "Saving..." : "Approve Data & Continue", onClick: handleSaveAndApprove } : undefined}
      />
      <PageBody>
        {error && (
          <div className="bg-rose/20 border border-rose text-ink px-4 py-3 rounded-xl text-sm font-medium flex items-center justify-between">
             <span>{error}</span>
             <button onClick={() => setError(null)} className="opacity-50 hover:opacity-100">&times;</button>
          </div>
        )}

        {auditSession?.actual_data_approved && auditSession?.capacity_approved && (
          <div className="flex items-center gap-2 bg-pista/30 border border-pista text-ink px-4 py-3 rounded-xl text-sm font-semibold">
            <CheckCircle size={18} />
            <span>Platform & Capacity Approved</span>
          </div>
        )}

        <div className="max-w-3xl">
          <div className="soft-card p-6 bg-beige/30 border border-hairline">
             <div className="flex items-center gap-2 border-b border-hairline pb-4 mb-5">
               <Database className="size-5 text-ink" />
               <h2 className="font-display text-2xl text-ink">Platform Connection</h2>
             </div>

             <div className="space-y-4">
                {loadingConnections ? (
                  <div className="flex items-center gap-2 text-subtext text-sm">
                    <RefreshCw className="size-4 animate-spin" /> Loading connection status...
                  </div>
                ) : connections.length === 0 ? (
                  <div className="p-6 bg-card border border-hairline rounded-xl text-center">
                    <Plug className="size-8 text-subtext mx-auto mb-3" />
                    <h3 className="font-medium text-ink mb-1">No Platforms Connected</h3>
                    <p className="text-subtext text-sm max-w-sm mx-auto">
                      Please use the "Integrations" section in the left sidebar to connect your Jira or GitHub account.
                    </p>
                  </div>
                ) : (
                  <div className="p-4 bg-success/10 border border-success/20 rounded-xl flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <CheckCircle className="size-5 text-success" />
                      <div>
                        {connections.length === 1 ? (
                          <>
                            <div className="text-sm font-medium text-ink">
                              Connected to {connections[0].platform === "jira" ? "Jira Project Key: " + connections[0].credentials.project_key : "GitHub Repo: " + connections[0].credentials.repo}
                            </div>
                            <div className="text-xs text-subtext mt-0.5">
                              Ready to fetch actual platform tasks.
                            </div>
                          </>
                        ) : (
                          <div className="w-full">
                            <label className="text-xs font-semibold tracking-wider text-subtext uppercase mb-1 block">Select Project Key to Fetch</label>
                            <select
                              value={selectedConnectionId || ""}
                              onChange={(e) => setSelectedConnectionId(Number(e.target.value))}
                              className="bg-card border border-hairline rounded-lg px-3 py-1.5 text-sm text-ink focus:outline-none focus:ring-1 focus:ring-primary/20 w-64"
                            >
                              {connections.map(c => (
                                <option key={c.id} value={c.id}>
                                  {c.platform === "jira" ? `Jira Project Key: ${c.credentials.project_key}` : `GitHub Repo: ${c.credentials.repo}`}
                                </option>
                              ))}
                            </select>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}
                
                <div className="flex items-center gap-2 mt-4">
                  <input
                    type="checkbox"
                    id="forceFullSync"
                    checked={forceFullSync}
                    onChange={(e) => setForceFullSync(e.target.checked)}
                    className="w-4 h-4 text-ink border-hairline rounded focus:ring-ring"
                  />
                  <label htmlFor="forceFullSync" className="text-sm font-medium text-ink">
                    Force Full Sync (Ignore Incremental Delta)
                  </label>
                </div>

                <button
                  onClick={handleFetchPlatform}
                  disabled={!isPlatformValid || fetching || sessionLoading}
                  className="w-full h-12 mt-4 rounded-full bg-ink text-background text-sm font-medium inline-flex items-center justify-center hover:opacity-90 transition disabled:opacity-50"
                >
                  {fetching ? "Fetching Actual Data..." : "Fetch Platform Tasks"}
                </button>
             </div>
          </div>

        </div>

        {actualFeatures.length > 0 ? (
          <div className="mt-10 soft-card overflow-hidden">
            <div className="flex justify-between items-center px-6 py-5 border-b border-hairline">
              <div>
                <h3 className="font-display text-2xl">Table 2: Actual Platform Tasks</h3>
                <p className="text-subtext text-sm">Inspect and override the tasks fetched from {connections.length > 0 ? (connections[0].platform === "jira" ? "Jira" : "GitHub") : "the platform"}.</p>
              </div>
              <button
                onClick={addActualRow}
                className="h-10 px-4 rounded-full border border-hairline bg-card text-sm hover:bg-secondary transition flex items-center gap-2"
              >
                <Plus size={16} /> Add Task
              </button>
            </div>

            <div className="overflow-x-auto">
              <div className="min-w-[1400px]">
                <div className="grid grid-cols-[2fr_2.5fr_1fr_1fr_1.5fr_1fr_1fr_1fr_1fr_0.8fr_40px] gap-2 px-6 py-3 text-[11px] uppercase tracking-wider text-subtext bg-beige/40 border-b border-hairline items-center">
                  <div>Module / Epic</div>
                  <div>Actual Feature</div>
                  <div>Type</div>
                  <div>Status</div>
                  <div>Assignee</div>
                  <div>Priority</div>
                  <div>Created</div>
                  <div>Completed</div>
                  <div className="text-center">Story Pts</div>
                  <div className="text-center">Hours</div>
                  <div className="text-right">Act</div>
                </div>
                
                <div className="divide-y divide-hairline">
                  {actualFeatures.map((item, index) => (
                    <div key={index} className="grid grid-cols-[2fr_2.5fr_1fr_1fr_1.5fr_1fr_1fr_1fr_1fr_0.8fr_40px] px-6 py-3 items-center hover:bg-secondary/50 transition gap-2">
                      <div>
                         <input
                          type="text"
                          value={item.module || ""}
                          onChange={(e) => handleFieldChange(index, "module", e.target.value)}
                          className="bg-card border border-hairline rounded-lg px-2 py-1.5 text-xs text-ink w-full focus:outline-none focus:ring-1 focus:ring-ring"
                        />
                      </div>
                      <div>
                        <input
                          type="text"
                          value={item.requirement || item.name || ""}
                          onChange={(e) => handleFieldChange(index, "requirement", e.target.value)}
                          className="bg-card border border-hairline rounded-lg px-2 py-1.5 text-xs font-medium text-ink w-full focus:outline-none focus:ring-1 focus:ring-ring"
                        />
                      </div>
                      <div>
                        <div className="bg-card border border-hairline rounded-lg px-2 py-1.5 text-xs text-subtext w-full text-center truncate">
                          {item.issue_type || "Task"}
                        </div>
                      </div>
                      <div>
                        <select
                          value={item.status || "Todo"}
                          onChange={(e) => handleFieldChange(index, "status", e.target.value)}
                          className="bg-card border border-hairline rounded-lg px-2 py-1.5 text-xs text-ink w-full focus:outline-none focus:ring-1 focus:ring-ring"
                        >
                          <option value="Todo">Todo</option>
                          <option value="In Progress">In Progress</option>
                          <option value="In Review">In Review</option>
                          <option value="Done">Done</option>
                          <option value="Blocked">Blocked</option>
                        </select>
                      </div>
                      <div>
                         <input
                          type="text"
                          value={item.assigned_developer || ""}
                          onChange={(e) => handleFieldChange(index, "assigned_developer", e.target.value)}
                          className="bg-card border border-hairline rounded-lg px-2 py-1.5 text-xs text-ink w-full focus:outline-none focus:ring-1 focus:ring-ring"
                        />
                      </div>
                      <div>
                        <select
                          value={item.priority || "Medium"}
                          onChange={(e) => handleFieldChange(index, "priority", e.target.value)}
                          className="bg-card border border-hairline rounded-lg px-2 py-1.5 text-xs text-ink w-full focus:outline-none focus:ring-1 focus:ring-ring"
                        >
                          <option value="Low">Low</option>
                          <option value="Medium">Medium</option>
                          <option value="High">High</option>
                          <option value="Critical">Critical</option>
                        </select>
                      </div>
                      <div>
                        <div className="bg-card border border-hairline rounded-lg px-2 py-1.5 text-xs text-subtext w-full truncate">
                          {item.created_date ? new Date(item.created_date).toLocaleDateString() : "-"}
                        </div>
                      </div>
                      <div>
                        <div className="bg-card border border-hairline rounded-lg px-2 py-1.5 text-xs text-subtext w-full truncate">
                          {item.completed_date ? new Date(item.completed_date).toLocaleDateString() : "-"}
                        </div>
                      </div>
                      <div>
                        <div className="bg-card border border-hairline rounded-lg px-2 py-1.5 text-xs text-subtext w-full text-center truncate">
                          {item.story_points ?? "-"}
                        </div>
                      </div>
                      <div>
                         <input
                          type="number"
                          step="0.5"
                          value={item.actual_hours || 0}
                          onChange={(e) => handleFieldChange(index, "actual_hours", parseFloat(e.target.value) || 0)}
                          className="bg-card border border-hairline rounded-lg px-2 py-1.5 text-xs text-ink w-full text-center focus:outline-none focus:ring-1 focus:ring-ring"
                        />
                      </div>
                      <div className="flex justify-end">
                        <button
                          onClick={() => deleteActualRow(index)}
                          className="text-risk hover:text-red-700 p-1.5 rounded-lg hover:bg-rose/30 transition"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
            
            <div className="flex justify-end p-6 border-t border-hairline bg-beige/30">
              <button
                  onClick={handleSaveAndApprove}
                  disabled={savingActual || savingCalendar}
                  className="h-12 px-6 rounded-full bg-ink text-background text-sm font-medium inline-flex items-center hover:opacity-90 transition disabled:opacity-50"
              >
                  {savingActual ? "Saving Data & Calendar..." : "Approve Data & Continue to Normalization →"}
              </button>
            </div>
          </div>
        ) : hasFetched ? (
          <div className="soft-card p-10 text-center mt-10">
            <h2 className="text-xl font-display text-ink">No Tasks Found</h2>
            <p className="text-subtext mt-2">We successfully connected to your project, but found 0 tasks. Please check if your project is empty or try a different project key.</p>
          </div>
        ) : null}
      </PageBody>
    </>
  );
}

export default ProjectSetupPage;
