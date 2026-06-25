import React from "react";

function AuditProgressBar({ progress, statusMessage }) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-6">
      <div className="text-3xl font-bold text-slate-800">Running Background Audit...</div>
      <div className="w-full max-w-lg bg-slate-200 rounded-full h-4">
        <div
          className="bg-indigo-600 h-4 rounded-full transition-all duration-500"
          style={{ width: `${progress}%` }}
        ></div>
      </div>
      <div className="text-slate-500">{statusMessage}</div>
    </div>
  );
}

export default AuditProgressBar;
