
import React from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useTaskPoller }  from "../hooks/useTaskPoller";
import ProgressBar        from "../components/ProgressBar";
import ResultsTable       from "../components/ResultsTable";
import LogsPanel          from "../components/LogsPanel";
import ExportButton       from "../components/ExportButton";
import EnrichButton       from "../components/EnrichButton";
import { formatDate }     from "../utils/formatters";

export default function Results() {
  const { taskId } = useParams();
  const navigate   = useNavigate();

  const {
    task,
    leads,
    logs,
    pagination,
    filters,
    error,
    loading,
    goToPage,
    applyFilters,
    resumePolling,
  } = useTaskPoller(taskId);

  if (loading && !task) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex flex-col items-center gap-3 text-gray-500">
          <span className="w-6 h-6 border-2 border-surface-600 border-t-brand-500
                           rounded-full animate-spin" />
          <p className="text-sm">Loading task…</p>
        </div>
      </div>
    );
  }

  if (error && !task) {
    return (
      <div className="max-w-xl mx-auto px-6 py-12">
        <div className="card text-center">
          <p className="text-red-400 text-sm mb-4">{error}</p>
          <button onClick={() => navigate("/")} className="btn-secondary text-sm">
            ← Back to Search
          </button>
        </div>
      </div>
    );
  }

  const taskTitle = task?.keyword
    ? `${task.keyword}${task.location ? ` · ${task.location}` : ""}`
    : task?.dork_query || "Scraping Task";

  return (
    <div className="max-w-6xl mx-auto px-6 py-8 space-y-5 animate-fade-in">

      <div className="flex items-start justify-between gap-4">

        <div className="flex items-center gap-3 min-w-0">
          <button
            onClick={() => navigate("/")}
            className="text-gray-500 hover:text-gray-300 transition-colors shrink-0"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}
              className="w-5 h-5">
              <path d="m15 18-6-6 6-6" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>
          <div className="min-w-0">
            <h1 className="text-base font-semibold text-gray-100 truncate">
              {taskTitle}
            </h1>
            <p className="text-xs text-gray-500 font-mono mt-0.5">
              {taskId?.slice(0, 8)}… · {formatDate(task?.created_at)}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <span className={`tag tag-${task?.source === "maps" ? "maps" : "dorks"}`}>
            {task?.source}
          </span>

          <EnrichButton
            taskId={taskId}
            taskStatus={task?.status}
            enrichmentStatus={task?.enrichment_status}
            onStarted={resumePolling}
          />

          <ExportButton
            taskId={taskId}
            taskStatus={task?.status}
            total={pagination.total}
            filters={filters}
          />
        </div>
      </div>

      <div className="card">
        <ProgressBar task={task} />
      </div>

      {pagination.total > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            {
              label: "Total Leads",
              value: pagination.total,
              color: "text-gray-100",
            },
            {
              label: "With Email",
              value: leads.filter((l) => l.email).length,
              note:  "on this page",
              color: "text-brand-400",
            },
            {
              label: "With Phone",
              value: leads.filter((l) => l.phone).length,
              note:  "on this page",
              color: "text-blue-400",
            },
            {
              label: "Enriched",
              value: leads.filter((l) => l.enriched).length,
              note:  "on this page",
              color: "text-yellow-400",
            },
          ].map(({ label, value, note, color }) => (
            <div key={label}
              className="bg-surface-800 border border-surface-600 rounded-xl px-4 py-3">
              <p className={`text-xl font-display font-semibold ${color}`}>{value}</p>
              <p className="text-xs text-gray-500 mt-0.5">{label}</p>
              {note && <p className="text-[10px] text-gray-700 mt-0.5">{note}</p>}
            </div>
          ))}
        </div>
      )}

      <div className="card">
        <h2 className="text-sm font-semibold text-gray-300 mb-4 flex items-center gap-2">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8}
            className="w-4 h-4 text-brand-400">
            <path d="M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2"
              strokeLinecap="round" />
            <rect x="9" y="3" width="6" height="4" rx="1" />
          </svg>
          Collected Leads
          <span className="text-gray-600 font-normal font-mono text-xs">
            — click column headers to sort
          </span>
        </h2>

        <ResultsTable
          leads={leads}
          pagination={pagination}
          filters={filters}
          onFiltersChange={applyFilters}
          onPageChange={goToPage}
        />
      </div>

      <LogsPanel logs={logs} />

    </div>
  );
}