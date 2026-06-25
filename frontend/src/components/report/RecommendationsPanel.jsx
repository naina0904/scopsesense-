import React from 'react';
import { Lightbulb } from 'lucide-react';

const RecommendationsPanel = ({ recommendations }) => {
    if (!recommendations || recommendations.length === 0) {
        return null;
    }

    return (
        <div className="soft-card p-8 mb-6">
            <h3 className="font-display text-2xl mb-6">Recommendations</h3>
            <div className="bg-lavender/10 border border-lavender/30 rounded-2xl p-6">
                <ul className="space-y-4">
                    {recommendations.map((rec, index) => (
                        <li key={index} className="flex gap-3 text-ink leading-relaxed text-sm">
                            <Lightbulb className="size-5 text-lavender shrink-0 mt-0.5" />
                            <span>{rec}</span>
                        </li>
                    ))}
                </ul>
            </div>
        </div>
    );
};

export default RecommendationsPanel;
