import React from "react";

export function PageHeader({ eyebrow, title, lede, primary, secondary, actions }) {
  return (
    <div className="px-6 lg:px-10 pt-10 pb-8 border-b border-hairline">
      <div className="flex items-start justify-between flex-wrap gap-6">
        <div className="max-w-2xl">
          {eyebrow && <span className="chip">{eyebrow}</span>}
          <h1 className="mt-3 font-display text-5xl leading-[1.05]">{title}</h1>
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
                  className="h-10 px-5 rounded-full bg-ink text-background hover:opacity-90 transition text-xs font-semibold flex items-center justify-center gap-2 shadow-sm w-full sm:w-auto"
              >
                  {primary.label}
              </button>
            )}
            {secondary && (
              <button 
                  onClick={secondary.onClick}
                  className="h-10 px-5 rounded-full border border-hairline bg-card hover:bg-secondary transition text-xs font-semibold flex items-center justify-center gap-2 shadow-2xs w-full sm:w-auto"
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
