import React, { useState } from "react";
import { getExportUrl } from "../services/api";

export default function ExportButton({ taskId, taskStatus, total }) {
  const [downloading, setDownloading] = useState(false);

  const canExport = ["completed", "running"].includes(taskStatus) && total > 0;

  async function handleExport() {
    if (!canExport) return;
    setDownloading(true);
    try {
      const url = getExportUrl(taskId);
      const a   = document.createElement("a");
      a.href    = url;
      a.target  = "_blank";
      a.rel     = "noopener noreferrer";
      a.click();
    } finally {
      setTimeout(() => setDownloading(false), 1500);
    }
  }

  return (
    <button
      onClick={handleExport}
      disabled={!canExport || downloading}
      className="btn-secondary flex items-center gap-2 text-sm"
      title={!canExport ? "Task must be running or completed with at least one lead." : "Download CSV"}
    >
      {downloading ? (
        <>
          <span className="w-4 h-4 border-2 border-gray-600 border-t-gray-300 rounded-full animate-spin" />
          Preparing…
        </>
      ) : (
        <>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} className="w-4 h-4">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" strokeLinecap="round" />
            <polyline points="7 10 12 15 17 10" strokeLinecap="round" strokeLinejoin="round" />
            <line x1="12" y1="15" x2="12" y2="3" strokeLinecap="round" />
          </svg>
          Export CSV
          {total > 0 && (
            <span className="text-xs font-mono text-gray-500">({total})</span>
          )}
        </>
      )}
    </button>
  );
}
