
import React from "react";
import { formatProgress, formatEnrichStatus } from "../utils/formatters";

const SCRAPE_LABEL = {
  pending:   "Queued",
  running:   "Scraping…",
  completed: "Completed",
  failed:    "Failed",
  cancelled: "Cancelled",
};

const SCRAPE_BAR_COLOR = {
  pending:   "bg-gray-500",
  running:   "bg-brand-500",
  completed: "bg-brand-500",
  failed:    "bg-red-500",
  cancelled: "bg-gray-500",
};

export default function ProgressBar({ task }) {
  if (!task) return null;

  const pct    = formatProgress(task.progress, task.total);
  const isLive = task.status === "running";
  const isFail = task.status === "failed";

  const enrichStatus  = task.enrichment_status || "none";
  const showEnrichRow = enrichStatus !== "none";
  const enrichInfo    = formatEnrichStatus(enrichStatus);

  return (
    <div className="space-y-4">

      <div className="space-y-2">
        <div className="flex items-center justify-between text-xs">
          <div className="flex items-center gap-2">
            {isLive && (
              <span className="w-2 h-2 rounded-full bg-brand-400 animate-pulse-slow" />
            )}
            <span className={`font-medium ${isFail ? "text-red-400" : "text-gray-300"}`}>
              {SCRAPE_LABEL[task.status] || task.status}
            </span>
            {task.keyword && (
              <span className="text-gray-500">
                — {task.keyword}{task.location ? `, ${task.location}` : ""}
              </span>
            )}
            {task.dork_query && !task.keyword && (
              <span className="text-gray-500 font-mono truncate max-w-[160px]">
                — {task.dork_query}
              </span>
            )}
          </div>
          <span className="font-mono text-gray-400">
            {task.progress} / {task.total || "?"} leads
          </span>
        </div>

        <div className="h-1.5 bg-surface-600 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500
              ${SCRAPE_BAR_COLOR[task.status] || "bg-gray-500"}
              ${isLive ? "animate-pulse-slow" : ""}`}
            style={{ width: `${isLive && pct === 0 ? 5 : pct}%` }}
          />
        </div>

        {isFail && task.error && (
          <p className="text-xs text-red-400 font-mono bg-red-900/20 px-3 py-2 rounded-lg border border-red-800/40">
            {task.error}
          </p>
        )}
      </div>

      {showEnrichRow && (
        <div className="flex items-center gap-2 pt-1 border-t border-surface-600">
          {enrichStatus === "running" && (
            <span className="w-3 h-3 border-2 border-surface-600 border-t-yellow-400 rounded-full animate-spin" />
          )}
          {enrichStatus === "completed" && (
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}
              className="w-3.5 h-3.5 text-brand-400 shrink-0">
              <path d="M20 6 9 17l-5-5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          )}
          {enrichStatus === "failed" && (
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}
              className="w-3.5 h-3.5 text-red-400 shrink-0">
              <path d="M18 6 6 18M6 6l12 12" strokeLinecap="round" />
            </svg>
          )}
          <span className={`text-xs font-medium ${enrichInfo.colorClass}`}>
            Enrichment: {enrichInfo.label}
          </span>
        </div>
      )}
    </div>
  );
}