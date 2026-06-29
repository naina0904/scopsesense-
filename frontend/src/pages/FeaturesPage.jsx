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

// ZIP binary header as it appears when a DOCX/XLSX blob is misread as text
const ZIP_BINARY_PREFIX = "PK\u0003\u0004";

function FeaturesPage() {
    const navigate = useNavigate();
    const { registerStepAction } = useAudit();

    const [features, setFeatures] = useState([]);
    const [hasAudit, setHasAudit] = useState(false);

    useEffect(() => {
        registerStepAction({
            onPrev: () => navigate("/upload-srs"),
            onNext: () => navigate("/configuration")
        });
    });

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

                const semanticFeatures =
                    latest.semantic_features || [];

                setHasAudit(true);

                if (semanticFeatures.length > 0) {

                    // Only block names that are literally ZIP binary garbage.
                    // Valid acronyms like "PKI Authentication" pass safely.
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

                console.error(error);
            }
        }

        loadLatestAudit();

    }, []);

    return (

        <div className="space-y-8">

            <div>

                <h1 className="text-4xl font-bold">
                    Project Features
                </h1>

                <p className="text-slate-400 mt-2">
                    AI-detected feature ownership and completion tracking
                </p>

            </div>

            {!hasAudit ? (

                <div className="text-center py-20 text-slate-500">
                    <p className="text-xl font-semibold">No audit data yet</p>
                    <p className="text-sm mt-2">
                        Run a full audit to detect features from your repository and SRS.
                    </p>
                </div>

            ) : features.length === 0 ? (

                <div className="text-center py-20 text-slate-500">
                    <p className="text-xl font-semibold">No features detected</p>
                    <p className="text-sm mt-2">
                        The latest audit did not detect any semantic features.
                    </p>
                </div>

            ) : (

                <div className="grid grid-cols-2 gap-6">

                    {
                        features.map((feature, index) => (

                            <FeatureCard
                                key={index}
                                feature={feature}
                            />
                        ))
                    }

                </div>

            )}

        </div>
    );
}

export default FeaturesPage;
