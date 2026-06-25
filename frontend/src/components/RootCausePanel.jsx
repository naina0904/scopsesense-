import React from "react";

function RootCausePanel({ causality }) {
  const data = causality || [];
  if (data.length === 0) {
    return null;
  }
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 mt-6">
      <h2 className="text-2xl font-bold mb-4 text-slate-200">Root Cause Analysis</h2>
      <ul className="space-y-2 text-slate-300">
        {data.map((item, idx) => (
          <li key={idx} className="flex justify-between">
            <span>{item.cause || "Cause"}</span>
            <span>{item.severity || ""}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default RootCausePanel;
