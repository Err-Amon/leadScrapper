
import React, { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useTaskPoller }   from "../hooks/useTaskPoller";
import { useToast }        from "../components/Toast";
import ProgressBar         from "../components/ProgressBar";
import ResultsTable        from "../components/ResultsTable";
import LogsPanel           from "../components/LogsPanel";
import ExportButton        from "../components/ExportButton";
import EnrichButton        from "../components/EnrichButton";
import { formatDate }      from "../utils/formatters";
import api                 from "../services/api";

export default function Results() {
  const { taskId } = useParams();
  const navigate   = useNavigate();
  const toast      = useToast();

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
    refresh,
  } = useTaskPoller(taskId);

  const [cancelling, setCancelling] = useState(false);
  const [idCopied,   setIdCopied]   = useState(false);

  async function handleCancel() {
    if (!taskId || cancelling) return;
    setCancelling(true);
    try {
      await api.post(`/tasks/${taskId}/cancel`);
      toast.warning("Cancellation requested — task will stop after the current batch.");
      refresh();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not cancel the task.");
    } finally {
      setCancelling(false);
    }
  }

  async function copyTaskId() {
    try {
      await navigator.clipboard.writeText(taskId);
      setIdCopied(true);
      setTimeout(() => setIdCopied(false), 2000);
    } catch { /* ignore */ }
  }

  if (loading && !task) {
    return (
      <div className="max-w-6xl mx-auto px-6 py-8 space-y-5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="skeleton w-5 h-5 rounded" />
            <div className="space-y-1.5">
              <div className="skeleton w-44 h-4" />
              <div className="skeleton w-32 h-3" />
            </div>
          </div>
          <div className="flex gap-2">
            <div className="skeleton w-16 h-8 rounded-lg" />
            <div className="skeleton w-24 h-8 rounded-lg" />
          </div>
        </div>
        <div className="card space-y-3">
          <div className="skeleton w-24 h-3" />
          <div className="skeleton w-full h-1.5 rounded-full" />
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="card space-y-2">
              <div className="skeleton w-10 h-6" />
              <div className="skeleton w-20 h-3" />
            </div>
          ))}
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

  const isRunning   = task?.status === "running";
  const isFailed    = task?.status === "failed";
  const isCancelled = task?.status === "cancelled";

  return (
    <div className="max-w-6xl mx-auto px-6 py-8 space-y-5 animate-fade-in">

      <div className="flex items-start justify-between gap-4">

        <div className="flex items-center gap-3 min-w-0">
          <button
            onClick={() => navigate("/")}
            className="text-gray-500 hover:text-gray-300 transition-colors shrink-0"
            title="New search"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
              strokeWidth={2} className="w-5 h-5">
              <path d="m15 18-6-6 6-6" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>

          <div className="min-w-0">
            <h1 className="text-base font-semibold text-gray-100 truncate">
              {taskTitle}
            </h1>
            <button
              onClick={copyTaskId}
              title="Click to copy task ID"
              className="text-xs text-gray-600 font-mono mt-0.5 hover:text-gray-400
                         transition-colors flex items-center gap-1"
            >
              {idCopied ? (
                <span className="text-brand-500 animate-fade-in">copied</span>
              ) : (
                <>
                  {taskId?.slice(0, 8)}… · {formatDate(task?.created_at)}
                </>
              )}
            </button>
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0 flex-wrap justify-end">
          <span className={`tag tag-${task?.source === "maps" ? "maps" : "dorks"}`}>
            {task?.source}
          </span>

          {isRunning && (
            <button
              onClick={handleCancel}
              disabled={cancelling}
              className="btn-danger flex items-center gap-1.5"
              title="Stop after the current batch"
            >
              {cancelling ? (
                <span className="w-3 h-3 border-2 border-red-800
                                 border-t-red-400 rounded-full animate-spin" />
              ) : (
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
                  strokeWidth={2} className="w-3.5 h-3.5">
                  <rect x="6" y="6" width="12" height="12" rx="1" fill="currentColor"
                    stroke="none" />
                </svg>
              )}
              {cancelling ? "Stopping…" : "Cancel"}
            </button>
          )}

          <EnrichButton
            taskId={taskId}
            taskStatus={task?.status}
            enrichmentStatus={task?.enrichment_status}
            onStarted={() => {
              resumePolling();
              toast.info("Enrichment started — visiting websites to find missing emails.");
            }}
          />

          <ExportButton
            taskId={taskId}
            taskStatus={task?.status}
            total={pagination.total}
            filters={filters}
            onExport={() => toast.success("CSV download started!")}
          />
        </div>
      </div>

      {isFailed && task?.error && (
        <div className="flex items-start gap-3 px-4 py-3 bg-red-900/20
                        border border-red-800/40 rounded-xl animate-slide-down">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}
            className="w-4 h-4 text-red-400 shrink-0 mt-0.5">
            <circle cx="12" cy="12" r="10" />
            <path d="M12 8v4m0 4h.01" strokeLinecap="round" />
          </svg>
          <p className="text-xs text-red-300 font-mono leading-relaxed">
            {task.error}
          </p>
        </div>
      )}

      {isCancelled && (
        <div className="flex items-center gap-3 px-4 py-3 bg-orange-900/20
                        border border-orange-800/40 rounded-xl animate-slide-down">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}
            className="w-4 h-4 text-orange-400 shrink-0">
            <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"
              strokeLinecap="round" strokeLinejoin="round" />
            <path d="M12 9v4m0 4h.01" strokeLinecap="round" />
          </svg>
          <p className="text-xs text-orange-300">
            Task was cancelled. {pagination.total > 0
              ? `${pagination.total} leads were saved before stopping.`
              : "No leads were saved."}
          </p>
        </div>
      )}

      <div className="card">
        <ProgressBar task={task} />
      </div>

      {pagination.total > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { label: "Total Leads",   value: pagination.total,                       color: "text-gray-100" },
            { label: "With Email",    value: leads.filter((l) => l.email).length,    color: "text-brand-400", note: "this page" },
            { label: "With Phone",    value: leads.filter((l) => l.phone).length,    color: "text-blue-400",  note: "this page" },
            { label: "Enriched",      value: leads.filter((l) => l.enriched).length, color: "text-yellow-400", note: "this page" },
          ].map(({ label, value, color, note }) => (
            <div key={label}
              className="bg-surface-800 border border-surface-600 rounded-xl
                         px-4 py-3 animate-scale-in">
              <p className={`text-xl font-display font-semibold ${color} stat-value`}>
                {value}
              </p>
              <p className="text-xs text-gray-500 mt-0.5">{label}</p>
              {note && (
                <p className="text-[10px] text-gray-700 mt-0.5">{note}</p>
              )}
            </div>
          ))}
        </div>
      )}

      <div className="card">
        <h2 className="text-sm font-semibold text-gray-300 mb-4 flex items-center gap-2">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
            strokeWidth={1.8} className="w-4 h-4 text-brand-400">
            <path d="M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0
                     0 2-2V7a2 2 0 0 0-2-2h-2" strokeLinecap="round" />
            <rect x="9" y="3" width="6" height="4" rx="1" />
          </svg>
          Collected Leads
          <span className="text-gray-600 font-normal font-mono text-xs">
            — click headers to sort · click cells to copy
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