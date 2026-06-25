import React from "react";

export function PageHeader({ eyebrow, title, lede, primary, secondary }) {
  return (
    <div className="px-6 lg:px-10 pt-10 pb-8 border-b border-hairline">
      <div className="flex items-start justify-between flex-wrap gap-6">
        <div className="max-w-2xl">
          <span className="chip">{eyebrow}</span>
          <h1 className="mt-3 font-display text-5xl leading-[1.05]">{title}</h1>
          <p className="mt-3 text-subtext text-lg">{lede}</p>
        </div>
        <div className="flex items-center gap-2">
          {secondary && (
            <button 
                onClick={secondary.onClick}
                className="h-12 px-5 rounded-full border border-hairline bg-card hover:bg-secondary transition text-sm"
            >
                {secondary.label}
            </button>
          )}
          {primary && (
            <button 
                onClick={primary.onClick}
                className="h-12 px-6 rounded-full bg-ink text-background hover:opacity-90 transition text-sm font-medium"
            >
                {primary.label}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export function PageBody({ children }) {
  return <div className="px-6 lg:px-10 py-10 space-y-8">{children}</div>;
}
