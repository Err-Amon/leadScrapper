

import { useState, useEffect, useRef, useCallback } from "react";
import { getTaskStatus, getTaskResults, getTaskLogs } from "../services/api";

const POLL_INTERVAL_MS  = 2000;
const SCRAPE_TERMINAL   = new Set(["completed", "failed"]);

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

  // Keep filtersRef in sync so the interval callback always reads current values
  useEffect(() => { filtersRef.current = filters; }, [filters]);

  const fetchAll = useCallback(async () => {
    if (!taskId) return;
    try {
      const [statusRes, resultsRes, logsRes] = await Promise.all([
        getTaskStatus(taskId),
        getTaskResults(taskId, pageRef.current, 20, filtersRef.current),
        getTaskLogs(taskId, 60),
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

      // Stop polling only when scrape is terminal AND enrichment is not running
      const scrapeTerminal    = SCRAPE_TERMINAL.has(taskData.status);
      const enrichmentRunning = taskData.enrichment_status === "running";

      if (scrapeTerminal && !enrichmentRunning) {
        clearInterval(intervalRef.current);
      }
    } catch (err) {
      setError(err?.response?.data?.detail || "Failed to fetch task data.");
    } finally {
      setLoading(false);
    }
  }, [taskId]);

  // Start polling on mount, restart if taskId changes
  useEffect(() => {
    if (!taskId) return;
    setLoading(true);
    fetchAll();
    intervalRef.current = setInterval(fetchAll, POLL_INTERVAL_MS);
    return () => clearInterval(intervalRef.current);
  }, [taskId, fetchAll]);

  // When filters change: reset to page 1, re-fetch immediately, restart polling
  const applyFilters = useCallback((newFilters) => {
    pageRef.current = 1;
    setFilters(newFilters);
    // fetchAll reads filtersRef which will be updated on next render —
    // use setTimeout(0) to let the ref update first
    setTimeout(() => fetchAll(), 0);
  }, [fetchAll]);

  const goToPage = useCallback((page) => {
    pageRef.current = page;
    fetchAll();
  }, [fetchAll]);

  // Restart polling (used after triggering enrichment so UI stays live)
  const resumePolling = useCallback(() => {
    clearInterval(intervalRef.current);
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