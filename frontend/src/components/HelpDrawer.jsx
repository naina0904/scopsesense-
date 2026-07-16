import { useEffect, useRef, useState } from "react";
import { X, BookOpen, HelpCircle, ChevronRight, Sparkles, ExternalLink, ArrowLeft } from "lucide-react";
import { USER_GUIDE_CHAPTERS } from "../data/userGuideData";
import { useAudit } from "../context/AuditContext";

// Helper to parse inline **bold** and `code` formatting
function parseInlineText(str) {
  if (!str) return null;
  const parts = str.split(/(\*\*.*?\*\*|`.*?`)/g);
  return parts.map((part, index) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return (
        <strong key={index} className="text-ink font-semibold">
          {part.slice(2, -2)}
        </strong>
      );
    }
    if (part.startsWith("`") && part.endsWith("`")) {
      return (
        <code key={index} className="px-1.5 py-0.5 rounded bg-secondary border border-hairline font-mono text-[11px] font-bold text-ink">
          {part.slice(1, -1)}
        </code>
      );
    }
    return part;
  });
}

// Helper to format structured bullet lists, numbered steps, and callout blocks
function formatSectionContent(text) {
  if (!text) return null;
  const lines = text.split("\n");
  return (
    <div className="space-y-2 font-sans text-xs sm:text-sm text-subtext leading-relaxed">
      {lines.map((line, i) => {
        const trimmed = line.trim();
        if (!trimmed) return <div key={i} className="h-1" />;

        // Bullet points (• or -)
        if (trimmed.startsWith("• ") || trimmed.startsWith("- ")) {
          const content = trimmed.replace(/^[•-]\s+/, "");
          return (
            <div key={i} className="flex items-start gap-2.5 my-1">
              <span className="text-info font-bold text-sm mt-0.5 shrink-0">•</span>
              <span className="flex-1 text-subtext">{parseInlineText(content)}</span>
            </div>
          );
        }

        // Numbered steps (1. , 2. , etc.)
        const numMatch = trimmed.match(/^(\d+\.)\s+(.*)/);
        if (numMatch) {
          return (
            <div key={i} className="flex items-start gap-2.5 my-1">
              <span className="px-1.5 py-0.5 rounded bg-info/10 text-info font-mono font-bold text-[11px] shrink-0 mt-0.5">
                {numMatch[1]}
              </span>
              <span className="flex-1 text-subtext">{parseInlineText(numMatch[2])}</span>
            </div>
          );
        }

        // Callout blocks (> text)
        if (trimmed.startsWith(">")) {
          const content = trimmed.replace(/^>\s*/, "");
          return (
            <div key={i} className="p-3 my-2 rounded-xl bg-info/10 border border-info/20 text-ink text-xs font-medium">
              {parseInlineText(content)}
            </div>
          );
        }

        // Standard paragraph line
        return (
          <p key={i} className="my-1 text-subtext">
            {parseInlineText(line)}
          </p>
        );
      })}
    </div>
  );
}

export default function HelpDrawer() {
  const { isHelpOpen, closeHelp, helpActiveSection } = useAudit();
  const [selectedChapterId, setSelectedChapterId] = useState("quick-start");
  const contentRef = useRef(null);

  useEffect(() => {
    if (helpActiveSection) {
      setSelectedChapterId(helpActiveSection);
    }
  }, [helpActiveSection, isHelpOpen]);

  useEffect(() => {
    if (isHelpOpen && contentRef.current) {
      contentRef.current.scrollTo({ top: 0, behavior: "smooth" });
    }
  }, [selectedChapterId, isHelpOpen]);

  // Handle ESC key to dismiss
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === "Escape" && isHelpOpen) {
        closeHelp();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isHelpOpen, closeHelp]);

  if (!isHelpOpen) return null;

  const currentChapter = USER_GUIDE_CHAPTERS.find((c) => c.id === selectedChapterId) || USER_GUIDE_CHAPTERS[0];

  return (
    <div className="fixed inset-0 z-50 overflow-hidden flex justify-end animate-in fade-in duration-200">
      {/* Backdrop */}
      <div 
        onClick={closeHelp}
        className="fixed inset-0 bg-ink/60 backdrop-blur-sm transition-opacity cursor-pointer"
        aria-hidden="true"
      />

      {/* Slide-out Drawer */}
      <div className="relative w-full sm:w-[580px] md:w-[680px] lg:w-[760px] max-w-full bg-background/95 backdrop-blur-xl border-l border-hairline shadow-2xl flex flex-col h-full z-10 animate-in slide-in-from-right duration-300">
        
        {/* Top Header Bar */}
        <div className="h-16 px-6 border-b border-hairline bg-card/60 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <div className="size-9 rounded-2xl bg-info/15 border border-info/30 grid place-items-center text-info shadow-sm">
              <BookOpen className="size-5" />
            </div>
            <div>
              <h3 className="font-display font-bold text-sm text-ink flex items-center gap-2">
                ScopeSense v2 User Guide & Management Manual
              </h3>
              <p className="text-[11px] text-subtext flex items-center gap-1.5">
                <Sparkles className="size-3 text-info" />
                Enterprise Forensic Audit & Predictive Intelligence
              </p>
            </div>
          </div>

          <button
            onClick={closeHelp}
            className="size-9 rounded-full border border-hairline bg-card hover:bg-secondary hover:text-ink transition-colors grid place-items-center text-subtext cursor-pointer shadow-sm"
            title="Close Help Drawer (Esc)"
          >
            <X className="size-4.5" />
          </button>
        </div>

        {/* Main Body Grid: Left Navigation & Right Content */}
        <div className="flex-1 flex overflow-hidden min-h-0">
          
          {/* Left Navigation (Chapter Selector) */}
          <div className="w-56 sm:w-64 border-r border-hairline bg-card/30 overflow-y-auto p-3 shrink-0 hidden sm:block space-y-1">
            <div className="px-3 py-2 text-[11px] font-bold text-subtext uppercase tracking-wider">
              Table of Contents
            </div>
            
            {USER_GUIDE_CHAPTERS.map((chapter) => {
              const active = chapter.id === selectedChapterId;
              return (
                <button
                  key={chapter.id}
                  onClick={() => setSelectedChapterId(chapter.id)}
                  className={`w-full text-left p-2.5 rounded-xl transition-all flex items-center justify-between group cursor-pointer ${
                    active 
                      ? "bg-ink text-background font-bold shadow-sm" 
                      : "hover:bg-secondary/60 text-subtext hover:text-ink"
                  }`}
                >
                  <div className="min-w-0 pr-2">
                    <div className="text-xs truncate">{chapter.title}</div>
                    <div className={`text-[10px] truncate ${active ? "text-background/70" : "text-subtext/70"}`}>
                      {chapter.category}
                    </div>
                  </div>
                  <ChevronRight className={`size-3.5 shrink-0 transition-transform ${active ? "text-background translate-x-0.5" : "text-subtext group-hover:translate-x-0.5"}`} />
                </button>
              );
            })}
          </div>

          {/* Right Content Area */}
          <div ref={contentRef} className="flex-1 overflow-y-auto p-6 sm:p-8 space-y-6 bg-background/40">
            
            {/* Mobile Chapter Selector Dropdown */}
            <div className="block sm:hidden mb-4">
              <label className="text-[11px] font-bold text-subtext uppercase block mb-1.5">Select Chapter:</label>
              <select
                value={selectedChapterId}
                onChange={(e) => setSelectedChapterId(e.target.value)}
                className="w-full h-10 px-3 rounded-xl bg-card border border-hairline text-xs font-bold text-ink focus:outline-none focus:border-info"
              >
                {USER_GUIDE_CHAPTERS.map((c) => (
                  <option key={c.id} value={c.id}>{c.title}</option>
                ))}
              </select>
            </div>

            {/* Chapter Header Card */}
            <div className="p-6 rounded-3xl bg-gradient-to-br from-info/10 via-card to-secondary/30 border border-info/20 shadow-sm relative overflow-hidden">
              <div className="flex items-center gap-2 text-xs font-bold text-info uppercase tracking-wider mb-2">
                <HelpCircle className="size-3.5" />
                <span>{currentChapter.category}</span>
              </div>
              <h2 className="font-display text-xl sm:text-2xl font-black text-ink mb-2">
                {currentChapter.title}
              </h2>
              <p className="text-xs sm:text-sm text-subtext leading-relaxed">
                {currentChapter.summary}
              </p>
            </div>

            {/* Rendered Sections */}
            <div className="space-y-6">
              {currentChapter.sections.map((sec, idx) => (
                <div key={idx} className="p-6 rounded-3xl bg-card border border-hairline shadow-sm space-y-3 hover:border-ink/20 transition-all">
                  <h4 className="font-display font-bold text-base text-ink flex items-center gap-2 border-b border-hairline pb-2.5">
                    <span className="size-6 rounded-lg bg-secondary text-ink text-xs font-mono grid place-items-center shrink-0">
                      {idx + 1}
                    </span>
                    <span>{sec.heading}</span>
                  </h4>
                  {formatSectionContent(sec.content)}
                </div>
              ))}
            </div>

            {/* Bottom Footer / Next Chapter Navigation */}
            <div className="pt-6 border-t border-hairline flex items-center justify-between gap-4">
              {(() => {
                const idx = USER_GUIDE_CHAPTERS.findIndex((c) => c.id === selectedChapterId);
                const prev = idx > 0 ? USER_GUIDE_CHAPTERS[idx - 1] : null;
                const next = idx < USER_GUIDE_CHAPTERS.length - 1 ? USER_GUIDE_CHAPTERS[idx + 1] : null;
                return (
                  <>
                    {prev ? (
                      <button
                        onClick={() => setSelectedChapterId(prev.id)}
                        className="px-4 py-2.5 rounded-xl border border-hairline bg-card hover:bg-secondary text-xs font-bold text-ink flex items-center gap-2 transition-colors cursor-pointer shadow-sm"
                      >
                        <ArrowLeft className="size-3.5" />
                        <span className="truncate max-w-[140px] sm:max-w-[180px]">{prev.title}</span>
                      </button>
                    ) : <div />}

                    {next && (
                      <button
                        onClick={() => setSelectedChapterId(next.id)}
                        className="px-4 py-2.5 rounded-xl bg-ink text-background hover:opacity-90 text-xs font-bold flex items-center gap-2 transition-opacity cursor-pointer shadow-sm ml-auto"
                      >
                        <span className="truncate max-w-[140px] sm:max-w-[180px]">{next.title}</span>
                        <ChevronRight className="size-3.5" />
                      </button>
                    )}
                  </>
                );
              })()}
            </div>

          </div>
        </div>

        {/* Footer Bar */}
        <div className="h-12 px-6 bg-card border-t border-hairline flex items-center justify-between text-[11px] text-subtext shrink-0">
          <span>Need real-time answers? Try the <strong className="text-ink">Project AI Copilot</strong> in the sidebar.</span>
          <span className="flex items-center gap-1">Press <kbd className="px-1.5 py-0.5 rounded bg-secondary border border-hairline font-mono font-bold">ESC</kbd> to close</span>
        </div>

      </div>
    </div>
  );
}
