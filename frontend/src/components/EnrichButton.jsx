
import React, { useState } from "react";
import { triggerEnrichment } from "../services/api";

export default function EnrichButton({ taskId, taskStatus, enrichmentStatus, onStarted }) {
  const [requesting, setRequesting] = useState(false);
  const [localError,  setLocalError]  = useState("");

  const canEnrich = (
    ["completed", "running"].includes(taskStatus) &&
    enrichmentStatus !== "running" &&
    enrichmentStatus !== "completed"
  );

  async function handleEnrich() {
    if (!canEnrich) return;
    setRequesting(true);
    setLocalError("");
    try {
      await triggerEnrichment(taskId);
      if (onStarted) onStarted();   // tell parent to resume polling
    } catch (err) {
      const msg = err?.response?.data?.detail || "Failed to start enrichment.";
      setLocalError(msg);
    } finally {
      setRequesting(false);
    }
  }

  if (enrichmentStatus === "running") {
    return (
      <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-yellow-900/20
                      border border-yellow-700/30 text-yellow-400 text-xs font-medium">
        <span className="w-3.5 h-3.5 border-2 border-yellow-800 border-t-yellow-400
                         rounded-full animate-spin shrink-0" />
        Enriching…
      </div>
    );
  }

  if (enrichmentStatus === "completed") {
    return (
      <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-brand-900/20
                      border border-brand-700/30 text-brand-400 text-xs font-medium">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.2}
          className="w-3.5 h-3.5 shrink-0">
          <path d="M20 6 9 17l-5-5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        Enriched
      </div>
    );
  }

  return (
    <div className="flex flex-col items-end gap-1">
      <button
        onClick={handleEnrich}
        disabled={!canEnrich || requesting}
        title={!canEnrich ? "Complete the scrape task first." : "Visit websites to find missing emails and social links"}
        className="flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium
                   bg-surface-700 hover:bg-surface-600 border border-surface-500
                   text-gray-300 transition-all duration-150
                   disabled:opacity-40 disabled:cursor-not-allowed active:scale-95"
      >
        {requesting ? (
          <>
            <span className="w-3.5 h-3.5 border-2 border-gray-700 border-t-gray-300
                             rounded-full animate-spin" />
            Starting…
          </>
        ) : (
          <>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8}
              className="w-3.5 h-3.5">
              <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" strokeLinecap="round" />
              <circle cx="12" cy="10" r="3" />
            </svg>
            {enrichmentStatus === "failed" ? "Retry Enrich" : "Enrich Leads"}
          </>
        )}
      </button>
      {localError && (
        <p className="text-[10px] text-red-400 font-mono max-w-[200px] text-right">
          {localError}
        </p>
      )}
    </div>
  );
}