
import { useState, useEffect, useRef, useCallback } from "react";
import { getTaskStatus, getTaskResults, getTaskLogs } from "../services/api";

const POLL_INTERVAL_MS  = 2000;
const SCRAPE_TERMINAL   = new Set(["completed", "failed", "cancelled"]);

export function useTaskPoller(taskId) {
  const [task,       setTask]       = useState(null);
  const [leads,      setLeads]      = useState([]);
  const [logs,       setLogs]       = useState([]);
  const [pagination, setPagination] = useState({ page: 1, total: 0, totalPages: 1 });
  const [filters,    setFilters]    = useState({
    search:   "",
    source:   "",
    hasEmail: false,
    hasPhone: false,
  });
  const [error,   setError]   = useState(null);
  const [loading, setLoading] = useState(true);

  const intervalRef  = useRef(null);
  const pageRef      = useRef(1);
  const filtersRef   = useRef(filters);
  const taskIdRef    = useRef(taskId);

  useEffect(() => { filtersRef.current = filters; }, [filters]);
  useEffect(() => { taskIdRef.current = taskId; }, [taskId]);

  const fetchAll = useCallback(async () => {
    const currentTaskId = taskIdRef.current;
    if (!currentTaskId) return;
    try {
      const [statusRes, resultsRes, logsRes] = await Promise.all([
        getTaskStatus(currentTaskId),
        getTaskResults(currentTaskId, pageRef.current, 20, filtersRef.current),
        getTaskLogs(currentTaskId, 60),
      ]);

      const taskData = statusRes.data;
      setTask(taskData);
      setLeads(resultsRes.data.leads);
      setLogs(logsRes.data.logs);
      setPagination({
        page:       resultsRes.data.page,
        total:      resultsRes.data.total,
        totalPages: resultsRes.data.total_pages,
      });
      setError(null);

      const scrapeTerminal    = SCRAPE_TERMINAL.has(taskData.status);
      const enrichmentRunning = taskData.enrichment_status === "running";

      if (scrapeTerminal && !enrichmentRunning) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    } catch (err) {
      setError(err?.response?.data?.detail || "Failed to fetch task data.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!taskId) return;
    setLoading(true);
    fetchAll();
    intervalRef.current = setInterval(fetchAll, POLL_INTERVAL_MS);
    return () => {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    };
  }, [taskId, fetchAll]);

  const applyFilters = useCallback((newFilters) => {
    pageRef.current = 1;
    setFilters(newFilters);
    setTimeout(() => fetchAll(), 0);
  }, [fetchAll]);

  const goToPage = useCallback((page) => {
    pageRef.current = page;
    fetchAll();
  }, [fetchAll]);

  const resumePolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }
    intervalRef.current = setInterval(fetchAll, POLL_INTERVAL_MS);
  }, [fetchAll]);

  return {
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
    refresh: fetchAll,
  };
}
