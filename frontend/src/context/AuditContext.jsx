import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";
import api from "../api/client";
import { 
  getDelayAnalysisResult, 
  getLatestDelayAnalysisResult,
  uploadSRS as apiUploadSRS,
  fetchPlannedData,
  savePlannedFeatures,
  fetchPlatformData,
  fetchActualData,
  saveActualFeatures,
  previewCapacity,
  fetchNormalizationData,
  saveNormalizationData,
  fetchMatches,
  approveMatch,
  rejectMatch,
  saveMatches,
  getRowIntelligence
} from "../api/audit";

const AuditContext = createContext();
const POLL_INTERVAL_MS = 3000;
const AUDIT_TIMEOUT_MS = 5 * 60 * 1000;

export const useAudit = () => useContext(AuditContext);

export const AuditProvider = ({ children }) => {
  const [auditResult, setAuditResult] = useState(null);
  const [auditSession, setAuditSession] = useState(null);

  const [loading, setLoading] = useState(false);
  const [sessionLoading, setSessionLoading] = useState(true);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState(null);

  const [taskId, setTaskId] = useState(null);
  const [sessionId, setSessionId] = useState(null);

  // UI toggle states for sidebar and modals
  const [showFaqs, setShowFaqs] = useState(false);
  const [showCopilot, setShowCopilot] = useState(false);
  const [showDeveloperPerformance, setShowDeveloperPerformance] = useState(false);

  const pollRef = useRef(null);
  const stepActionRef = useRef({ onNext: null, onPrev: null });

  const registerStepAction = useCallback((actions) => {
    stepActionRef.current = { onNext: actions?.onNext || null, onPrev: actions?.onPrev || null };
  }, []);

  const stopPolling = () => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  };

  const fetchActiveSession = useCallback(async () => {
    try {
      setSessionLoading(true);
      setError(null);
      const response = await api.get("/api/v1/confirm/session/active");
      setAuditSession(response.data);
      setSessionId(response.data.id);
      return response.data;
    } catch (err) {
      console.error("Failed to fetch active session", err);
      setError(err.response?.data?.detail || "Unable to create or load the audit session.");
      throw err;
    } finally {
      setSessionLoading(false);
    }
  }, []);

  const confirmSRS = async (activeSessionId) => {
    try {
      const response = await api.post("/api/v1/confirm/srs", { audit_session_id: activeSessionId });
      await fetchActiveSession();
      return response.data;
    } catch (err) {
      console.error("Failed to confirm SRS", err);
      throw err;
    }
  };

  const confirmPlatform = async (activeSessionId) => {
    try {
      const response = await api.post("/api/v1/confirm/platform", { audit_session_id: activeSessionId });
      await fetchActiveSession();
      return response.data;
    } catch (err) {
      console.error("Failed to confirm platform", err);
      throw err;
    }
  };

  const confirmCalendar = async (activeSessionId, calendarProfile = {}) => {
    try {
      const response = await api.post("/api/v1/confirm/calendar", {
        audit_session_id: activeSessionId,
        ...calendarProfile,
      });
      await fetchActiveSession();
      return response.data;
    } catch (err) {
      console.error("Failed to confirm calendar", err);
      throw err;
    }
  };

  const uploadSRSFile = async (file) => {
    if (!auditSession) throw new Error("No active session");
    try {
      const data = await apiUploadSRS(auditSession.id, file);
      await fetchActiveSession();
      return data;
    } catch (err) {
      console.error("Failed to upload SRS file", err);
      throw err;
    }
  };

  const getPlannedFeatures = async () => {
    if (!auditSession) return { features: [] };
    try {
      return await fetchPlannedData(auditSession.id);
    } catch (err) {
      console.error("Failed to fetch planned features", err);
      throw err;
    }
  };

  const savePlannedData = async (features) => {
    if (!auditSession) throw new Error("No active session");
    try {
      const res = await savePlannedFeatures(auditSession.id, features);
      await fetchActiveSession();
      return res;
    } catch (err) {
      console.error("Failed to save planned features", err);
      throw err;
    }
  };

  const fetchPlatform = async (credentials, forceFullSync = false) => {
    if (!auditSession) throw new Error("No active session");
    try {
      const res = await fetchPlatformData(auditSession.id, credentials, forceFullSync);
      await fetchActiveSession();
      return res;
    } catch (err) {
      console.error("Failed to fetch platform data", err);
      throw err;
    }
  };

  const getActualFeatures = async () => {
    if (!auditSession) return { features: [] };
    try {
      return await fetchActualData(auditSession.id);
    } catch (err) {
      console.error("Failed to fetch actual features", err);
      throw err;
    }
  };

  const saveActualData = async (features) => {
    if (!auditSession) throw new Error("No active session");
    try {
      const res = await saveActualFeatures(auditSession.id, features);
      await fetchActiveSession();
      return res;
    } catch (err) {
      console.error("Failed to save actual features", err);
      throw err;
    }
  };

  const getCapacityPreview = async (calendarProfile) => {
    if (!auditSession) return null;
    try {
      return await previewCapacity(auditSession.id, calendarProfile);
    } catch (err) {
      console.error("Failed to preview capacity", err);
      throw err;
    }
  };

  const getNormalizationData = async () => {
    if (!auditSession) return { normalization_data: [] };
    try {
      return await fetchNormalizationData(auditSession.id);
    } catch (err) {
      console.error("Failed to fetch normalization data", err);
      throw err;
    }
  };

  const saveNormalization = async (normalizationData) => {
    if (!auditSession) throw new Error("No active session");
    try {
      const res = await saveNormalizationData(auditSession.id, normalizationData);
      await fetchActiveSession();
      return res;
    } catch (err) {
      console.error("Failed to save normalization data", err);
      throw err;
    }
  };

  const getMatchesList = async () => {
    if (!auditSession) return { matches: [] };
    try {
      return await fetchMatches(auditSession.id);
    } catch (err) {
      console.error("Failed to fetch matches list", err);
      throw err;
    }
  };

  const approveSingleMatch = async (matchId) => {
    try {
      return await approveMatch(matchId);
    } catch (err) {
      console.error("Failed to approve match", err);
      throw err;
    }
  };

  const rejectSingleMatch = async (matchId) => {
    try {
      return await rejectMatch(matchId);
    } catch (err) {
      console.error("Failed to reject match", err);
      throw err;
    }
  };

  const saveMatchesList = async (matches) => {
    if (!auditSession) throw new Error("No active session");
    try {
      const res = await saveMatches(auditSession.id, matches);
      await fetchActiveSession();
      return res;
    } catch (err) {
      console.error("Failed to save matches", err);
      throw err;
    }
  };

  const fetchRowIntelligence = async (requirement) => {
    if (!auditSession) throw new Error("No active session");
    try {
      return await getRowIntelligence(auditSession.id, requirement);
    } catch (err) {
      console.error("Failed to fetch row intelligence", err);
      throw err;
    }
  };

  const runDelayAnalysis = async (provider = "groq") => {
    if (!auditSession) throw new Error("No active session");
    try {
      stopPolling();
      setLoading(true);
      setError(null);
      setAuditResult(null);
      setProgress(10);

      const formData = new FormData();
      formData.append("audit_session_id", auditSession.id);
      formData.append("provider", provider);

      const response = await api.post("/api/v1/delay-analysis/analyze", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      const { task_id, session_id: responseSessionId } = response.data;
      if (!task_id) throw new Error("No task ID returned");

      setTaskId(task_id);
      if (responseSessionId) {
        setSessionId(responseSessionId);
      }

      const startedAt = Date.now();
      const poll = setInterval(async () => {
        try {
          if (Date.now() - startedAt > AUDIT_TIMEOUT_MS) {
            stopPolling();
            setError("Audit timed out before completion. Retry when the backend worker is available.");
            setLoading(false);
            setProgress(0);
            return;
          }

          const statusRes = await api.get(`/api/v1/delay-analysis/analyze/status/${task_id}`);
          const status = statusRes.data.status;

          if (status === "COMPLETED") {
            stopPolling();
            const sid = statusRes.data.session_id || responseSessionId || auditSession.id;
            if (sid) {
              setSessionId(sid);
              await fetchAuditResult(sid);
            } else {
              throw new Error("Missing session ID from backend response.");
            }
            setLoading(false);
            setProgress(100);
          } else if (status === "FAILED") {
            stopPolling();
            setError(statusRes.data.error || "Analysis failed");
            setLoading(false);
            setProgress(0);
          } else {
            setProgress((currentProgress) => (currentProgress < 90 ? currentProgress + 10 : currentProgress));
          }
        } catch (pollErr) {
          console.error("Polling error", pollErr);
          stopPolling();
          setError("Lost connection to the audit task. Retry when the service is reachable.");
          setLoading(false);
          setProgress(0);
        }
      }, POLL_INTERVAL_MS);

      pollRef.current = poll;
    } catch (err) {
      console.error("Failed to queue analysis", err);
      if (err.response?.data?.detail) {
        const detail = err.response.data.detail;
        setError(typeof detail === 'string' ? detail : JSON.stringify(detail));
      } else {
        setError(err.message || "Failed to fetch active session.");
      }
      setLoading(false);
      setProgress(0);
      throw err;
    }
  };

  const fetchAuditResult = useCallback(async (activeSessionId = null) => {
    try {
      setLoading(true);
      setError(null);
      const targetSessionId = activeSessionId || sessionId;
      if (!targetSessionId) return null;
      const result = await getDelayAnalysisResult(targetSessionId);
      setAuditResult(result);
      setSessionId(result.session_id);
      setProgress(100);
      return result;
    } catch (err) {
      console.error("fetchAuditResult error:", err);
      if (err.response?.status !== 404) {
        setError(err.response?.data?.detail || err.message || "Unable to load audit results.");
      }
      return null;
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  useEffect(() => {
    return () => {
      stopPolling();
    };
  }, []);

  const value = {
    auditResult,
    setAuditResult,
    loading,
    setLoading,
    sessionLoading,
    progress,
    setProgress,
    error,
    setError,
    auditSession,
    setAuditSession,
    fetchActiveSession,
    confirmSRS,
    confirmPlatform,
    confirmCalendar,
    uploadSRSFile,
    getPlannedFeatures,
    savePlannedData,
    fetchPlatform,
    getActualFeatures,
    saveActualData,
    getCapacityPreview,
    getNormalizationData,
    saveNormalization,
    getMatchesList,
    approveSingleMatch,
    rejectSingleMatch,
    saveMatchesList,
    fetchRowIntelligence,
    runDelayAnalysis,
    fetchAuditResult,
    taskId,
    sessionId,
    stepActionRef,
    registerStepAction,
    showFaqs,
    setShowFaqs,
    showCopilot,
    setShowCopilot,
    showDeveloperPerformance,
    setShowDeveloperPerformance,
  };

  return <AuditContext.Provider value={value}>{children}</AuditContext.Provider>;
};
