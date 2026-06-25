import React from "react";

function OwnershipTimeline({ featureOwnership }) {
  const data = featureOwnership || [];
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 mt-6">
      <h2 className="text-2xl font-bold mb-4 text-slate-200">Feature Ownership Timeline</h2>
      <ul className="space-y-2 text-slate-300">
        {data.map((item, idx) => (
          <li key={idx} className="flex justify-between">
            <span>{item.feature_name || "Feature"}</span>
            <span>{item.owner || "Owner"}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default OwnershipTimeline;
