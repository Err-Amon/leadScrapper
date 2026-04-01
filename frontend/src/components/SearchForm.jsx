import React, { useState } from "react";

export default function SearchForm({ onSubmit, loading }) {
  const [mode, setMode]         = useState("maps"); // 'maps' | 'dorks'
  const [keyword, setKeyword]   = useState("");
  const [location, setLocation] = useState("");
  const [dorkQuery, setDorkQuery] = useState("");
  const [maxResults, setMaxResults] = useState(20);
  const [errors, setErrors]     = useState({});

  function validate() {
    const e = {};
    if (mode === "maps") {
      if (!keyword.trim())  e.keyword  = "Keyword is required.";
      if (!location.trim()) e.location = "Location is required.";
    } else {
      if (!dorkQuery.trim()) e.dorkQuery = "Dork query is required.";
    }
    setErrors(e);
    return Object.keys(e).length === 0;
  }

  function handleSubmit(e) {
    e.preventDefault();
    if (!validate()) return;
    onSubmit({ mode, keyword, location, dorkQuery, maxResults });
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6 animate-fade-in">
      {/* Mode toggle */}
      <div className="flex gap-2 p-1 bg-surface-700 rounded-lg w-fit">
        {["maps", "dorks"].map((m) => (
          <button
            key={m}
            type="button"
            onClick={() => { setMode(m); setErrors({}); }}
            className={`px-5 py-2 rounded-md text-sm font-medium transition-all duration-200 ${
              mode === m
                ? "bg-brand-500 text-surface-900 shadow"
                : "text-gray-400 hover:text-gray-200"
            }`}
          >
            {m === "maps" ? "🗺  Google Maps" : "🔍  Google Dorks"}
          </button>
        ))}
      </div>

      {/* Maps fields */}
      {mode === "maps" && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 animate-slide-up">
          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1.5">
              Keyword
            </label>
            <input
              className="input-field"
              placeholder="e.g. plumbers, dentists, lawyers"
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
            />
            {errors.keyword && (
              <p className="text-red-400 text-xs mt-1">{errors.keyword}</p>
            )}
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1.5">
              Location
            </label>
            <input
              className="input-field"
              placeholder="e.g. Lahore, Pakistan"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
            />
            {errors.location && (
              <p className="text-red-400 text-xs mt-1">{errors.location}</p>
            )}
          </div>
        </div>
      )}

      {/* Dorks field */}
      {mode === "dorks" && (
        <div className="animate-slide-up">
          <label className="block text-xs font-medium text-gray-400 mb-1.5">
            Google Dork Query
          </label>
          <input
            className="input-field font-mono"
            placeholder='e.g. "plumbers in Lahore" "contact us" email'
            value={dorkQuery}
            onChange={(e) => setDorkQuery(e.target.value)}
          />
          {errors.dorkQuery && (
            <p className="text-red-400 text-xs mt-1">{errors.dorkQuery}</p>
          )}
          <div className="mt-3 flex flex-wrap gap-2">
            {[
              'site:linkedin.com "CEO" email',
              '"plumbers Lahore" contact',
              'intext:"@gmail.com" "real estate"',
            ].map((example) => (
              <button
                key={example}
                type="button"
                onClick={() => setDorkQuery(example)}
                className="text-[11px] font-mono text-gray-500 hover:text-brand-400 bg-surface-700 hover:bg-surface-600 px-2.5 py-1 rounded-md border border-surface-500 transition-colors"
              >
                {example}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Max results */}
      <div className="flex items-center gap-4">
        <div>
          <label className="block text-xs font-medium text-gray-400 mb-1.5">
            Max Results
          </label>
          <select
            className="input-field w-32"
            value={maxResults}
            onChange={(e) => setMaxResults(Number(e.target.value))}
          >
            {[10, 20, 30, 50, 100].map((n) => (
              <option key={n} value={n}>{n} results</option>
            ))}
          </select>
        </div>

        <div className="pt-5">
          <button
            type="submit"
            disabled={loading}
            className="btn-primary flex items-center gap-2"
          >
            {loading ? (
              <>
                <span className="w-4 h-4 border-2 border-surface-900/30 border-t-surface-900 rounded-full animate-spin" />
                Starting…
              </>
            ) : (
              <>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.2} className="w-4 h-4">
                  <polygon points="5 3 19 12 5 21 5 3" fill="currentColor" stroke="none" />
                </svg>
                Start Scraping
              </>
            )}
          </button>
        </div>
      </div>
    </form>
  );
}
