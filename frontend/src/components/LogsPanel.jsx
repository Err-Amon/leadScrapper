import React, { useEffect, useRef, useState } from "react";

export default function LogsPanel({ logs = [] }) {
  const bottomRef = useRef(null);
  const [expanded, setExpanded] = useState(true);

  useEffect(() => {
    if (expanded && bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [logs, expanded]);

  return (
    <div className="border border-surface-600 rounded-xl overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setExpanded((v) => !v)}
        className="w-full flex items-center justify-between px-4 py-3 bg-surface-700 hover:bg-surface-600 transition-colors text-left"
      >
        <div className="flex items-center gap-2">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} className="w-4 h-4 text-gray-400">
            <rect x="3" y="3" width="18" height="18" rx="2" />
            <path d="M7 8h10M7 12h10M7 16h6" strokeLinecap="round" />
          </svg>
          <span className="text-xs font-medium text-gray-400">Task Logs</span>
          <span className="text-[10px] font-mono bg-surface-600 text-gray-500 px-1.5 py-0.5 rounded">
            {logs.length} lines
          </span>
        </div>
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth={2}
          className={`w-4 h-4 text-gray-500 transition-transform ${expanded ? "rotate-180" : ""}`}
        >
          <path d="m6 9 6 6 6-6" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </button>

      {/* Log lines */}
      {expanded && (
        <div className="max-h-48 overflow-y-auto bg-surface-900 p-3 font-mono text-[11px] leading-relaxed">
          {logs.length === 0 ? (
            <p className="text-gray-600 italic">No logs yet…</p>
          ) : (
            logs.map((line, i) => (
              <div
                key={i}
                className={`${
                  line.includes("ERROR") || line.includes("failed")
                    ? "text-red-400"
                    : line.includes("WARNING")
                    ? "text-yellow-400"
                    : line.includes("completed") || line.includes("success")
                    ? "text-brand-400"
                    : "text-gray-400"
                }`}
              >
                {line}
              </div>
            ))
          )}
          <div ref={bottomRef} />
        </div>
      )}
    </div>
  );
}
