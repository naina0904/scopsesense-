import { useLocation, Link, useNavigate } from "react-router-dom";
import { ArrowLeft, ArrowRight, Check } from "lucide-react";
import Sidebar from "../components/Sidebar";
import Header from "../components/Header";
import { useAudit } from "../context/AuditContext";

const STEPS = [
  { to: "/upload-srs", label: "Upload SRS" },
  { to: "/requirements", label: "Planned" },
  { to: "/configuration", label: "Connect" },
  { to: "/normalization", label: "Normalize" },
  { to: "/matches", label: "Match" },
  { to: "/execute", label: "Audit" },
  { to: "/results", label: "Results" },
];

function WorkflowProgress({ pathname }) {
  const navigate = useNavigate();
  const { stepActionRef } = useAudit();
  const currentIdx = STEPS.findIndex(s => pathname === s.to || pathname.startsWith(s.to));
  const active = currentIdx >= 0;
  if (!active) return null;

  const prevStep = currentIdx > 0 ? STEPS[currentIdx - 1] : null;
  const nextStep = currentIdx < STEPS.length - 1 ? STEPS[currentIdx + 1] : null;

  const handleBack = async (e) => {
    e.preventDefault();
    if (stepActionRef?.current?.onPrev) {
      await stepActionRef.current.onPrev();
    } else if (prevStep) {
      navigate(prevStep.to);
    }
  };

  const handleNext = async (e) => {
    e.preventDefault();
    if (stepActionRef?.current?.onNext) {
      await stepActionRef.current.onNext();
    } else if (nextStep) {
      navigate(nextStep.to);
    }
  };

  return (
    <div className="border-b border-hairline bg-background/95 backdrop-blur sticky top-16 z-20">
      <div className="px-6 lg:px-10 py-2.5 flex items-center justify-between gap-4">
        <div className="flex items-center gap-2 overflow-x-auto py-1">
          {STEPS.map((s, i) => {
            const done = i < currentIdx;
            const cur = i === currentIdx;
            return (
              <Link key={s.to} to={s.to} className="flex items-center gap-2 shrink-0 group">
                <div className={`size-6 rounded-full grid place-items-center text-[10px] font-bold border transition ${
                  done ? "bg-success/20 border-success text-success group-hover:bg-success/30" :
                  cur ? "bg-ink text-background border-ink shadow-sm" :
                  "bg-card border-hairline text-subtext group-hover:border-ink/40"
                }`}>
                  {done ? <Check className="size-3.5 stroke-[2.5]" /> : i + 1}
                </div>
                <span className={`text-xs transition ${cur ? "text-ink font-bold" : "text-subtext group-hover:text-ink"}`}>{s.label}</span>
                {i < STEPS.length - 1 && <div className={`w-6 h-0.5 rounded-full transition ${done ? "bg-success" : "bg-hairline"}`} />}
              </Link>
            );
          })}
        </div>
        
        <div className="flex items-center gap-2 shrink-0 border-l border-hairline pl-4">
          {prevStep ? (
            <button 
              onClick={handleBack}
              className="h-8 px-3 rounded-lg border border-hairline bg-card hover:bg-secondary transition text-xs font-semibold text-ink flex items-center gap-1 shadow-sm cursor-pointer"
              title={`Go back to ${prevStep.label}`}
            >
              <ArrowLeft className="size-3.5" />
              <span>Back</span>
            </button>
          ) : (
            <button disabled className="h-8 px-3 rounded-lg border border-hairline bg-card/40 opacity-40 text-xs font-semibold text-subtext flex items-center gap-1 cursor-not-allowed">
              <ArrowLeft className="size-3.5" />
              <span>Back</span>
            </button>
          )}
          
          {nextStep ? (
            <button 
              onClick={handleNext}
              className="h-8 px-3.5 rounded-lg bg-ink text-background hover:opacity-90 transition text-xs font-bold flex items-center gap-1 shadow-sm cursor-pointer"
              title={`Move next to ${nextStep.label}`}
            >
              <span>Next</span>
              <ArrowRight className="size-3.5" />
            </button>
          ) : (
            <button disabled className="h-8 px-3.5 rounded-lg bg-ink/40 opacity-40 text-background text-xs font-bold flex items-center gap-1 cursor-not-allowed">
              <span>Next</span>
              <ArrowRight className="size-3.5" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

function MainLayout({ children }) {
    const location = useLocation();
    
    return (
        <div className="min-h-screen bg-background flex font-sans text-foreground">
            <Sidebar />
            <div className="flex-1 min-w-0 flex flex-col">
                <Header />
                <WorkflowProgress pathname={location.pathname} />
                <main className="flex-1 overflow-auto">
                    {children}
                </main>
            </div>
        </div>
    );
}

export default MainLayout;