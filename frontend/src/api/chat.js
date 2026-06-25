import api from "./client";

export async function askProjectAI(
    question,
    provider = "groq"
) {

    const response = await api.post(
        "/chat",
        {
            question,
            provider
        }
    );

    return response.data;
}

export async function askDelayAnalysisChat(question, sessionId, provider = "groq", projectKey = "", platform = "") {
    const response = await api.post(
        "/api/v1/delay-analysis/chat",
        {
            question,
            session_id: sessionId,
            provider,
            project_key: projectKey,
            platform: platform
        }
    );
    return response.data;
}
