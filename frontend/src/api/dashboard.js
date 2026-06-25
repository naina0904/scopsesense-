import api from "./client";

export async function fetchHealth() {

    const response = await api.get(
        "/health"
    );

    return response.data;
}