import React from 'react';

const FindingsTable = ({ findings }) => {
    if (!findings || findings.length === 0) {
        return (
            <div className="soft-card p-8 mb-6">
                <h3 className="font-display text-2xl mb-4">Detailed Findings</h3>
                <p className="text-subtext italic">No findings to display.</p>
            </div>
        );
    }

    const getSeverityBadge = (severity) => {
        switch (severity) {
            case 'CRITICAL': return <span className="chip bg-rose/20 text-risk">CRITICAL</span>;
            case 'HIGH': return <span className="chip bg-rose/10 text-risk">HIGH</span>;
            case 'MEDIUM': return <span className="chip bg-warning/20 text-warning">MEDIUM</span>;
            case 'LOW': return <span className="chip bg-pista/20 text-success">LOW</span>;
            default: return <span className="chip bg-secondary text-ink">{severity}</span>;
        }
    };

    return (
        <div className="soft-card overflow-hidden mb-6">
            <div className="px-8 py-6 border-b border-hairline">
                <h3 className="font-display text-2xl">Detailed Findings</h3>
            </div>
            <div className="overflow-x-auto">
                <div className="min-w-[800px]">
                    <div className="grid grid-cols-12 px-8 py-3 text-[11px] uppercase tracking-wider text-subtext bg-beige/40 border-b border-hairline">
                        <div className="col-span-2">Feature ID</div>
                        <div className="col-span-2">Category</div>
                        <div className="col-span-2">Severity</div>
                        <div className="col-span-6">Message</div>
                    </div>
                    <div className="divide-y divide-hairline">
                        {findings.map((finding) => (
                            <div key={finding.id} className="grid grid-cols-12 px-8 py-4 items-center hover:bg-secondary/50 transition">
                                <div className="col-span-2 text-sm font-medium text-ink">{finding.feature_id}</div>
                                <div className="col-span-2 text-sm text-subtext">{finding.category}</div>
                                <div className="col-span-2 text-sm">{getSeverityBadge(finding.severity)}</div>
                                <div className="col-span-6 text-sm text-ink/80 leading-relaxed pr-4">{finding.message}</div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default FindingsTable;
