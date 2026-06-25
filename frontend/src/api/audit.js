import API from "./client";

export const getRepositories = async (owner) => {
    const response = await API.get(`/github/repos/${owner}`);
    return response.data;
};

export const runAudit = async (owner, repo, file, provider) => {
    const formData = new FormData();
    formData.append("owner", owner);
    formData.append("repo", repo);
    formData.append("provider", provider);
    formData.append("srs_file", file);

    const response = await API.post("/audit/upload", formData, {
        headers: {
            "Content-Type": "multipart/form-data"
        }
    });
    return response.data;
};

export const getAuditStatus = async (taskId) => {
    const response = await API.get(`/audit/status/${taskId}`);
    return response.data;
};

export const getDelayAnalysisResult = async (sessionId) => {
    const response = await API.get(`/api/v1/delay-analysis/results/${sessionId}`);
    return response.data;
};

export const getLatestDelayAnalysisResult = async () => {
    const response = await API.get("/api/v1/delay-analysis/results/latest/active");
    return response.data;
};

// ============================================================================
// CONFIRMATION WORKFLOW ENDPOINTS
// ============================================================================

export const uploadSRS = async (auditSessionId, file) => {
    const formData = new FormData();
    formData.append("audit_session_id", auditSessionId);
    formData.append("file", file);

    const response = await API.post("/api/v1/confirm/srs/upload", formData, {
        headers: {
            "Content-Type": "multipart/form-data"
        }
    });
    return response.data;
};

export const fetchPlannedData = async (sessionId) => {
    const response = await API.get(`/api/v1/confirm/session/${sessionId}/srs-data`);
    return response.data;
};

export const savePlannedFeatures = async (sessionId, features) => {
    const response = await API.post("/api/v1/confirm/planned/save", {
        audit_session_id: sessionId,
        features
    });
    return response.data;
};

export const fetchPlatformData = async (sessionId, credentials, forceFullSync = false) => {
    const response = await API.post("/api/v1/confirm/actual/fetch", {
        audit_session_id: sessionId,
        credentials,
        force_full_sync: forceFullSync
    });
    return response.data;
};

export const fetchActualData = async (sessionId) => {
    const response = await API.get(`/api/v1/confirm/session/${sessionId}/platform-data`);
    return response.data;
};

export const saveActualFeatures = async (sessionId, features) => {
    const response = await API.post("/api/v1/confirm/actual/save", {
        audit_session_id: sessionId,
        features
    });
    return response.data;
};

export const previewCapacity = async (sessionId, calendarProfile) => {
    const response = await API.post("/api/v1/confirm/calendar/preview", {
        audit_session_id: sessionId,
        ...calendarProfile
    });
    return response.data;
};

export const fetchNormalizationData = async (sessionId) => {
    const response = await API.get(`/api/v1/confirm/session/${sessionId}/normalization-data`);
    return response.data;
};

export const saveNormalizationData = async (sessionId, normalizationData) => {
    const response = await API.post("/api/v1/confirm/normalization/save", {
        audit_session_id: sessionId,
        normalization_data: normalizationData
    });
    return response.data;
};

export const fetchMatches = async (sessionId) => {
    const response = await API.get(`/api/v1/confirm/session/${sessionId}/matches`);
    return response.data;
};

export const approveMatch = async (matchId) => {
    const response = await API.post(`/api/v1/confirm/matches/approve/${matchId}`);
    return response.data;
};

export const rejectMatch = async (matchId) => {
    const response = await API.post(`/api/v1/confirm/matches/reject/${matchId}`);
    return response.data;
};

export const saveMatches = async (sessionId, matches) => {
    const response = await API.post("/api/v1/confirm/matches/save", {
        audit_session_id: sessionId,
        matches
    });
    return response.data;
};

export const getRowIntelligence = async (sessionId, requirement) => {
    const response = await API.get("/api/v1/delay-analysis/row-intelligence", {
        params: {
            session_id: sessionId,
            requirement
        }
    });
    return response.data;
};
