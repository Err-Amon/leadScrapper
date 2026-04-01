import React from "react";
import { formatProgress } from "../utils/formatters";

const STATUS_LABEL = {
  pending:   "Queued",
  running:   "Scraping…",
  completed: "Completed",
  failed:    "Failed",
};

const STATUS_COLOR = {
  pending:   "bg-gray-500",
  running:   "bg-brand-500",
  completed: "bg-brand-500",
  failed:    "bg-red-500",
};

export default function ProgressBar({ task }) {
  if (!task) return null;

  const pct     = formatProgress(task.progress, task.total);
  const isLive  = task.status === "running";
  const isFail  = task.status === "failed";

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-xs">
        <div className="flex items-center gap-2">
          {isLive && (
            <span className="w-2 h-2 rounded-full bg-brand-400 animate-pulse-slow" />
          )}
          <span className={`font-medium ${isFail ? "text-red-400" : "text-gray-300"}`}>
            {STATUS_LABEL[task.status] || task.status}
          </span>
          {task.keyword && (
            <span className="text-gray-500">
              — {task.keyword}
              {task.location ? `, ${task.location}` : ""}
            </span>
          )}
        </div>
        <span className="font-mono text-gray-400">
          {task.progress} / {task.total || "?"} leads
        </span>
      </div>

      {/* Track */}
      <div className="h-1.5 bg-surface-600 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${STATUS_COLOR[task.status] || "bg-gray-500"} ${
            isLive ? "animate-pulse-slow" : ""
          }`}
          style={{ width: `${task.status === "running" && pct === 0 ? 5 : pct}%` }}
        />
      </div>

      {isFail && task.error && (
        <p className="text-xs text-red-400 font-mono bg-red-900/20 px-3 py-2 rounded-lg border border-red-800/40">
          {task.error}
        </p>
      )}
    </div>
  );
}
