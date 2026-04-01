import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getAllTasks } from "../services/api";
import { formatDate, truncate } from "../utils/formatters";

export default function TaskHistory() {
  const navigate    = useNavigate();
  const [tasks, setTasks]   = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError]   = useState("");

  useEffect(() => {
    getAllTasks()
      .then((res) => setTasks(res.data))
      .catch(() => setError("Could not load task history."))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="max-w-4xl mx-auto px-6 py-10">
      <div className="mb-8">
        <h1 className="text-2xl font-display font-700 text-gray-100 mb-1">Task History</h1>
        <p className="text-gray-500 text-sm">All scraping tasks — click any row to view results.</p>
      </div>

      {loading && (
        <div className="flex justify-center py-12">
          <span className="w-6 h-6 border-2 border-surface-600 border-t-brand-500 rounded-full animate-spin" />
        </div>
      )}

      {error && (
        <div className="card text-center">
          <p className="text-red-400 text-sm">{error}</p>
        </div>
      )}

      {!loading && !error && tasks.length === 0 && (
        <div className="card text-center py-12 text-gray-600">
          <p className="text-sm">No tasks yet.</p>
          <button
            onClick={() => navigate("/")}
            className="mt-4 btn-primary text-sm"
          >
            Start Your First Search
          </button>
        </div>
      )}

      {!loading && tasks.length > 0 && (
        <div className="space-y-2 animate-fade-in">
          {tasks.map((task) => (
            <button
              key={task.id}
              onClick={() => navigate(`/results/${task.id}`)}
              className="w-full card hover:border-surface-500 hover:bg-surface-700 transition-all duration-150 text-left flex items-center gap-4"
            >
              {/* Source badge */}
              <span className={`tag shrink-0 ${task.source === "maps" ? "tag-maps" : "tag-dorks"}`}>
                {task.source}
              </span>

              {/* Info */}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-200 truncate">
                  {task.keyword
                    ? `${task.keyword}${task.location ? ` · ${task.location}` : ""}`
                    : truncate(task.dork_query, 60) || "—"}
                </p>
                <p className="text-xs text-gray-500 font-mono mt-0.5">
                  {task.id.slice(0, 8)}… · {formatDate(task.created_at)}
                </p>
              </div>

              {/* Progress */}
              <div className="text-right shrink-0">
                <span className={`tag tag-${task.status}`}>{task.status}</span>
                <p className="text-xs font-mono text-gray-500 mt-1">
                  {task.progress}/{task.total || "?"} leads
                </p>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
