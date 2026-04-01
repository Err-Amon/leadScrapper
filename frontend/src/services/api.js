

import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8000/api",
  timeout: 15000,
  headers: { "Content-Type": "application/json" },
});


export const startMapsTask = (keyword, location, maxResults = 20) =>
  api.post("/tasks/maps", { keyword, location, max_results: maxResults });

export const startDorksTask = (dorkQuery, maxResults = 20) =>
  api.post("/tasks/dorks", { dork_query: dorkQuery, max_results: maxResults });

export const getTaskStatus = (taskId) =>
  api.get(`/tasks/${taskId}`);

export const getAllTasks = () =>
  api.get("/tasks");

export const getTaskLogs = (taskId, tail = 60) =>
  api.get(`/tasks/${taskId}/logs`, { params: { tail } });


export const triggerEnrichment = (taskId) =>
  api.post(`/tasks/${taskId}/enrich`);


export const getTaskResults = (taskId, page = 1, pageSize = 20, filters = {}) =>
  api.get(`/tasks/${taskId}/results`, {
    params: {
      page,
      page_size: pageSize,
      search:    filters.search    || "",
      source:    filters.source    || "",
      has_email: filters.hasEmail  || false,
      has_phone: filters.hasPhone  || false,
    },
  });



export const getExportUrl = (taskId, filters = {}) => {
  const params = new URLSearchParams();
  if (filters.search)    params.set("search",    filters.search);
  if (filters.source)    params.set("source",    filters.source);
  if (filters.hasEmail)  params.set("has_email", "true");
  if (filters.hasPhone)  params.set("has_phone", "true");
  const qs = params.toString();
  return `http://localhost:8000/api/tasks/${taskId}/export${qs ? `?${qs}` : ""}`;
};


export const healthCheck = () =>
  api.get("/health");

export default api;