import React from "react";
import { BookOpen, HelpCircle, ArrowRight, Sparkles, Download } from "lucide-react";
import { useAudit } from "../../context/AuditContext";
import { generateUserGuidePDF } from "../../utils/generateUserGuidePDF";

export function StageGuideCard({
  sectionId,
  title = "View Complete Stage Guide & How This Works",
  description = "Explore the full interactive walkthrough, analytical logic, and troubleshooting actions for this stage.",
  className = ""
}) {
  const { openHelp } = useAudit();

  return (
    <div 
      onClick={() => openHelp(sectionId)}
      className={`mt-8 p-6 lg:p-7 rounded-3xl bg-gradient-to-r from-info/20 via-primary/15 to-info/20 border-2 border-info/50 hover:border-info text-left shadow-lg hover:shadow-2xl transition-all duration-300 cursor-pointer group flex flex-col sm:flex-row items-start sm:items-center justify-between gap-5 max-w-4xl mx-auto ${className}`}
    >
      <div className="flex items-start sm:items-center gap-5">
        <div className="size-14 rounded-2xl bg-info/20 border border-info/40 flex items-center justify-center shrink-0 text-info group-hover:scale-110 group-hover:bg-info group-hover:text-background transition-all duration-300 shadow-sm">
          <BookOpen className="size-7" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wider bg-info/20 text-info border border-info/30">
              <Sparkles className="size-3" /> Management & User Guide
            </span>
          </div>
          <h4 className="font-display font-bold text-lg lg:text-xl text-ink group-hover:text-info transition-colors mt-2 flex items-center gap-2">
            <span>{title}</span>
          </h4>
          <p className="text-sm lg:text-base text-subtext mt-1.5 leading-relaxed max-w-2xl">
            {description}
          </p>
        </div>
      </div>
      <div className="flex items-center gap-3 self-end sm:self-center shrink-0">
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            generateUserGuidePDF();
          }}
          className="px-4 py-3 rounded-full bg-card/80 hover:bg-card text-info border border-info/40 font-semibold text-sm flex items-center gap-2 shadow-sm hover:scale-105 transition-all"
          title="Download Official PDF Manual (Professional Publication Format)"
        >
          <Download className="size-4 shrink-0" />
          <span className="hidden md:inline">PDF Manual</span>
        </button>
        <div className="px-5 py-3 rounded-full bg-info text-background font-semibold text-sm flex items-center gap-2 shadow-md group-hover:scale-105 group-hover:bg-info/90 transition-all">
          <span>Read Guide</span>
          <ArrowRight className="size-4 group-hover:translate-x-1 transition-transform" />
        </div>
      </div>
    </div>
  );
}

export default StageGuideCard;
