import { AlertCircle, Key, Globe, Zap } from "lucide-react";

function JiraSetupHelper() {
    return (
        <div className="bg-blue-950 border border-blue-800 rounded-3xl p-8 space-y-6">
            <div className="flex items-center gap-3">
                <AlertCircle className="text-blue-400" size={24} />
                <h3 className="text-xl font-bold text-blue-200">Jira Setup Guide</h3>
            </div>

            <div className="space-y-4">
                <div className="bg-blue-900/50 rounded-2xl p-5">
                    <div className="flex items-start gap-3 mb-3">
                        <Globe size={20} className="text-blue-300 flex-shrink-0 mt-1" />
                        <div>
                            <h4 className="font-semibold text-blue-200">Jira Domain</h4>
                            <p className="text-blue-300 text-sm mt-1">
                                For Jira Cloud: <span className="font-mono bg-blue-800 px-2 py-1 rounded">your-domain.atlassian.net</span>
                            </p>
                            <p className="text-blue-400 text-xs mt-2">
                                ℹ️ Do NOT include <span className="font-mono">https://</span> or trailing slash
                            </p>
                        </div>
                    </div>
                </div>

                <div className="bg-blue-900/50 rounded-2xl p-5">
                    <div className="flex items-start gap-3 mb-3">
                        <Key size={20} className="text-blue-300 flex-shrink-0 mt-1" />
                        <div>
                            <h4 className="font-semibold text-blue-200">API Token</h4>
                            <p className="text-blue-300 text-sm mt-1">
                                Generate at: <span className="font-mono bg-blue-800 px-2 py-1 rounded text-xs">id.atlassian.com/manage-profile/security/api-tokens</span>
                            </p>
                            <p className="text-blue-400 text-xs mt-2">
                                ℹ️ Use your email address (not username) with the token
                            </p>
                        </div>
                    </div>
                </div>

                <div className="bg-blue-900/50 rounded-2xl p-5">
                    <div className="flex items-start gap-3 mb-3">
                        <Zap size={20} className="text-blue-300 flex-shrink-0 mt-1" />
                        <div>
                            <h4 className="font-semibold text-blue-200">Project Key</h4>
                            <p className="text-blue-300 text-sm mt-1">
                                Usually UPPERCASE: <span className="font-mono bg-blue-800 px-2 py-1 rounded">SCOPE</span>, <span className="font-mono bg-blue-800 px-2 py-1 rounded">JIRA</span>, etc.
                            </p>
                            <p className="text-blue-400 text-xs mt-2">
                                ℹ️ Find it in your Jira board URL: <span className="font-mono">jira.atlassian.net/browse/SCOPE-123</span>
                            </p>
                        </div>
                    </div>
                </div>
            </div>

            <div className="bg-blue-800/30 border border-blue-700/50 rounded-2xl p-4">
                <p className="text-blue-300 text-sm">
                    <span className="font-semibold">Tip:</span> Click "Validate Credentials" to test your connection before running analysis.
                </p>
            </div>
        </div>
    );
}

export default JiraSetupHelper;
