import API from "./client";

export async function getAuditHistory() {

    const response = await API.get(
        "/audits/history"
    );

    return response.data;
}

export async function getContributorHistory() {

    const response = await API.get(
        "/contributors/history"
    );

    return response.data;
}

export async function getFeatureHistory() {

    const response = await API.get(
        "/features/history"
    );

    return response.data;
}