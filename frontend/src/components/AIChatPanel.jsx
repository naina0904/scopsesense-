import { useState } from "react";
import { Send, Sparkles, User, Loader2 } from "lucide-react";
import { askProjectAI, askDelayAnalysisChat } from "../api/chat";

function AIChatPanel({ provider, sessionId, projectKey = "", platform = "" }) {
    const [question, setQuestion] = useState("");
    const [messages, setMessages] = useState([
        { role: "ai", text: "Hello! I'm your Project AI Copilot. I've analyzed your project's data, requirements, and timeline. Ask me anything!" }
    ]);
    const [loading, setLoading] = useState(false);

    async function handleAskAI() {
        if (!question.trim() || loading) return;

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
        <div className="lift-card p-0 overflow-hidden border border-hairline bg-card">
            <div className="bg-secondary/40 px-6 py-4 border-b border-hairline flex items-center gap-3">
                <div className="size-8 rounded-full bg-lavender flex items-center justify-center">
                    <Sparkles className="size-4 text-white" />
                </div>
                <div>
                    <h2 className="text-lg font-display text-ink">Project AI Copilot</h2>
                    <p className="text-xs text-subtext">Powered by {provider === 'groq' ? 'Groq' : 'Gemini'}</p>
                </div>
            </div>

            <div className="h-[400px] overflow-y-auto p-6 space-y-6">
                {messages.map((message, index) => (
                    <div key={index} className={`flex gap-3 ${message.role === "user" ? "flex-row-reverse" : ""}`}>
                        <div className={`shrink-0 size-8 rounded-full flex items-center justify-center ${message.role === "user" ? "bg-ink" : "bg-lavender/20"}`}>
                            {message.role === "user" ? <User className="size-4 text-background" /> : <Sparkles className="size-4 text-lavender" />}
                        </div>
                        <div className={`max-w-[80%] px-5 py-3.5 rounded-2xl text-sm leading-relaxed ${
                            message.role === "user" 
                                ? "bg-ink text-background rounded-tr-sm" 
                                : "bg-secondary/30 text-ink border border-hairline rounded-tl-sm"
                        }`}>
                            {message.text}
                        </div>
                    </div>
                ))}
                {loading && (
                    <div className="flex gap-3">
                        <div className="shrink-0 size-8 rounded-full bg-lavender/20 flex items-center justify-center">
                            <Sparkles className="size-4 text-lavender" />
                        </div>
                        <div className="px-5 py-3.5 rounded-2xl bg-secondary/30 text-ink border border-hairline rounded-tl-sm flex items-center gap-2">
                            <Loader2 className="size-4 animate-spin text-subtext" />
                            <span className="text-sm text-subtext">Thinking...</span>
                        </div>
                    </div>
                )}
            </div>

            <div className="p-4 border-t border-hairline bg-card">
                <div className="flex items-center gap-3 relative">
                    <input
                        value={question}
                        onChange={(e) => setQuestion(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Ask anything about the project..."
                        className="flex-1 bg-secondary/30 border border-hairline rounded-full pl-5 pr-12 py-3.5 text-sm outline-none focus:border-lavender transition-colors"
                        disabled={loading}
                    />
                    <button
                        onClick={handleAskAI}
                        disabled={!question.trim() || loading}
                        className="absolute right-2 shrink-0 size-9 rounded-full bg-ink text-background flex items-center justify-center hover:opacity-80 transition disabled:opacity-30"
                    >
                        <Send className="size-4" />
                    </button>
                </div>
            </div>
        </div>
    );
}

export default AIChatPanel;