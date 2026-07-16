import React from "react";
import { useLocation } from "react-router-dom";
import { Info } from "lucide-react";
import { useAudit } from "../../context/AuditContext";
import { STAGE_HELP_MAP } from "../../data/userGuideData";

export function PageHeader({ eyebrow, title, lede, primary, secondary, actions, helpSection }) {
  const location = useLocation();
  const { openHelp } = useAudit();
  const targetHelp = helpSection || STAGE_HELP_MAP[location.pathname] || "quick-start";

  return (
    <div className="px-6 lg:px-10 pt-10 pb-8 border-b border-hairline">
      <div className="flex items-start justify-between flex-wrap gap-6">
        <div className="max-w-2xl">
          {eyebrow && <span className="chip">{eyebrow}</span>}
          <div className="flex items-center gap-3 mt-3">
            <h1 className="font-display text-4xl sm:text-5xl leading-[1.05]">{title}</h1>
            <button
              type="button"
              onClick={() => openHelp(targetHelp)}
              className="size-8 rounded-full bg-info/10 hover:bg-info/20 text-info border border-info/30 grid place-items-center transition-all cursor-pointer shrink-0 shadow-2xs group"
              title="Click for stage user guide & instructions"
              aria-label="Open stage user guide"
            >
              <Info className="size-4 group-hover:scale-110 transition-transform" />
            </button>
          </div>
          {lede && <p className="mt-3 text-subtext text-lg">{lede}</p>}
        </div>
        <div className="flex flex-col items-end gap-2.5 shrink-0">
          <div className="flex items-center gap-2 flex-wrap justify-end">
            {actions}
          </div>
          <div className="flex flex-col items-end gap-2 w-full sm:w-auto">
            {primary && (
              <button 
                  onClick={primary.onClick}
                  className="h-10 px-5 rounded-full bg-ink text-background hover:opacity-90 transition text-xs font-semibold flex items-center justify-center gap-2 shadow-sm w-full sm:w-auto cursor-pointer"
              >
                  {primary.label}
              </button>
            )}
            {secondary && (
              <button 
                  onClick={secondary.onClick}
                  className="h-10 px-5 rounded-full border border-hairline bg-card hover:bg-secondary transition text-xs font-semibold flex items-center justify-center gap-2 shadow-2xs w-full sm:w-auto cursor-pointer"
              >
                  {secondary.label}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export function PageBody({ children }) {
  return <div className="px-6 lg:px-10 py-10 space-y-8">{children}</div>;
}
