import React, { useState } from "react";
import {
  formatPhone, formatEmail, formatWebsite,
  formatRating, truncate,
} from "../utils/formatters";

const COLUMNS = [
  { key: "name",    label: "Business Name" },
  { key: "phone",   label: "Phone" },
  { key: "email",   label: "Email" },
  { key: "website", label: "Website" },
  { key: "address", label: "Address" },
  { key: "rating",  label: "Rating" },
  { key: "source",  label: "Source" },
];

export default function ResultsTable({ leads, pagination, onPageChange }) {
  const [filter, setFilter] = useState("");

  const filtered = filter.trim()
    ? leads.filter((l) =>
        Object.values(l).some((v) =>
          String(v).toLowerCase().includes(filter.toLowerCase())
        )
      )
    : leads;

  if (leads.length === 0) {
    return (
      <div className="text-center py-16 text-gray-600">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.2} className="w-12 h-12 mx-auto mb-3 text-surface-600">
          <path d="M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2" strokeLinecap="round" />
          <rect x="9" y="3" width="6" height="4" rx="1" />
        </svg>
        <p className="text-sm">No leads collected yet.</p>
        <p className="text-xs mt-1 text-gray-700">Results will appear here as scraping progresses.</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Filter bar */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-xs">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8}
            className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 pointer-events-none">
            <circle cx="11" cy="11" r="8" /><path d="m21 21-4.35-4.35" strokeLinecap="round" />
          </svg>
          <input
            className="input-field pl-9 py-2 text-xs"
            placeholder="Filter results…"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
          />
        </div>
        <span className="text-xs text-gray-500 font-mono">
          {pagination.total} total leads
        </span>
      </div>

      {/* Table */}
      <div className="overflow-x-auto rounded-xl border border-surface-600">
        <table className="w-full text-xs">
          <thead>
            <tr className="bg-surface-700 border-b border-surface-600">
              {COLUMNS.map((col) => (
                <th
                  key={col.key}
                  className="text-left px-4 py-3 text-gray-400 font-medium whitespace-nowrap"
                >
                  {col.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-surface-700">
            {filtered.map((lead, i) => (
              <tr
                key={lead.id || i}
                className="hover:bg-surface-700/50 transition-colors animate-fade-in"
              >
                <td className="px-4 py-3 font-medium text-gray-200 whitespace-nowrap">
                  {truncate(lead.name, 28) || "—"}
                </td>
                <td className="px-4 py-3 font-mono text-gray-300 whitespace-nowrap">
                  {formatPhone(lead.phone)}
                </td>
                <td className="px-4 py-3 text-brand-400 whitespace-nowrap">
                  {lead.email ? (
                    <a href={`mailto:${lead.email}`} className="hover:underline">
                      {truncate(lead.email, 26)}
                    </a>
                  ) : "—"}
                </td>
                <td className="px-4 py-3 text-blue-400 whitespace-nowrap">
                  {lead.website ? (
                    <a href={lead.website} target="_blank" rel="noopener noreferrer" className="hover:underline">
                      {formatWebsite(lead.website)}
                    </a>
                  ) : "—"}
                </td>
                <td className="px-4 py-3 text-gray-400 max-w-[160px]">
                  <span title={lead.address}>{truncate(lead.address, 24)}</span>
                </td>
                <td className="px-4 py-3 font-mono text-yellow-400 whitespace-nowrap">
                  {formatRating(lead.rating)}
                </td>
                <td className="px-4 py-3">
                  <span className={`tag ${lead.source === "maps" ? "tag-maps" : "tag-dorks"}`}>
                    {lead.source}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {pagination.totalPages > 1 && (
        <div className="flex items-center justify-between pt-1">
          <p className="text-xs text-gray-500 font-mono">
            Page {pagination.page} of {pagination.totalPages}
          </p>
          <div className="flex gap-2">
            <button
              className="btn-secondary py-1.5 px-3 text-xs"
              disabled={pagination.page <= 1}
              onClick={() => onPageChange(pagination.page - 1)}
            >
              ← Prev
            </button>
            <button
              className="btn-secondary py-1.5 px-3 text-xs"
              disabled={pagination.page >= pagination.totalPages}
              onClick={() => onPageChange(pagination.page + 1)}
            >
              Next →
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
