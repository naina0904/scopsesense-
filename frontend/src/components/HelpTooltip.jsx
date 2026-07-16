import { useState, useRef, useEffect } from "react";
import { Info, ExternalLink, Sparkles } from "lucide-react";
import { GLOSSARY_TERMS } from "../data/userGuideData";
import { useAudit } from "../context/AuditContext";

export default function HelpTooltip({ termKey, children, className = "" }) {
  const { openHelp } = useAudit();
  const [isOpen, setIsOpen] = useState(false);
  const tooltipRef = useRef(null);

  const termObj = GLOSSARY_TERMS[termKey] || {
    term: termKey,
    definition: "Executive audit metric calculated by ScopeSense intelligence engine.",
    action: null,
    chapterId: "glossary"
  };

  // Close on click outside
  useEffect(() => {
    if (!isOpen) return;
    const handleClickOutside = (e) => {
      if (tooltipRef.current && !tooltipRef.current.contains(e.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [isOpen]);

  return (
    <div ref={tooltipRef} className={`inline-flex items-center gap-1.5 relative ${className}`}>
      {children && <span>{children}</span>}
      <button
        type="button"
        onClick={(e) => {
          e.stopPropagation();
          setIsOpen(!isOpen);
        }}
        onMouseEnter={() => setIsOpen(true)}
        onMouseLeave={() => setIsOpen(false)}
        className="size-4.5 rounded-full bg-secondary/80 hover:bg-info/15 text-subtext hover:text-info border border-hairline inline-flex items-center justify-center transition-colors cursor-pointer shrink-0 shadow-2xs"
        title={`What is ${termObj.term}?`}
        aria-label={`Help definition for ${termObj.term}`}
      >
        <Info className="size-3" />
      </button>

      {/* Floating Popover Card */}
      {isOpen && (
        <div 
          onClick={(e) => e.stopPropagation()}
          className="absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-2 w-72 sm:w-80 p-4 rounded-2xl bg-card border border-hairline shadow-2xl animate-in fade-in zoom-in-95 duration-150 text-left"
        >
          {/* Arrow indicator */}
          <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-1 border-4 border-transparent border-t-card" />

          <div className="flex items-center gap-1.5 text-[11px] font-bold text-info uppercase tracking-wider mb-1">
            <Sparkles className="size-3" />
            <span>ScopeSense Glossary</span>
          </div>

          <h5 className="font-display font-bold text-xs text-ink mb-1.5">
            {termObj.term}
          </h5>

          <p className="text-xs text-subtext leading-relaxed font-sans mb-2.5">
            {termObj.definition}
          </p>

          {termObj.action && (
            <div className="p-2 rounded-xl bg-secondary/50 border border-hairline text-[11px] text-ink font-medium mb-3">
              <strong className="text-info font-bold">Action:</strong> {termObj.action}
            </div>
          )}

          <button
            type="button"
            onClick={() => {
              setIsOpen(false);
              openHelp(termObj.chapterId || "glossary");
            }}
            className="w-full h-8 px-3 rounded-xl bg-info/10 hover:bg-info/20 text-info font-bold text-xs flex items-center justify-center gap-1.5 transition-colors cursor-pointer"
          >
            <span>Learn more in User Guide</span>
            <ExternalLink className="size-3.5" />
          </button>
        </div>
      )}
    </div>
  );
}
