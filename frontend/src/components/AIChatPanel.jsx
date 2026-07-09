import { useState } from "react";
import { Send, Sparkles, User, Loader2, X } from "lucide-react";
import { askProjectAI, askDelayAnalysisChat } from "../api/chat";

function AIChatPanel({ provider, sessionId, projectKey = "", platform = "", onClose = null, defaultExpanded = false }) {
    const [question, setQuestion] = useState("");
    const [messages, setMessages] = useState([
        { role: "ai", text: "Hello! I'm your Project AI Copilot. I've analyzed your project's data, requirements, and timeline. Ask me anything!" }
    ]);
    const [loading, setLoading] = useState(false);
    const [isExpanded, setIsExpanded] = useState(defaultExpanded);

    async function handleAskAI() {
        if (!question.trim() || loading) return;

        setIsExpanded(true);
        const userMessage = { role: "user", text: question };
        setMessages((prev) => [...prev, userMessage]);
        setLoading(true);
        setQuestion("");

        try {
            const response = sessionId
                ? await askDelayAnalysisChat(question, sessionId, provider, projectKey, platform)
                : await askProjectAI(question, provider);

            setMessages((prev) => [...prev, { role: "ai", text: response.answer }]);
        } catch (error) {
            setMessages((prev) => [...prev, { role: "ai", text: "I'm having trouble connecting to the backend right now." }]);
        }
        setLoading(false);
    }

    const handleKeyDown = (e) => {
        if (e.key === 'Enter') {
            handleAskAI();
        }
    };

    return (
        <div className="lift-card p-0 overflow-hidden border border-hairline bg-card shadow-sm transition-all duration-300">
            <div 
                onClick={() => !onClose && setIsExpanded(!isExpanded)} 
                className="bg-secondary/40 px-6 py-4 border-b border-hairline flex items-center justify-between cursor-pointer hover:bg-secondary/60 transition-colors"
            >
                <div className="flex items-center gap-3">
                    <div className="size-8 rounded-full bg-lavender flex items-center justify-center shrink-0 shadow-sm">
                        <Sparkles className="size-4 text-white" />
                    </div>
                    <div>
                        <h2 className="text-lg font-display text-ink font-bold">Project AI Copilot</h2>
                        <p className="text-xs text-subtext">Powered by {provider === 'groq' ? 'Groq' : 'Gemini'} · Ask anything about your audit</p>
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    {!onClose ? (
                        <button 
                            onClick={(e) => { e.stopPropagation(); setIsExpanded(!isExpanded); }}
                            className="px-4 py-1.5 rounded-full bg-card hover:bg-secondary border border-hairline text-xs font-semibold text-ink transition flex items-center gap-1.5 shadow-2xs"
                        >
                            <span>{isExpanded ? "Minimize Chat" : "Expand Chat"}</span>
                        </button>
                    ) : (
                        <button 
                            onClick={(e) => { e.stopPropagation(); onClose(); }}
                            className="size-9 rounded-full bg-secondary/80 hover:bg-secondary text-subtext hover:text-ink flex items-center justify-center transition shadow-sm cursor-pointer"
                        >
                            <X className="size-5" />
                        </button>
                    )}
                </div>
            </div>

            {isExpanded && (
                <div className={`${onClose ? "h-[480px]" : "h-[380px]"} overflow-y-auto p-6 space-y-6 border-b border-hairline/50 transition-all duration-300 bg-secondary/10`}>
                    {messages.map((message, index) => (
                        <div key={index} className={`flex gap-3 ${message.role === "user" ? "flex-row-reverse" : ""}`}>
                            <div className={`shrink-0 size-8 rounded-full flex items-center justify-center shadow-2xs ${message.role === "user" ? "bg-ink" : "bg-lavender/20"}`}>
                                {message.role === "user" ? <User className="size-4 text-background" /> : <Sparkles className="size-4 text-lavender" />}
                            </div>
                            <div className={`max-w-[80%] px-5 py-3.5 rounded-2xl text-sm leading-relaxed shadow-2xs ${
                                message.role === "user" 
                                    ? "bg-ink text-background rounded-tr-sm" 
                                    : "bg-card text-ink border border-hairline rounded-tl-sm font-sans"
                            }`}>
                                {message.text}
                            </div>
                        </div>
                    ))}
                    {loading && (
                        <div className="flex gap-3">
                            <div className="shrink-0 size-8 rounded-full bg-lavender/20 flex items-center justify-center shadow-2xs">
                                <Sparkles className="size-4 text-lavender" />
                            </div>
                            <div className="px-5 py-3.5 rounded-2xl bg-card text-ink border border-hairline rounded-tl-sm flex items-center gap-2 shadow-2xs">
                                <Loader2 className="size-4 animate-spin text-subtext" />
                                <span className="text-sm text-subtext font-medium">Thinking...</span>
                            </div>
                        </div>
                    )}
                </div>
            )}

            <div className="p-4 bg-card">
                <div className="flex items-center gap-3 relative">
                    <input
                        value={question}
                        onChange={(e) => setQuestion(e.target.value)}
                        onFocus={() => setIsExpanded(true)}
                        onKeyDown={handleKeyDown}
                        placeholder="Ask anything about the project, delays, or developers..."
                        className="flex-1 bg-secondary/30 border border-hairline rounded-full pl-5 pr-12 py-3.5 text-sm outline-none focus:border-lavender focus:bg-card transition-all shadow-inner"
                        disabled={loading}
                    />
                    <button
                        onClick={handleAskAI}
                        disabled={!question.trim() || loading}
                        className="absolute right-2 shrink-0 size-9 rounded-full bg-ink text-background flex items-center justify-center hover:opacity-80 transition disabled:opacity-30 shadow-sm"
                    >
                        <Send className="size-4" />
                    </button>
                </div>
            </div>

            {onClose && (
              <div className="px-6 py-3 border-t border-hairline bg-card/80 flex justify-end">
                <button
                  onClick={onClose}
                  className="px-6 py-2 rounded-full bg-ink text-background text-xs font-bold hover:opacity-90 transition shadow-sm cursor-pointer"
                >
                  Close Copilot
                </button>
              </div>
            )}
        </div>
    );
}

export default AIChatPanel;