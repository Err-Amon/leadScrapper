import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import SearchForm from "../components/SearchForm";
import { startMapsTask, startDorksTask } from "../services/api";

export default function Dashboard() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState("");

  async function handleSubmit({ mode, keyword, location, dorkQuery, maxResults }) {
    setLoading(true);
    setError("");
    try {
      let res;
      if (mode === "maps") {
        res = await startMapsTask(keyword, location, maxResults);
      } else {
        res = await startDorksTask(dorkQuery, maxResults);
      }
      const taskId = res.data.task_id;
      navigate(`/results/${taskId}`);
    } catch (err) {
      setError(
        err?.response?.data?.detail || "Failed to start task. Is the backend running?"
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-2xl mx-auto px-6 py-12">
      {/* Header */}
      <div className="mb-10 animate-fade-in">
        <h1 className="text-2xl font-display font-700 text-gray-100 mb-2">
          Lead Intelligence
        </h1>
        <p className="text-gray-500 text-sm leading-relaxed">
          Extract business contacts from Google Maps or advanced Dork queries.
          Results are collected, cleaned, and ready to export.
        </p>
      </div>

      {/* Form card */}
      <div className="card">
        <SearchForm onSubmit={handleSubmit} loading={loading} />
        {error && (
          <div className="mt-4 p-3 bg-red-900/20 border border-red-800/40 rounded-lg">
            <p className="text-xs text-red-400 font-mono">{error}</p>
          </div>
        )}
      </div>

      {/* How it works */}
      <div className="mt-8 grid grid-cols-2 gap-3 animate-slide-up">
        {[
          {
            icon: "🗺",
            title: "Maps Mode",
            desc: "Searches Google Maps for businesses by keyword + location. Extracts name, phone, address, website, rating.",
          },
          {
            icon: "🔍",
            title: "Dorks Mode",
            desc: "Runs advanced Google queries. Visits result pages and extracts emails, phone numbers, and contact info.",
          },
        ].map((item) => (
          <div key={item.title} className="bg-surface-700/50 border border-surface-600 rounded-xl p-4">
            <p className="text-lg mb-2">{item.icon}</p>
            <p className="text-sm font-medium text-gray-200 mb-1">{item.title}</p>
            <p className="text-xs text-gray-500 leading-relaxed">{item.desc}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
