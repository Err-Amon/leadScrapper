import { useState, useEffect, useRef, useCallback } from "react";
import { getTaskStatus, getTaskResults, getTaskLogs } from "../services/api";

const POLL_INTERVAL_MS = 2000;
const TERMINAL_STATUSES = new Set(["completed", "failed"]);


export function useTaskPoller(taskId) {
  const [task, setTask]       = useState(null);
  const [leads, setLeads]     = useState([]);
  const [logs, setLogs]       = useState([]);
  const [pagination, setPagination] = useState({ page: 1, total: 0, totalPages: 1 });
  const [error, setError]     = useState(null);
  const [loading, setLoading] = useState(true);

  const intervalRef = useRef(null);
  const pageRef     = useRef(1);

  const fetchAll = useCallback(async () => {
    if (!taskId) return;
    try {
      const [statusRes, resultsRes, logsRes] = await Promise.all([
        getTaskStatus(taskId),
        getTaskResults(taskId, pageRef.current, 20),
        getTaskLogs(taskId, 60),
      ]);

      setTask(statusRes.data);
      setLeads(resultsRes.data.leads);
      setLogs(logsRes.data.logs);
      setPagination({
        page:       resultsRes.data.page,
        total:      resultsRes.data.total,
        totalPages: resultsRes.data.total_pages,
      });
      setError(null);

      // Stop polling once terminal
      if (TERMINAL_STATUSES.has(statusRes.data.status)) {
        clearInterval(intervalRef.current);
      }
    } catch (err) {
      setError(err?.response?.data?.detail || "Failed to fetch task data.");
    } finally {
      setLoading(false);
    }
  }, [taskId]);

  useEffect(() => {
    if (!taskId) return;
    setLoading(true);
    fetchAll();
    intervalRef.current = setInterval(fetchAll, POLL_INTERVAL_MS);
    return () => clearInterval(intervalRef.current);
  }, [taskId, fetchAll]);

  const goToPage = useCallback((page) => {
    pageRef.current = page;
    fetchAll();
  }, [fetchAll]);

  return { task, leads, logs, pagination, error, loading, goToPage, refresh: fetchAll };
}
