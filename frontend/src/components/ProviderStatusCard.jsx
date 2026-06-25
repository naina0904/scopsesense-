function ProviderStatusCard({ metadata = {} }) {
    if (!metadata) {
        return null;
    }

    const statuses = metadata.provider_statuses || {};

    const renderProviderStatus = (name, status) => {
        if (!status) {
            return null;
        }

        const label = status.active
            ? "active"
            : status.enabled
                ? "enabled"
                : "disabled";

        return (
            <div key={name} className="flex justify-between gap-4 px-3 py-2 rounded-xl bg-slate-800 border border-slate-700">
                <div>
                    <div className="font-semibold">{name}</div>
                    <div className="text-slate-400 text-sm">{status.preferred ? "preferred" : "fallback"}</div>
                </div>
                <div className="text-right">
                    <div className="text-sm text-slate-300">{label}</div>
                    <div className="text-xs text-slate-500">{status.configured ? "configured" : "not configured"}</div>
                </div>
            </div>
        );
    };

    return (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
            <div className="flex items-center gap-3 mb-4">
                <div className="text-2xl font-semibold">AI Provider Status</div>
            </div>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
                    <div className="text-slate-400 text-sm">Requested provider</div>
                    <div className="font-semibold">{metadata.requested_provider || "unknown"}</div>
                </div>
                <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
                    <div className="text-slate-400 text-sm">Selected provider</div>
                    <div className="font-semibold">{metadata.selected_provider || "unknown"}</div>
                </div>
                <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
                    <div className="text-slate-400 text-sm">Provider used</div>
                    <div className="font-semibold">{metadata.provider_used || "none"}</div>
                </div>
                <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
                    <div className="text-slate-400 text-sm">FAQs applicable</div>
                    <div className="font-semibold">{metadata.faqs_applicable ? "yes" : "no"}</div>
                </div>
            </div>
            <div className="space-y-3">
                <div className="text-slate-400 text-sm">Provider order</div>
                <div className="flex flex-wrap gap-2">
                    {(metadata.provider_order || []).map(provider => (
                        <span key={provider} className="rounded-full bg-slate-800 px-3 py-1 text-xs text-slate-200 border border-slate-700">
                            {provider}
                        </span>
                    ))}
                </div>
            </div>
            <div className="space-y-2">
                {Object.entries(statuses).map(([name, status]) => renderProviderStatus(name, status))}
            </div>
            {metadata.provider_fallbacks && metadata.provider_fallbacks.length > 0 && (
                <div className="text-slate-300 text-sm">
                    <strong>Fallback path:</strong> {metadata.provider_fallbacks.join(", ")}
                </div>
            )}
        </div>
    );
}

export default ProviderStatusCard;
