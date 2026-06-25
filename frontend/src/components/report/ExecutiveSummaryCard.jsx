import React from 'react';
import { Sparkles } from 'lucide-react';

const ExecutiveSummaryCard = ({ summary }) => {
    return (
        <div className="lift-card p-10 grain mb-6">
            <div className="flex items-center gap-2 text-xs text-subtext mb-3"><Sparkles className="size-3.5" /> Executive Summary</div>
            <div className="prose prose-invert max-w-none text-ink">
                <p className="font-display text-2xl leading-relaxed text-ink/90">{summary}</p>
            </div>
        </div>
    );
};

export default ExecutiveSummaryCard;
