import { useLocation, Link } from "react-router-dom";
import { Check } from "lucide-react";
import Sidebar from "../components/Sidebar";
import Header from "../components/Header";

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
  const currentIdx = STEPS.findIndex(s => pathname === s.to || pathname.startsWith(s.to));
  const active = currentIdx >= 0;
  if (!active) return null;
  return (
    <div className="border-b border-hairline bg-beige/30">
      <div className="px-6 lg:px-10 py-3 flex items-center gap-2 overflow-x-auto">
        {STEPS.map((s, i) => {
          const done = i < currentIdx;
          const cur = i === currentIdx;
          return (
            <div key={s.to} className="flex items-center gap-2 shrink-0">
              <div className={`size-6 rounded-full grid place-items-center text-[10px] font-medium border ${
                done ? "bg-success/40 border-success text-ink" :
                cur ? "bg-ink text-background border-ink" :
                "bg-card border-hairline text-subtext"
              }`}>
                {done ? <Check className="size-3" /> : i + 1}
              </div>
              <span className={`text-xs ${cur ? "text-ink font-medium" : "text-subtext"}`}>{s.label}</span>
              {i < STEPS.length - 1 && <div className={`w-8 h-px ${done ? "bg-success" : "bg-hairline"}`} />}
            </div>
          );
        })}
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