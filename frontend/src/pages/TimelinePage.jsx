import {
    useEffect,
    useState
} from "react";

import axios from "axios";
import { API_BASE_URL } from "../config";

import TimelineChart from "../components/TimelineChart";

import DelayInsightsCard from "../components/DelayInsightsCard";
import ProviderStatusCard from "../components/ProviderStatusCard";

function TimelinePage() {

    const [timelineAnalysis, setTimelineAnalysis] =
        useState([]);

    const [insights, setInsights] =
        useState([]);

    const [providerMetadata, setProviderMetadata] =
        useState(null);

    useEffect(() => {

        async function loadLatestAudit() {

            try {

                const owner =
                    window.localStorage.getItem(
                        "latest_audit_owner"
                    );

                const repo =
                    window.localStorage.getItem(
                        "latest_audit_repo"
                    );

                const params = new URLSearchParams();
                if (owner && repo) {
                    params.append("owner", owner);
                    params.append("repo", repo);
                }
                params.append("normalize", "true");

                const response =
                    await axios.get(
                        `${API_BASE_URL}/audit/latest?${params.toString()}`
                    );

                const latest =
                    response.data.result || {};

                setTimelineAnalysis(
                    latest.timeline_analysis || []
                );

                setInsights(
                    latest.insights || []
                );

                setProviderMetadata(
                    latest.provider_metadata || null
                );

            } catch (error) {

                console.error(error);
            }
        }

        loadLatestAudit();

    }, []);

    const formatDate = (value) => {
        if (!value) {
            return null;
        }

        try {
            return new Date(value).toLocaleDateString();
        } catch (err) {
            return value;
        }
    };

    return (

        <div className="space-y-8">

            <div>

                <h1 className="text-4xl font-bold">
                    Timeline Intelligence
                </h1>

                <p className="text-slate-400 mt-2">
                    AI-powered engineering activity analysis
                </p>

            </div>

            <TimelineChart data={timelineAnalysis} />

            <ProviderStatusCard metadata={providerMetadata} />

            <DelayInsightsCard insights={insights} />

            {
                timelineAnalysis.length > 0 && (

                    <div className="
                        bg-slate-900
                        border
                        border-slate-800
                        rounded-2xl
                        p-6
                        space-y-4
                    ">

                        <h2 className="text-2xl font-semibold">
                            Latest Semantic Timeline
                        </h2>

                        {
                            timelineAnalysis.map(
                                (item, index) => (

                                    <div
                                        key={index}
                                        className="
                                            bg-slate-800
                                            rounded-xl
                                            p-4
                                        "
                                    >

                                        <div className="font-semibold">
                                            {item.feature}
                                        </div>

                                        <div className="text-slate-400 mt-1">
                                            {item.status}
                                        </div>

                                        <div className="text-slate-300 mt-3 space-y-2 text-sm">
                                            {item.schedule_source && (
                                                <div>
                                                    <strong>Schedule source:</strong> {item.schedule_source}
                                                </div>
                                            )}

                                            {item.planned_completion_date && (
                                                <div>
                                                    <strong>Planned completion:</strong> {formatDate(item.planned_completion_date)}
                                                </div>
                                            )}

                                            {item.schedule_delay_days != null && (
                                                <div>
                                                    <strong>Schedule delay:</strong> {item.schedule_delay_days} workday(s)
                                                </div>
                                            )}

                                            {item.matched_issue && (
                                                <div>
                                                    <strong>Matched issue:</strong> #{item.matched_issue.number} {item.matched_issue.title}
                                                </div>
                                            )}

                                            {item.delay_root_cause && (
                                                <div className="text-slate-200">
                                                    <strong>Root cause:</strong> {item.delay_root_cause}
                                                </div>
                                            )}
                                        </div>

                                    </div>
                                )
                            )
                        }

                    </div>
                )
            }

        </div>
    );
}

export default TimelinePage;
