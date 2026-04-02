
import React, { useEffect, useState, useCallback } from "react";
import { useNavigate }  from "react-router-dom";
import { getAllTasks }   from "../services/api";
import { useToast }     from "../components/Toast";
import { formatDate, truncate } from "../utils/formatters";
import api from "../services/api";

export default function TaskHistory() {
  const navigate          = useNavigate();
  const toast             = useToast();
  const [tasks, setTasks]       = useState([]);
  const [loading, setLoading]   = useState(true);
  const [error, setError]       = useState("");
  const [cancelling, setCancelling] = useState(null); // task id being cancelled

  const fetchTasks = useCallback(() => {
    setLoading(true);
    setError("");
    getAllTasks()
      .then((res) => setTasks(res.data))
      .catch(() => setError("Could not load task history."))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { fetchTasks(); }, [fetchTasks]);

  async function handleCancel(e, taskId) {
    e.stopPropagation();
    setCancelling(taskId);
    try {
      await api.post(`/tasks/${taskId}/cancel`);
      toast.warning("Task cancellation requested — it will stop after the current batch.");
      fetchTasks();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not cancel task.");
    } finally {
      setCancelling(null);
    }
  }

  return (
    <div className="max-w-4xl mx-auto px-6 py-10">

      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-display font-semibold text-gray-100 mb-1">
            Task History
          </h1>
          <p className="text-gray-500 text-sm">
            All scraping tasks — click any row to view results.
          </p>
        </div>
        <button
          onClick={fetchTasks}
          disabled={loading}
          className="btn-secondary flex items-center gap-2 text-sm py-2 px-3"
          title="Refresh list"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
            strokeWidth={2}
            className={`w-4 h-4 ${loading ? "animate-spin" : ""}`}>
            <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"
              strokeLinecap="round" />
            <path d="M21 3v5h-5" strokeLinecap="round" strokeLinejoin="round" />
            <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"
              strokeLinecap="round" />
            <path d="M8 16H3v5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          Refresh
        </button>
      </div>

      {loading && (
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <div
              key={i}
              className="card flex items-center gap-4"
              style={{ animationDelay: `${i * 80}ms` }}
            >
              <div className="skeleton w-14 h-6 shrink-0" />
              <div className="flex-1 space-y-2">
                <div className="skeleton h-4 w-48" />
                <div className="skeleton h-3 w-32" />
              </div>
              <div className="space-y-2 text-right shrink-0">
                <div className="skeleton h-5 w-20 ml-auto" />
                <div className="skeleton h-3 w-16 ml-auto" />
              </div>
            </div>
          ))}
        </div>
      )}

      {!loading && error && (
        <div className="card text-center py-10">
          <p className="text-red-400 text-sm mb-4">{error}</p>
          <button onClick={fetchTasks} className="btn-secondary text-sm">
            Try Again
          </button>
        </div>
      )}

      {!loading && !error && tasks.length === 0 && (
        <div className="card text-center py-14 animate-fade-in">
          <div className="w-12 h-12 rounded-full bg-surface-700 flex items-center
                          justify-center mx-auto mb-4">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
              strokeWidth={1.5} className="w-6 h-6 text-gray-600">
              <circle cx="11" cy="11" r="8" />
              <path d="m21 21-4.35-4.35" strokeLinecap="round" />
            </svg>
          </div>
          <p className="text-gray-500 text-sm mb-1">No tasks yet</p>
          <p className="text-gray-700 text-xs mb-5">
            Start your first search to begin collecting leads.
          </p>
          <button
            onClick={() => navigate("/")}
            className="btn-primary text-sm"
          >
            New Search
          </button>
        </div>
      )}

      {!loading && !error && tasks.length > 0 && (
        <div className="space-y-2 animate-fade-in">
          {tasks.map((task, i) => (
            <div
              key={task.id}
              onClick={() => navigate(`/results/${task.id}`)}
              className="card-hover flex items-center gap-4 animate-slide-up"
              style={{
                animationDelay: `${Math.min(i * 40, 240)}ms`,
                animationFillMode: "both",
              }}
            >
              <span className={`tag shrink-0 ${
                task.source === "maps" ? "tag-maps" : "tag-dorks"
              }`}>
                {task.source}
              </span>

              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-200 truncate">
                  {task.keyword
                    ? `${task.keyword}${task.location ? ` · ${task.location}` : ""}`
                    : truncate(task.dork_query, 55) || "—"}
                </p>
                <div className="flex items-center gap-2 mt-0.5">
                  <p className="text-xs text-gray-600 font-mono">
                    {task.id.slice(0, 8)}…
                  </p>
                  <span className="text-gray-700 text-xs">·</span>
                  <p className="text-xs text-gray-600">
                    {formatDate(task.created_at)}
                  </p>
                  {task.enrichment_status && task.enrichment_status !== "none" && (
                    <>
                      <span className="text-gray-700 text-xs">·</span>
                      <span className={`text-[10px] font-mono ${
                        task.enrichment_status === "completed" ? "text-brand-600" :
                        task.enrichment_status === "running"   ? "text-yellow-600" :
                        task.enrichment_status === "failed"    ? "text-red-600"    :
                        "text-gray-700"
                      }`}>
                        {task.enrichment_status === "completed" ? "enriched" :
                         task.enrichment_status === "running"   ? "enriching…" :
                         task.enrichment_status === "failed"    ? "enrich failed" : ""}
                      </span>
                    </>
                  )}
                </div>
              </div>

              <div className="flex items-center gap-3 shrink-0">
                <div className="text-right">
                  <span className={`tag tag-${task.status}`}>
                    {task.status}
                  </span>
                  <p className="text-xs font-mono text-gray-600 mt-1">
                    {task.progress}/{task.total || "?"} leads
                  </p>
                </div>

                {task.status === "running" && (
                  <button
                    onClick={(e) => handleCancel(e, task.id)}
                    disabled={cancelling === task.id}
                    className="btn-danger py-1.5 px-2.5 text-xs shrink-0"
                    title="Cancel this task after current batch"
                  >
                    {cancelling === task.id ? (
                      <span className="w-3 h-3 border-2 border-red-800
                                       border-t-red-400 rounded-full animate-spin" />
                    ) : "Cancel"}
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}