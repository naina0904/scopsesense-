import { useMemo, useState } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  CartesianGrid
} from "recharts";
import { Sparkles, AlertTriangle, CheckCircle2, Clock, Zap, Activity, Layers, Filter, ShieldAlert, CheckCircle, ChevronDown } from "lucide-react";

// Minimalist, precision floating glassmorphic pill tooltip that appears on hover and disappears on exit!
function PrecisionWaveTooltip({ active, payload }) {
  if (!active || !payload || !payload.length || !payload[0].payload) {
    return null;
  }

  const item = payload[0].payload;

  return (
    <div className="bg-card/95 backdrop-blur-xl border border-hairline rounded-2xl p-3.5 shadow-xl max-w-xs animate-in fade-in zoom-in-95 duration-150 ring-1 ring-ink/5 pointer-events-none z-50">
      <div className="flex items-center justify-between gap-3 mb-1.5 border-b border-hairline/60 pb-1.5">
        <span className="font-bold text-xs text-ink truncate max-w-[160px]" title={item.fullReq}>
          {item.fullReq}
        </span>
        <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase tracking-wider shrink-0 shadow-sm flex items-center gap-1 ${
          item.stage === "Delayed" 
            ? "bg-rose/15 text-risk border border-rose/30" 
            : item.stage === "Advanced" 
            ? "bg-amber-500/15 text-amber-600 dark:text-amber-300 border border-amber-500/30" 
            : "bg-emerald/15 text-emerald border border-emerald/30"
        }`}>
          {item.stage === "Delayed" ? "🔴 DELAYED" : item.stage === "Advanced" ? "🟡 ADVANCED" : "🟢 ON TRACK"}
        </span>
      </div>
      
      <div className="text-[11px] font-semibold text-ink mb-1.5 flex justify-between bg-secondary/50 px-2 py-1 rounded-lg border border-hairline">
        <span>Planned: <strong className="text-info">{item.planned}h</strong></span>
        <span>Worked: <strong className={item.stage === "Delayed" ? "text-risk" : "text-emerald"}>{item.actual}h</strong></span>
        <span>Remaining: <strong className="text-subtext">{item.remaining}h</strong></span>
      </div>

      <div className="text-[11px] text-subtext leading-relaxed bg-secondary/30 p-2 rounded-xl border border-hairline font-medium">
        💡 <strong className="text-ink">Reason:</strong> {item.shortReason}
      </div>
    </div>
  );
}

function TemporalDriftChart({ varianceRows = [] }) {
  const [filterMode, setFilterMode] = useState("all"); // "all" | "delayed" | "ontrack"
  const [isModalOpen, setIsModalOpen] = useState(false); // Cinematic Pop-up Modal state

  // Clean, calculate, and categorize data into 3 stages: Delayed/Underdeveloped, On Track, and Advanced
  const allChartData = useMemo(() => {
    if (!Array.isArray(varianceRows) || !varianceRows.length) return [];
    
    return varianceRows
      .filter(r => (Number(r.planned_hours) > 0 || Number(r.actual_hours) > 0))
      .map((item, idx) => {
        const planned = Number(item.planned_hours || 0);
        const actual = Number(item.actual_hours || 0);
        const variance = Number(item.variance_hours ?? (actual - planned));
        
        // Exact remaining hours to work on (if status is done/completed, remaining is 0)
        const isDone = String(item.status || "").toLowerCase() in { done: 1, completed: 1, closed: 1, resolved: 1 };
        const remaining = isDone ? 0 : Math.max(0, planned - actual);

        const req = (item.requirement || `Feature ${idx + 1}`).trim();
        const shortName = req.length > 15 ? req.slice(0, 14) + "…" : req;

        // Categorize into 3 distinct Executive Stages (Status-Aware / Lifecycle-Aware)
        let stage = "On Track";
        let shortReason = "Progressing smoothly within allocated budget.";

        if (planned > 0 && actual === 0) {
          stage = "Delayed";
          shortReason = `Underdeveloped / Unstarted: 0 hours logged out of ${planned}h planned budget.`;
        } else if (variance > 0) {
          stage = "Delayed";
          shortReason = `Effort Overrun (+${variance.toFixed(1)}h slip): Actual work exceeded planned budget.`;
        } else if (isDone && remaining === 0 && actual > 0 && variance < 0) {
          stage = "Advanced";
          shortReason = `Completed Under Budget: Successfully delivered ${Math.abs(variance).toFixed(1)}h below estimated baseline.`;
        } else if (isDone && variance === 0) {
          stage = "On Track";
          shortReason = `Completed On Schedule: Successfully delivered exactly on estimated baseline (${actual}h logged).`;
        } else {
          stage = "On Track";
          const progressPct = planned > 0 ? Math.round((actual / planned) * 100) : 0;
          shortReason = `Work Underway / On Track: ${actual}h logged (${progressPct}% of budget); ${remaining.toFixed(1)}h remaining to completion.`;
        }

        return {
          id: item.srs_node_id || idx,
          name: shortName,
          fullReq: req,
          planned,
          actual,
          remaining,
          variance,
          stage,
          shortReason,
          developer: item.developer || "Unassigned",
          module: item.module || "General"
        };
      });
  }, [varianceRows]);

  // Apply filter mode
  const chartData = useMemo(() => {
    if (filterMode === "delayed") {
      return allChartData.filter(d => d.stage === "Delayed");
    }
    if (filterMode === "ontrack") {
      return allChartData.filter(d => d.stage !== "Delayed");
    }
    return allChartData;
  }, [allChartData, filterMode]);

  // Real-Time Mathematical Calculations across entire project
  const { totalPlanned, totalWorked, totalRemaining, totalVariance, projectFlag } = useMemo(() => {
    let plannedSum = 0;
    let workedSum = 0;
    let remainingSum = 0;
    let delayedCount = 0;

    allChartData.forEach(d => {
      plannedSum += d.planned;
      workedSum += d.actual;
      remainingSum += d.remaining;
      if (d.stage === "Delayed") delayedCount++;
    });

    const varSum = workedSum - plannedSum;

    // Real-Time Project Flagging Logic
    let flag = {
      label: "🟢 PROJECT ON TRACK",
      desc: "Delivering within planned budget milestones",
      style: "bg-emerald/15 text-emerald border-emerald/30 shadow-emerald/10"
    };

    if (varSum > 0 || (allChartData.length > 0 && delayedCount / allChartData.length >= 0.25)) {
      flag = {
        label: `🔴 PROJECT DELAYED (+${varSum > 0 ? varSum.toFixed(1) : 0}h slip)`,
        desc: `${delayedCount} requirements experiencing schedule drift`,
        style: "bg-rose/15 text-risk border-rose/30 shadow-rose/10 animate-pulse"
      };
    } else if (varSum < 0 && delayedCount === 0 && remainingSum === 0) {
      flag = {
        label: `🟡 PROJECT ADVANCED (${Math.abs(varSum).toFixed(1)}h under budget)`,
        desc: "All engineering milestones completed ahead of planned schedule",
        style: "bg-amber-500/15 text-amber-600 dark:text-amber-300 border-amber-500/30 shadow-amber-500/10"
      };
    }

    return {
      totalPlanned: plannedSum,
      totalWorked: workedSum,
      totalRemaining: remainingSum,
      totalVariance: varSum,
      projectFlag: flag
    };
  }, [allChartData]);

  if (!allChartData.length) {
    return null;
  }

  return (
    <div className="bg-card border border-hairline rounded-3xl p-6 md:p-8 shadow-sm relative overflow-hidden transition-all duration-300">
      {/* Subtle ambient light gradient matching our native UI/UX design tokens */}
      <div className="absolute -top-32 -right-32 size-96 bg-info/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute -bottom-32 -left-32 size-96 bg-emerald/10 rounded-full blur-3xl pointer-events-none" />

      {/* Header & Real-Time Project Flag (Clickable to Launch Modal) */}
      <div 
        onClick={() => setIsModalOpen(true)}
        className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 relative z-10 cursor-pointer select-none group"
      >
        <div>
          <div className="flex flex-wrap items-center gap-3">
            <h3 className="font-display text-2xl md:text-3xl text-ink tracking-tight flex items-center gap-2.5 group-hover:text-info transition-colors">
              <Activity className="size-7 text-info shrink-0 animate-pulse" />
              Executive Waveform Timeline
            </h3>
            <span className={`chip border text-xs font-extrabold px-3.5 py-1 rounded-full flex items-center gap-1.5 shadow-sm ${projectFlag.style}`}>
              <Zap className="size-3.5 fill-current" />
              {projectFlag.label}
            </span>
            <span className="text-xs font-extrabold text-info bg-info/10 border border-info/30 px-3.5 py-1.5 rounded-full flex items-center gap-1.5 shadow-sm group-hover:bg-info group-hover:text-white transition-all">
              <Sparkles className="size-3.5" />
              Click to Launch Cinematic Waveform Modal
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="px-5 py-2.5 rounded-2xl bg-info/10 border border-info/30 font-bold text-xs text-info flex items-center gap-2 group-hover:bg-info group-hover:text-white transition-all shadow-sm">
            <span>View Timeline</span>
          </div>
        </div>
      </div>

      {/* Glassmorphic Cinematic Pop-up Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 md:p-10 bg-ink/80 backdrop-blur-md animate-in fade-in duration-300">
          <div 
            onClick={(e) => e.stopPropagation()}
            className="bg-background border border-hairline/80 rounded-3xl shadow-2xl w-full max-w-6xl max-h-[90vh] flex flex-col overflow-hidden animate-in zoom-in-95 duration-300"
          >
            {/* Modal Header */}
            <div className="px-8 py-6 border-b border-hairline flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-card">
              <div className="flex items-center gap-3">
                <Activity className="size-7 text-info shrink-0 animate-pulse" />
                <div>
                  <h3 className="font-display text-2xl text-ink font-bold">Executive Waveform Timeline</h3>
                </div>
              </div>

              <div className="flex items-center gap-4">
                {/* View Mode Filters */}
                <div className="flex flex-wrap items-center gap-2 bg-secondary/50 p-1.5 rounded-2xl border border-hairline shrink-0 shadow-sm">
                  <button
                    onClick={() => setFilterMode("all")}
                    className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition flex items-center gap-1.5 ${
                      filterMode === "all" 
                        ? "bg-ink text-background shadow-md" 
                        : "text-subtext hover:text-ink hover:bg-card"
                    }`}
                  >
                    <Layers className="size-3.5" />
                    All Stages ({allChartData.length})
                  </button>
                  <button
                    onClick={() => setFilterMode("delayed")}
                    className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition flex items-center gap-1.5 ${
                      filterMode === "delayed" 
                        ? "bg-rose/90 text-white shadow-md shadow-rose/20" 
                        : "text-subtext hover:text-ink hover:bg-card"
                    }`}
                  >
                    <ShieldAlert className="size-3.5" />
                    Delayed Only ({allChartData.filter(d => d.stage === "Delayed").length})
                  </button>
                  <button
                    onClick={() => setFilterMode("ontrack")}
                    className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition flex items-center gap-1.5 ${
                      filterMode === "ontrack" 
                        ? "bg-emerald-600 text-white shadow-md shadow-emerald-600/20" 
                        : "text-subtext hover:text-ink hover:bg-card"
                    }`}
                  >
                    <CheckCircle className="size-3.5" />
                    On Track / Advanced ({allChartData.filter(d => d.stage !== "Delayed").length})
                  </button>
                </div>

                <button
                  onClick={() => setIsModalOpen(false)}
                  className="size-10 rounded-full bg-secondary hover:bg-rose/20 hover:text-risk flex items-center justify-center text-subtext font-bold transition-all"
                  title="Close Modal"
                >
                  ✕
                </button>
              </div>
            </div>

            {/* Modal Body (Chart & Legend) */}
            <div className="p-8 overflow-y-auto flex-1 bg-background">
              <div className="h-[420px] w-full relative z-10">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart
                    data={chartData}
                    margin={{ top: 20, right: 30, left: 15, bottom: 65 }}
                  >
                    <defs>
                      <linearGradient id="colorPlanned" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.02} />
                      </linearGradient>
                      <linearGradient id="colorWorked" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
                        <stop offset="95%" stopColor="#10b981" stopOpacity={0.02} />
                      </linearGradient>
                    </defs>

                    <CartesianGrid strokeDasharray="3 3" stroke="#cbd5e1" opacity={0.4} vertical={false} />

                    <XAxis
                      dataKey="name"
                      stroke="#64748b"
                      fontSize={11}
                      tickLine={false}
                      axisLine={{ stroke: '#cbd5e1' }}
                      angle={-28}
                      textAnchor="end"
                      interval="preserveStartEnd"
                    />
                    <YAxis
                      stroke="#64748b"
                      fontSize={11}
                      tickLine={false}
                      axisLine={false}
                      unit="h"
                    />

                    <Tooltip
                      cursor={{ stroke: '#8b5cf6', strokeWidth: 1.5, strokeDasharray: '4 4' }}
                      content={<PrecisionWaveTooltip />}
                    />

                    <ReferenceLine y={0} stroke="#cbd5e1" />

                    <Area
                      type="monotone"
                      dataKey="planned"
                      name="Exact Hours Planned (SRS)"
                      stroke="#3b82f6"
                      strokeWidth={2.5}
                      fillOpacity={1}
                      fill="url(#colorPlanned)"
                    />

                    <Area
                      type="monotone"
                      dataKey="actual"
                      name="Hours Worked On (Jira)"
                      stroke="#10b981"
                      strokeWidth={3}
                      fillOpacity={1}
                      fill="url(#colorWorked)"
                      activeDot={{ r: 7, fill: '#10b981', stroke: '#ffffff', strokeWidth: 2 }}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>

              {/* Minimalist 3-Stage Waveform Legend */}
              <div className="mt-6 pt-4 border-t border-hairline/60 flex flex-wrap items-center justify-center gap-8 text-xs font-bold text-ink">
                <div className="flex items-center gap-2">
                  <span className="size-3.5 rounded-md bg-[#3b82f6] shadow-sm" />
                  <span>Exact Hours Planned <span className="font-normal text-subtext">(SRS Baseline Wave)</span></span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="size-3.5 rounded-md bg-[#10b981] shadow-sm" />
                  <span>Hours Worked On <span className="font-normal text-subtext">(Jira Actual Wave)</span></span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default TemporalDriftChart;
