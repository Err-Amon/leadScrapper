
import React, { useEffect, useRef, useState } from "react";

export default function LogsPanel({ logs = [] }) {
  const bottomRef    = useRef(null);
  const containerRef = useRef(null);
  const [expanded,   setExpanded]   = useState(true);
  const [autoScroll, setAutoScroll] = useState(true);
  const [copied,     setCopied]     = useState(false);

  // Auto-scroll to bottom when new lines arrive
  useEffect(() => {
    if (expanded && autoScroll && bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [logs, expanded, autoScroll]);

  function handleScroll() {
    if (!containerRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = containerRef.current;
    const atBottom = scrollHeight - scrollTop - clientHeight < 30;
    setAutoScroll(atBottom);
  }

  async function copyLogs() {
    try {
      await navigator.clipboard.writeText(logs.join("\n"));
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Clipboard unavailable — silently ignore
    }
  }

  function lineClass(line) {
    const l = line.toLowerCase();
    if (l.includes("error") || l.includes("failed") || l.includes("captcha"))
      return "text-red-400";
    if (l.includes("warning") || l.includes("blocked") || l.includes("timeout"))
      return "text-yellow-400";
    if (l.includes("saved") || l.includes("completed") || l.includes("success"))
      return "text-brand-400";
    if (l.includes("skipping") || l.includes("duplicate"))
      return "text-gray-600";
    return "text-gray-400";
  }

  return (
    <div className="border border-surface-600 rounded-xl overflow-hidden
                    transition-all duration-200">

      <div className="flex items-center justify-between px-4 py-3
                      bg-surface-700 border-b border-surface-600">
        <button
          onClick={() => setExpanded((v) => !v)}
          className="flex items-center gap-2 text-left group"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
            strokeWidth={1.8} className="w-3.5 h-3.5 text-gray-500">
            <rect x="3" y="3" width="18" height="18" rx="2" />
            <path d="M7 8h10M7 12h10M7 16h6" strokeLinecap="round" />
          </svg>
          <span className="text-xs font-medium text-gray-400
                           group-hover:text-gray-300 transition-colors">
            Task Logs
          </span>
          {logs.length > 0 && (
            <span className="text-[10px] font-mono bg-surface-600 text-gray-500
                             px-1.5 py-0.5 rounded">
              {logs.length}
            </span>
          )}
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
            strokeWidth={2}
            className={`w-3.5 h-3.5 text-gray-600 transition-transform duration-200
              ${expanded ? "rotate-180" : ""}`}>
            <path d="m6 9 6 6 6-6" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>

        {expanded && logs.length > 0 && (
          <div className="flex items-center gap-2">
            <button
              onClick={() => setAutoScroll((v) => !v)}
              title={autoScroll ? "Lock scroll position" : "Resume auto-scroll"}
              className={`text-[10px] font-mono px-2 py-0.5 rounded transition-colors ${
                autoScroll
                  ? "bg-brand-900/40 text-brand-500 border border-brand-800/40"
                  : "text-gray-600 hover:text-gray-400"
              }`}
            >
              {autoScroll ? "↓ auto" : "locked"}
            </button>

            <button
              onClick={copyLogs}
              title="Copy all logs"
              className="text-gray-600 hover:text-gray-300 transition-colors"
            >
              {copied ? (
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
                  strokeWidth={2} className="w-3.5 h-3.5 text-brand-400">
                  <path d="M20 6 9 17l-5-5" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              ) : (
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
                  strokeWidth={1.8} className="w-3.5 h-3.5">
                  <rect x="9" y="9" width="13" height="13" rx="2" />
                  <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"
                    strokeLinecap="round" />
                </svg>
              )}
            </button>
          </div>
        )}
      </div>

      {expanded && (
        <div
          ref={containerRef}
          onScroll={handleScroll}
          className="max-h-52 overflow-y-auto bg-surface-900 p-3
                     font-mono text-[11px] leading-relaxed"
        >
          {logs.length === 0 ? (
            <p className="text-gray-700 italic">No logs yet…</p>
          ) : (
            logs.map((line, i) => (
              <div key={i} className={lineClass(line)}>
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