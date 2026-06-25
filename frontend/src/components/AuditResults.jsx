import {
    AlertTriangle,
    ShieldCheck,
    Brain,
    Users
} from "lucide-react";

import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    Tooltip,
    ResponsiveContainer
} from "recharts";

import DependencyGraph from "./DependencyGraph";
import VarianceChart from "./VarianceChart";
import OwnershipTimeline from "./OwnershipTimeline";
import LowConfidenceMatchList from "./LowConfidenceMatchList";
import RootCausePanel from "./RootCausePanel";


function AuditResults({
    results
}) {

    const audit =
        results.result || results;

    const implementationData =
        audit.implementation_analysis
        || [];

    const driftData =
        audit.architectural_drift
        || [];

    const riskData =
        audit.predictive_risks
        || [];

    return (

        <div className="space-y-8">

            {/* KPI */}

            <div
                className="
                grid
                grid-cols-1
                md:grid-cols-4
                gap-6
            "
            >

                {/* HEALTH */}

                <div
                    className="
                    bg-slate-900
                    border
                    border-slate-800
                    rounded-2xl
                    p-6
                "
                >

                    <div
                        className="
                        flex
                        items-center
                        justify-between
                    "
                    >

                        <div>

                            <p
                                className="
                                text-slate-400
                                text-sm
                            "
                            >

                                Health Score

                            </p>

                            <h2
                                className="
                                text-3xl
                                font-bold
                                mt-2
                            "
                            >

                                {
                                    audit.health_score
                                }%

                            </h2>

                        </div>

                        <ShieldCheck
                            size={32}
                        />

                    </div>

                </div>


                {/* SEMANTIC */}

                <div
                    className="
                    bg-slate-900
                    border
                    border-slate-800
                    rounded-2xl
                    p-6
                "
                >

                    <div
                        className="
                        flex
                        items-center
                        justify-between
                    "
                    >

                        <div>

                            <p
                                className="
                                text-slate-400
                                text-sm
                            "
                            >

                                Semantic Confidence

                            </p>

                            <h2
                                className="
                                text-3xl
                                font-bold
                                mt-2
                            "
                            >

                                {
                                    audit.semantic_confidence
                                }%

                            </h2>

                        </div>

                        <Brain
                            size={32}
                        />

                    </div>

                </div>


                {/* RISKS */}

                <div
                    className="
                    bg-slate-900
                    border
                    border-slate-800
                    rounded-2xl
                    p-6
                "
                >

                    <div
                        className="
                        flex
                        items-center
                        justify-between
                    "
                    >

                        <div>

                            <p
                                className="
                                text-slate-400
                                text-sm
                            "
                            >

                                Drift Risks

                            </p>

                            <h2
                                className="
                                text-3xl
                                font-bold
                                mt-2
                            "
                            >

                                {
                                    driftData.length
                                }

                            </h2>

                        </div>

                        <AlertTriangle
                            size={32}
                        />

                    </div>

                </div>


                {/* PROVIDER */}

                <div
                    className="
                    bg-slate-900
                    border
                    border-slate-800
                    rounded-2xl
                    p-6
                "
                >

                    <div
                        className="
                        flex
                        items-center
                        justify-between
                    "
                    >

                        <div>

                            <p
                                className="
                                text-slate-400
                                text-sm
                            "
                            >

                                AI Provider

                            </p>

                            <h2
                                className="
                                text-2xl
                                font-bold
                                mt-2
                                capitalize
                            "
                            >

                                {
                                    audit.provider
                                }

                            </h2>

                        </div>

                        <Users
                            size={32}
                        />

                    </div>

                </div>

            </div>


            {/* IMPLEMENTATION */}

            <div
                className="
                bg-slate-900
                border
                border-slate-800
                rounded-2xl
                p-6
            "
            >

                <div className="mb-6">

                    <h2
                        className="
                        text-2xl
                        font-bold
                    "
                    >

                        Implementation Analysis

                    </h2>

                </div>

                <div
                    className="
                    h-[400px]
                "
                >

                    <ResponsiveContainer
                        width="100%"
                        height="100%"
                    >

                        <BarChart
                            data={
                                implementationData
                            }
                        >

                            <XAxis
                                dataKey="requirement"
                            />

                            <YAxis />

                            <Tooltip />

                            <Bar
                                dataKey="confidence"
                                fill="#ffffff"
                            />

                        </BarChart>

                    </ResponsiveContainer>

                </div>

            </div>


            {/* RISKS */}

            <div
                className="
                bg-slate-900
                border
                border-slate-800
                rounded-2xl
                p-6
            "
            >

                <h2
                    className="
                    text-2xl
                    font-bold
                    mb-6
                "
                >

                    Predictive Risks

                </h2>

                <div className="space-y-4">

                    {

                        riskData.map(
                            (
                                risk,
                                index
                            ) => (

                                <div

                                    key={index}

                                    className="
                                    bg-slate-800
                                    rounded-xl
                                    p-5
                                "
                                >

                                    <div
                                        className="
                                        flex
                                        justify-between
                                    "
                                    >

                                        <div>

                                            <h3
                                                className="
                                                font-semibold
                                            "
                                            >

                                                {
                                                    risk.type
                                                }

                                            </h3>

                                            <p
                                                className="
                                                text-slate-400
                                                mt-2
                                            "
                                            >

                                                {
                                                    risk.message
                                                }

                                            </p>

                                        </div>

                                        <div
                                            className="
                                            text-red-400
                                            font-bold
                                        "
                                        >

                                            {
                                                risk.probability
                                            }%

                                        </div>

                                    </div>

                                </div>
                            )
                        )
                    }

                </div>

            </div>

{/* NEW VISUALIZATION COMPONENTS */}
<VarianceChart hotspots={audit.hotspots || []} />
<OwnershipTimeline featureOwnership={audit.feature_ownership || []} />
<LowConfidenceMatchList insights={audit.insights || []} />
<RootCausePanel causality={audit.causality || []} />


            {/* DEPENDENCY GRAPH */}

            <div
                className="
                bg-slate-900
                border
                border-slate-800
                rounded-2xl
                p-6
            "
            >

                <h2
                    className="
                    text-2xl
                    font-bold
                    mb-6
                "
                >

                    Dependency Graph

                </h2>

                <DependencyGraph

                    dependencies={
                        audit.dependencies || []
                    }
                />

            </div>


            {/* SUMMARY */}

            <div
                className="
                bg-slate-900
                border
                border-slate-800
                rounded-2xl
                p-6
            "
            >

                <h2
                    className="
                    text-2xl
                    font-bold
                    mb-6
                "
                >

                    AI Summary

                </h2>

                <div
                    className="
                    whitespace-pre-wrap
                    text-slate-300
                    leading-8
                "
                >

                    {
                        audit.ai_summary
                    }

                </div>

            </div>

        </div>
    );
}

export default AuditResults;