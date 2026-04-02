
import React, { useState } from "react";
import { useNavigate }   from "react-router-dom";
import SearchForm        from "../components/SearchForm";
import { useToast }      from "../components/Toast";
import { startMapsTask, startDorksTask } from "../services/api";

const FEATURES = [
  {
    title: "Maps Mode",
    desc:  "Searches Google for local businesses by keyword + location. Extracts name, phone, address, website, and rating.",
  },
  {
    title: "Dorks Mode",
    desc:  "Runs advanced Google queries, visits each result page, and extracts emails, phones, and contact info.",
  },
  {
    title: "Enrichment",
    desc:  "After scraping, visit each website to find missing emails, phone numbers, and social media links.",
  },
  {
    title: "Export CSV",
    desc:  "Download all collected leads as a clean CSV, optionally filtered by source, email, or phone presence.",
  },
];

const TIPS = [
  "Be specific with location — city + country works best.",
  "Use Dorks mode to find emails not listed on Maps.",
  "Run Enrichment after Maps mode to fill in missing emails.",
  "Reduce Max Results for faster, lighter scrapes.",
];

export default function Dashboard() {
  const navigate  = useNavigate();
  const toast     = useToast();
  const [loading, setLoading] = useState(false);

  async function handleSubmit({ mode, keyword, location, dorkQuery, maxResults }) {
    setLoading(true);
    try {
      const res = mode === "maps"
        ? await startMapsTask(keyword, location, maxResults)
        : await startDorksTask(dorkQuery, maxResults);

      navigate(`/results/${res.data.task_id}`);
    } catch (err) {
      const msg = err?.response?.data?.detail
        || "Failed to start task. Is the backend running on port 8000?";
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-2xl mx-auto px-6 py-10">

      <div className="mb-8 animate-fade-in">
        <h1 className="text-2xl font-display font-semibold text-gray-100 mb-2">
          Lead Intelligence
        </h1>
        <p className="text-gray-500 text-sm leading-relaxed max-w-md">
          Extract business contacts from Google Maps or advanced search queries.
          Results are cleaned, deduplicated, and ready to export.
        </p>
      </div>

      <div className="card animate-scale-in">
        <SearchForm onSubmit={handleSubmit} loading={loading} />
      </div>

      <div className="mt-4 px-4 py-3 bg-surface-700/40 border border-surface-600
                      rounded-xl flex items-start gap-2.5 animate-fade-in">
        <span className="text-brand-600 text-xs mt-0.5 shrink-0"></span>
        <p className="text-xs text-gray-500 leading-relaxed">
          <span className="text-gray-400 font-medium">Tip: </span>
          {TIPS[Math.floor(Date.now() / 60000) % TIPS.length]}
        </p>
      </div>

      <div className="mt-6 grid grid-cols-2 gap-3">
        {FEATURES.map((item, i) => (
          <div
            key={item.title}
            className="bg-surface-700/40 border border-surface-600 rounded-xl p-4
                       hover:border-surface-500 transition-colors duration-150 animate-fade-in"
            style={{ animationDelay: `${i * 60}ms`, animationFillMode: "both" }}
          >
            <span className="text-base mb-2 block">{item.icon}</span>
            <p className="text-sm font-medium text-gray-200 mb-1">{item.title}</p>
            <p className="text-xs text-gray-500 leading-relaxed">{item.desc}</p>
          </div>
        ))}
      </div>
    </div>
  );
}