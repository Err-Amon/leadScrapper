
import React, { useState, useMemo } from "react";
import {
  formatPhone, formatWebsite, formatRating,
  truncate, formatSocialLinks, socialIcon,
} from "../utils/formatters";

const SOURCE_OPTIONS = [
  { value: "",       label: "All"   },
  { value: "maps",   label: "Maps"  },
  { value: "dorks",  label: "Dorks" },
];

export default function ResultsTable({
  leads,
  pagination,
  filters,
  onFiltersChange,
  onPageChange,
}) {
  const [sortKey,  setSortKey]  = useState("");
  const [sortAsc,  setSortAsc]  = useState(true);
  const [selected, setSelected] = useState(new Set());

  const sorted = useMemo(() => {
    if (!sortKey) return leads;
    return [...leads].sort((a, b) => {
      const av = a[sortKey] ?? "";
      const bv = b[sortKey] ?? "";
      return sortAsc
        ? String(av).localeCompare(String(bv))
        : String(bv).localeCompare(String(av));
    });
  }, [leads, sortKey, sortAsc]);

  function toggleSort(key) {
    if (sortKey === key) setSortAsc((v) => !v);
    else { setSortKey(key); setSortAsc(true); }
  }

  const allSelected = sorted.length > 0 && sorted.every((l) => selected.has(l.id));

  function toggleAll() {
    if (allSelected) setSelected(new Set());
    else setSelected(new Set(sorted.map((l) => l.id)));
  }

  function toggleRow(id) {
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }

  function patch(partial) {
    onFiltersChange({ ...filters, ...partial });
  }

  if (leads.length === 0) {
    return (
      <div className="space-y-4">
        <FilterBar filters={filters} patch={patch} />
        <div className="text-center py-14 text-gray-600">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.2}
            className="w-10 h-10 mx-auto mb-3 text-surface-600">
            <path d="M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2"
              strokeLinecap="round" />
            <rect x="9" y="3" width="6" height="4" rx="1" />
          </svg>
          <p className="text-sm">No leads match the current filters.</p>
          <p className="text-xs mt-1 text-gray-700">
            Results appear here as scraping progresses.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-3">

  
      <FilterBar filters={filters} patch={patch} total={pagination.total} />

      {/* Selection status bar */}
      {selected.size > 0 && (
        <div className="flex items-center gap-3 px-3 py-2 bg-brand-900/20
                        border border-brand-700/30 rounded-lg text-xs text-brand-400">
          <span className="font-medium">{selected.size} row{selected.size > 1 ? "s" : ""} selected</span>
          <button
            onClick={() => setSelected(new Set())}
            className="text-gray-500 hover:text-gray-300 transition-colors"
          >
            Clear
          </button>
        </div>
      )}

   
      <div className="overflow-x-auto rounded-xl border border-surface-600">
        <table className="w-full text-xs">
          <thead>
            <tr className="bg-surface-700 border-b border-surface-600">

          
              <th className="px-3 py-3 w-8">
                <input
                  type="checkbox"
                  checked={allSelected}
                  onChange={toggleAll}
                  className="accent-brand-500 cursor-pointer"
                />
              </th>

             
              {[
                { key: "name",    label: "Business Name" },
                { key: "phone",   label: "Phone"         },
                { key: "email",   label: "Email"         },
                { key: "website", label: "Website"       },
                { key: "address", label: "Address"       },
                { key: "rating",  label: "Rating"        },
                { key: "source",  label: "Source"        },
                { key: "social_links", label: "Socials"  },
              ].map(({ key, label }) => (
                <th
                  key={key}
                  onClick={() => toggleSort(key)}
                  className="text-left px-4 py-3 text-gray-400 font-medium
                             whitespace-nowrap cursor-pointer select-none
                             hover:text-gray-200 transition-colors"
                >
                  <span className="flex items-center gap-1">
                    {label}
                    {sortKey === key && (
                      <span className="text-brand-400">{sortAsc ? "↑" : "↓"}</span>
                    )}
                  </span>
                </th>
              ))}
            </tr>
          </thead>

          <tbody className="divide-y divide-surface-700">
            {sorted.map((lead, i) => {
              const socials = formatSocialLinks(lead.social_links);
              const isSelected = selected.has(lead.id);

              return (
                <tr
                  key={lead.id || i}
                  onClick={() => toggleRow(lead.id)}
                  className={`cursor-pointer transition-colors animate-fade-in
                    ${isSelected
                      ? "bg-brand-900/20"
                      : "hover:bg-surface-700/50"}`}
                >
                  
                  <td className="px-3 py-3" onClick={(e) => e.stopPropagation()}>
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => toggleRow(lead.id)}
                      className="accent-brand-500 cursor-pointer"
                    />
                  </td>

                  
                  <td className="px-4 py-3 font-medium text-gray-200 whitespace-nowrap">
                    <div className="flex items-center gap-1.5">
                      {lead.enriched === 1 && (
                        <span title="Enriched" className="text-brand-500 text-xs font-mono shrink-0">ENR</span>
                      )}
                      {truncate(lead.name, 26) || "—"}
                    </div>
                  </td>

                  
                  <td className="px-4 py-3 font-mono text-gray-300 whitespace-nowrap">
                    {lead.phone
                      ? <a href={`tel:${lead.phone}`} className="hover:text-gray-100"
                           onClick={(e) => e.stopPropagation()}>
                          {formatPhone(lead.phone)}
                        </a>
                      : "—"}
                  </td>

                  
                  <td className="px-4 py-3 text-brand-400 whitespace-nowrap">
                    {lead.email
                      ? <a href={`mailto:${lead.email}`} className="hover:underline"
                           onClick={(e) => e.stopPropagation()}>
                          {truncate(lead.email, 24)}
                        </a>
                      : "—"}
                  </td>

                  
                  <td className="px-4 py-3 text-blue-400 whitespace-nowrap">
                    {lead.website
                      ? <a href={lead.website} target="_blank" rel="noopener noreferrer"
                           className="hover:underline"
                           onClick={(e) => e.stopPropagation()}>
                          {formatWebsite(lead.website)}
                        </a>
                      : "—"}
                  </td>

                  
                  <td className="px-4 py-3 text-gray-400 max-w-[140px]">
                    <span title={lead.address}>{truncate(lead.address, 22)}</span>
                  </td>

                  
                  <td className="px-4 py-3 font-mono text-yellow-400 whitespace-nowrap">
                    {formatRating(lead.rating)}
                  </td>

                  
                  <td className="px-4 py-3">
                    <span className={`tag ${lead.source === "maps" ? "tag-maps" : "tag-dorks"}`}>
                      {lead.source}
                    </span>
                  </td>

                  
                  <td className="px-4 py-3 whitespace-nowrap">
                    {socials.length > 0
                      ? (
                        <div className="flex items-center gap-1">
                          {socials.slice(0, 4).map((url, si) => (
                            <a
                              key={si}
                              href={url}
                              target="_blank"
                              rel="noopener noreferrer"
                              title={url}
                              onClick={(e) => e.stopPropagation()}
                              className="text-[10px] font-mono px-1.5 py-0.5 rounded
                                         bg-surface-600 text-gray-300 hover:text-white
                                         hover:bg-surface-500 transition-colors"
                            >
                              {socialIcon(url)}
                            </a>
                          ))}
                        </div>
                      )
                      : <span className="text-gray-700">—</span>
                    }
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      
      {pagination.totalPages > 1 && (
        <div className="flex items-center justify-between pt-1">
          <p className="text-xs text-gray-500 font-mono">
            Page {pagination.page} of {pagination.totalPages}
            {" · "}{pagination.total} leads
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



function FilterBar({ filters, patch, total }) {
  return (
    <div className="flex flex-wrap items-center gap-3">

      
      <div className="relative">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8}
          className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2
                     text-gray-500 pointer-events-none">
          <circle cx="11" cy="11" r="8" />
          <path d="m21 21-4.35-4.35" strokeLinecap="round" />
        </svg>
        <input
          className="input-field pl-8 py-1.5 text-xs w-48"
          placeholder="Search name, email, phone…"
          value={filters.search}
          onChange={(e) => patch({ search: e.target.value })}
        />
      </div>

      
      <div className="flex gap-1 p-0.5 bg-surface-700 rounded-lg">
        {SOURCE_OPTIONS.map(({ value, label }) => (
          <button
            key={value}
            onClick={() => patch({ source: value })}
            className={`px-3 py-1 rounded-md text-xs font-medium transition-all duration-150
              ${filters.source === value
                ? "bg-surface-500 text-gray-100"
                : "text-gray-500 hover:text-gray-300"}`}
          >
            {label}
          </button>
        ))}
      </div>

      
      <div className="flex items-center gap-3">
        <label className="flex items-center gap-1.5 cursor-pointer text-xs text-gray-400
                          hover:text-gray-200 transition-colors select-none">
          <input
            type="checkbox"
            checked={filters.hasEmail}
            onChange={(e) => patch({ hasEmail: e.target.checked })}
            className="accent-brand-500"
          />
          Has Email
        </label>
        <label className="flex items-center gap-1.5 cursor-pointer text-xs text-gray-400
                          hover:text-gray-200 transition-colors select-none">
          <input
            type="checkbox"
            checked={filters.hasPhone}
            onChange={(e) => patch({ hasPhone: e.target.checked })}
            className="accent-brand-500"
          />
          Has Phone
        </label>
      </div>

     
      {total !== undefined && (
        <span className="ml-auto text-xs text-gray-500 font-mono">
          {total} lead{total !== 1 ? "s" : ""}
        </span>
      )}
    </div>
  );
}