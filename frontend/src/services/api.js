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

export const getTaskLogs = (taskId, tail = 50) =>
  api.get(`/tasks/${taskId}/logs`, { params: { tail } });


export const getTaskResults = (taskId, page = 1, pageSize = 20) =>
  api.get(`/tasks/${taskId}/results`, { params: { page, page_size: pageSize } });


export const getExportUrl = (taskId) =>
  `http://localhost:8000/api/tasks/${taskId}/export`;


export const healthCheck = () =>
  api.get("/health");

export default api;
