import {
    useEffect,
    useState
} from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, ArrowRight } from "lucide-react";

import axios from "axios";
import { API_BASE_URL } from "../config";

import FeatureCard from "../components/FeatureCard";
import { useAudit } from "../context/AuditContext";
import { PageHeader, PageBody } from "../components/ui/PageChrome";
import { StageGuideCard } from "../components/ui/StageGuideCard";

// ZIP binary header as it appears when a DOCX/XLSX blob is misread as text
const ZIP_BINARY_PREFIX = "PK\u0003\u0004";

function FeaturesPage() {
    const navigate = useNavigate();
    const { registerStepAction, auditResult, auditSession, getPlannedFeatures, fetchActiveSession, openHelp } = useAudit();

    const [features, setFeatures] = useState([]);
    const [hasAudit, setHasAudit] = useState(false);

    useEffect(() => {
        registerStepAction({
            onPrev: () => navigate("/upload-srs"),
            onNext: () => navigate("/configuration")
        });
    });

    useEffect(() => {
        fetchActiveSession().catch(() => {});
    }, [fetchActiveSession]);

    useEffect(() => {

        async function loadLatestAudit() {

            try {
                // 1. SSOT Memory Check: if we already ran or loaded an audit right in AuditContext
                const memoryFeatures =
                    auditResult?.semantic_features ||
                    auditResult?.delay_analysis?.semantic_features ||
                    [];

                if (memoryFeatures.length > 0) {
                    setHasAudit(true);
                    const validFeatures = memoryFeatures.filter(feature => {
                        const name = feature.feature_name || "";
                        return !name.startsWith(ZIP_BINARY_PREFIX) && name.length <= 200;
                    });
                    setFeatures(validFeatures.map(feature => ({
                        name: feature.feature_name,
                        developer: (feature.assigned_developers || []).join(", "),
                        status: feature.implementation_status || "Detected"
                    })));
                    return;
                }

                // 2. Check live planned features from active session (fetching session if null on refresh)
                let currentSession = auditSession;
                if (!currentSession?.id) {
                    try {
                        currentSession = await fetchActiveSession();
                    } catch (err) {}
                }

                if (currentSession?.id) {
                    try {
                        const planned = await getPlannedFeatures(currentSession.id);
                        const table1 = planned?.table1 || [];
                        if (table1.length > 0) {
                            setHasAudit(true);
                            setFeatures(table1.map(item => ({
                                name: item.requirement || item.module || "Requirement",
                                developer: item.assigned_developer || "Unassigned",
                                status: "Planned (SRS)"
                            })));
                            return;
                        }
                    } catch (err) {
                        // Silent fallback if session fetch not ready yet
                    }
                }

                // 3. Fallback: check localStorage or fetch latest audit across server
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
                    response.data.result || response.data || {};

                const semanticFeatures =
                    latest.semantic_features ||
                    latest.delay_analysis?.semantic_features ||
                    [];

                if (semanticFeatures.length > 0 || response.data.status === "success" || latest.status === "COMPLETED") {
                    setHasAudit(true);
                }

                if (semanticFeatures.length > 0) {

                    const validFeatures = semanticFeatures.filter(
                        feature => {
                            const name = feature.feature_name || "";
                            return !name.startsWith(ZIP_BINARY_PREFIX) && name.length <= 200;
                        }
                    );

                    setFeatures(
                        validFeatures.map(
                            (feature) => ({
                                name:
                                    feature.feature_name,
                                developer:
                                    (
                                        feature.assigned_developers
                                        || []
                                    ).join(", "),
                                status:
                                    feature.implementation_status || "Detected"
                            })
                        )
                    );
                }

            } catch (error) {

                console.error("Failed to load features:", error);
            }
        }

        loadLatestAudit();

    }, [auditResult, auditSession]);

    return (
        <>
            <PageHeader
                title="Planned Project Requirements"
                lede="AI-extracted feature requirements, assigned developers, and baseline estimates."
                helpSection="stage-2-planned-requirements"
            />
            <PageBody>
                {!hasAudit ? (
                    <div className="text-center py-16 text-subtext bg-card rounded-3xl border border-hairline p-8 max-w-xl mx-auto shadow-sm">
                        <p className="text-2xl font-bold text-ink">No audit data yet</p>
                        <p className="text-sm mt-2 text-subtext">
                            Run a full audit or upload your SRS requirement document to detect features.
                        </p>
                        <StageGuideCard
                            sectionId="stage-2-planned-requirements"
                            title="📖 Complete Stage 2 Guide & Planned Requirements Walkthrough"
                            description="Explore how feature estimates, baseline budgets, and assignments are structured."
                        />
                    </div>
                ) : features.length === 0 ? (
                    <div className="text-center py-16 text-subtext bg-card rounded-3xl border border-hairline p-8 max-w-xl mx-auto shadow-sm">
                        <p className="text-2xl font-bold text-ink">No features detected</p>
                        <p className="text-sm mt-2 text-subtext">
                            The latest audit did not detect any semantic features.
                        </p>
                        <StageGuideCard
                            sectionId="stage-2-planned-requirements"
                            title="📖 Complete Stage 2 Guide & Planned Requirements Walkthrough"
                            description="Explore how feature estimates, baseline budgets, and assignments are structured."
                        />
                    </div>
                ) : (
                    <div className="space-y-6">
                        <StageGuideCard
                            sectionId="stage-2-planned-requirements"
                            title="📖 Complete Stage 2 Guide & Planned Requirements Walkthrough"
                            description="Explore how feature estimates, baseline budgets, and assignments are structured."
                        />
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            {features.map((feature, index) => (
                                <FeatureCard key={index} feature={feature} />
                            ))}
                        </div>
                    </div>
                )}
            </PageBody>
        </>
    );
}

export default FeaturesPage;
