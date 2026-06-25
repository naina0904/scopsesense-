import React from 'react';

const RiskSummaryPanel = ({ riskSummary }) => {
    const total = Object.values(riskSummary).reduce((a, b) => a + b, 0);

    const getRiskColor = (level) => {
        switch (level) {
            case 'CRITICAL': return 'bg-rose';
            case 'HIGH': return 'bg-rose/60';
            case 'MEDIUM': return 'bg-warning';
            case 'LOW': return 'bg-pista';
            default: return 'bg-secondary';
        }
    };

    return (
        <div className="soft-card p-8 mb-6">
            <h3 className="font-display text-2xl mb-6">Risk Distribution</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {Object.entries(riskSummary).map(([level, count]) => (
                    <div key={level} className="flex flex-col p-5 bg-card border border-hairline rounded-2xl hover:border-ink/20 transition">
                        <span className="text-[11px] uppercase tracking-wider text-subtext font-medium">{level}</span>
                        <div className="flex items-center mt-3">
                            <div className={`size-3 rounded-full mr-3 ${getRiskColor(level)}`}></div>
                            <span className="font-display text-4xl text-ink">{count}</span>
                        </div>
                    </div>
                ))}
            </div>
            {total === 0 && (
                <div className="mt-6 p-4 bg-pista/20 border border-pista/30 text-ink rounded-xl font-medium text-sm flex items-center gap-2">
                    <div className="size-2 rounded-full bg-pista"></div>
                    No risks were detected during this audit.
                </div>
            )}
        </div>
    );
};

export default RiskSummaryPanel;
