import React from "react";

function LowConfidenceMatchList({ insights }) {
  // Filter low confidence insights (assuming a confidence field between 0 and 1)
  const lowConfidence = (insights || []).filter((i) => (i.confidence ?? 1) < 0.5);
  if (lowConfidence.length === 0) {
    return null;
  }
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 mt-6">
      <h2 className="text-2xl font-bold mb-4 text-slate-200">Low‑Confidence Matches</h2>
      <ul className="space-y-2 text-slate-300">
        {lowConfidence.map((item, idx) => (
          <li key={idx} className="flex justify-between">
            <span>{item.description || "Match"}</span>
            <span className="text-red-400">{(item.confidence * 100).toFixed(0)}%</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default LowConfidenceMatchList;
