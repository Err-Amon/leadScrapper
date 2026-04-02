
import React, { useState, useRef, useCallback } from "react";

const DORK_EXAMPLES = [
  '"plumbers Lahore" "contact us"',
  'intext:"@gmail.com" "real estate"',
  'site:.pk "dentist" email contact',
  '"restaurants Dubai" phone',
];

export default function SearchForm({ onSubmit, loading }) {
  const [mode,       setMode]       = useState("maps");
  const [keyword,    setKeyword]    = useState("");
  const [location,   setLocation]   = useState("");
  const [dorkQuery,  setDorkQuery]  = useState("");
  const [maxResults, setMaxResults] = useState(20);
  const [errors,     setErrors]     = useState({});

  const keywordRef  = useRef(null);
  const locationRef = useRef(null);
  const dorkRef     = useRef(null);

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

  function switchMode(m) {
    setMode(m);
    setErrors({});
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">

      <div className="flex gap-1 p-1 bg-surface-700 rounded-lg w-fit">
        {[
          { id: "maps",  label: "Maps"  },
          { id: "dorks", label: "Dorks" },
        ].map(({ id, label }) => (
          <button
            key={id}
            type="button"
            onClick={() => switchMode(id)}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 ${
              mode === id
                ? "bg-brand-500 text-surface-900 shadow-md"
                : "text-gray-400 hover:text-gray-200"
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {mode === "maps" && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 animate-slide-up">
          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1.5">
              Keyword
            </label>
            <div className="relative">
              <input
                ref={keywordRef}
                className="input-field pr-8"
                placeholder="e.g. plumbers, dentists"
                value={keyword}
                onChange={(e) => setKeyword(e.target.value)}
                disabled={loading}
              />
              {keyword && (
                <button
                  type="button"
                  onClick={() => { setKeyword(""); keywordRef.current?.focus(); }}
                  className="absolute right-2.5 top-1/2 -translate-y-1/2
                             text-gray-600 hover:text-gray-300 transition-colors"
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
                    strokeWidth={2} className="w-3.5 h-3.5">
                    <path d="M18 6 6 18M6 6l12 12" strokeLinecap="round" />
                  </svg>
                </button>
              )}
            </div>
            {errors.keyword && (
              <p className="text-red-400 text-xs mt-1 animate-slide-down">
                {errors.keyword}
              </p>
            )}
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1.5">
              Location
            </label>
            <div className="relative">
              <input
                ref={locationRef}
                className="input-field pr-8"
                placeholder="e.g. Lahore, Pakistan"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                disabled={loading}
              />
              {location && (
                <button
                  type="button"
                  onClick={() => { setLocation(""); locationRef.current?.focus(); }}
                  className="absolute right-2.5 top-1/2 -translate-y-1/2
                             text-gray-600 hover:text-gray-300 transition-colors"
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
                    strokeWidth={2} className="w-3.5 h-3.5">
                    <path d="M18 6 6 18M6 6l12 12" strokeLinecap="round" />
                  </svg>
                </button>
              )}
            </div>
            {errors.location && (
              <p className="text-red-400 text-xs mt-1 animate-slide-down">
                {errors.location}
              </p>
            )}
          </div>
        </div>
      )}

      {mode === "dorks" && (
        <div className="animate-slide-up space-y-2">
          <div className="flex items-center justify-between mb-1.5">
            <label className="text-xs font-medium text-gray-400">
              Google Dork Query
            </label>
            <span className={`text-[10px] font-mono transition-colors ${
              dorkQuery.length > 180 ? "text-yellow-400" : "text-gray-600"
            }`}>
              {dorkQuery.length}/200
            </span>
          </div>

          <div className="relative">
            <input
              ref={dorkRef}
              className="input-field font-mono pr-8"
              placeholder='"plumbers Lahore" "contact us" email'
              value={dorkQuery}
              maxLength={200}
              onChange={(e) => setDorkQuery(e.target.value)}
              disabled={loading}
            />
            {dorkQuery && (
              <button
                type="button"
                onClick={() => { setDorkQuery(""); dorkRef.current?.focus(); }}
                className="absolute right-2.5 top-1/2 -translate-y-1/2
                           text-gray-600 hover:text-gray-300 transition-colors"
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
                  strokeWidth={2} className="w-3.5 h-3.5">
                  <path d="M18 6 6 18M6 6l12 12" strokeLinecap="round" />
                </svg>
              </button>
            )}
          </div>

          {errors.dorkQuery && (
            <p className="text-red-400 text-xs animate-slide-down">
              {errors.dorkQuery}
            </p>
          )}

          <div className="flex flex-wrap gap-1.5 pt-1">
            <span className="text-[10px] text-gray-600 self-center">Examples:</span>
            {DORK_EXAMPLES.map((ex) => (
              <button
                key={ex}
                type="button"
                onClick={() => setDorkQuery(ex)}
                disabled={loading}
                className="text-[10px] font-mono text-gray-500 hover:text-brand-400
                           bg-surface-700 hover:bg-surface-600 px-2 py-0.5 rounded
                           border border-surface-500 transition-colors disabled:opacity-40"
              >
                {ex.length > 32 ? ex.slice(0, 32) + "…" : ex}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="flex items-end gap-4 pt-1">
        <div>
          <label className="block text-xs font-medium text-gray-400 mb-1.5"
            title="More results = longer scrape time">
            Max Results
          </label>
          <select
            className="input-field w-36"
            value={maxResults}
            onChange={(e) => setMaxResults(Number(e.target.value))}
            disabled={loading}
          >
            {[10, 20, 30, 50, 100].map((n) => (
              <option key={n} value={n}>{n} results</option>
            ))}
          </select>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="btn-primary flex items-center gap-2 mb-0"
        >
          {loading ? (
            <>
              <span className="w-4 h-4 border-2 border-surface-900/30
                               border-t-surface-900 rounded-full animate-spin" />
              Starting…
            </>
          ) : (
            <>
              <svg viewBox="0 0 24 24" fill="currentColor" className="w-4 h-4">
                <polygon points="5 3 19 12 5 21 5 3" />
              </svg>
              Start Scraping
            </>
          )}
        </button>
      </div>
    </form>
  );
}