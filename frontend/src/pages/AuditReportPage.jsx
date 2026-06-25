import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../api/client';
import { PageHeader, PageBody } from '../components/ui/PageChrome';
import { Loader2, ArrowLeft } from 'lucide-react';

import ExecutiveSummaryCard from '../components/report/ExecutiveSummaryCard';
import RiskSummaryPanel from '../components/report/RiskSummaryPanel';
import FindingsTable from '../components/report/FindingsTable';
import RecommendationsPanel from '../components/report/RecommendationsPanel';

const AuditReportPage = () => {
    const { auditId } = useParams();
    const navigate = useNavigate();
    
    const [report, setReport] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchReport = async () => {
            try {
                const endpoint = auditId === 'latest' ? '/delay/results/latest/active' : `/delay/results/${auditId}`;
                const response = await api.get(endpoint);
                
                if (response.data && response.data.audit_report) {
                    setReport(response.data.audit_report);
                } else {
                    setError("No audit report found for this session.");
                }
            } catch (err) {
                console.error("Error fetching audit report:", err);
                setError(err.response?.data?.detail || "Failed to load audit report. Please try again.");
            } finally {
                setLoading(false);
            }
        };

        fetchReport();
    }, [auditId]);

    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[50vh] space-y-4">
                <Loader2 className="size-8 text-ink animate-spin" />
                <div className="text-xl font-display text-ink">Generating report...</div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="p-8">
                <div className="bg-rose/20 border border-rose text-ink px-4 py-3 rounded-xl text-sm font-medium">
                    <h3 className="font-semibold text-lg mb-2">Error Loading Report</h3>
                    <p>{error}</p>
                    <button 
                        onClick={() => navigate('/results')} 
                        className="mt-4 px-4 py-2 bg-ink text-background rounded-lg hover:opacity-90 transition font-medium"
                    >
                        Back to Results
                    </button>
                </div>
            </div>
        );
    }

    if (!report) return null;

    return (
        <>
            <PageHeader
                eyebrow={`Report Generated: ${new Date(report.generated_at).toLocaleString()}`}
                title="Deep Audit Report"
                lede="Comprehensive findings, risks, and recommendations."
                primary={{ label: "Back to Dashboard", icon: ArrowLeft, onClick: () => navigate('/results') }}
            />
            
            <PageBody>
                <div className="space-y-10 max-w-6xl mx-auto">
                    <ExecutiveSummaryCard summary={report.executive_summary} />
                    <RiskSummaryPanel riskSummary={report.risk_summary} />
                    <RecommendationsPanel recommendations={report.recommendations} />
                    <FindingsTable findings={report.findings} />
                    
                    <div className="mt-12 text-center text-subtext text-xs uppercase tracking-wider">
                        Report ID: {report.report_id}
                    </div>
                </div>
            </PageBody>
        </>
    );
};

export default AuditReportPage;
