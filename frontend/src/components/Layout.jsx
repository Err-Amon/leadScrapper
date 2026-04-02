

import React, { useState, useEffect } from "react";
import { Outlet, NavLink } from "react-router-dom";
import { healthCheck } from "../services/api";

const NAV = [
  {
    to: "/",
    end: true,
    label: "New Search",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
        strokeWidth={1.8} className="w-4 h-4">
        <circle cx="11" cy="11" r="8" />
        <path d="m21 21-4.35-4.35" strokeLinecap="round" />
      </svg>
    ),
  },
  {
    to: "/history",
    end: false,
    label: "Task History",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
        strokeWidth={1.8} className="w-4 h-4">
        <rect x="3" y="4" width="18" height="18" rx="2" />
        <path d="M16 2v4M8 2v4M3 10h18" strokeLinecap="round" />
      </svg>
    ),
  },
];

export default function Layout() {
  const [apiStatus, setApiStatus] = useState("checking");

  function checkApi() {
    healthCheck()
      .then(() => setApiStatus("online"))
      .catch(() => setApiStatus("offline"));
  }

  useEffect(() => {
    checkApi();
    const interval = setInterval(checkApi, 30_000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex min-h-screen">

      <aside className="w-56 shrink-0 bg-surface-800 border-r border-surface-600
                        flex flex-col relative overflow-hidden">

        <div className="absolute -top-10 -left-10 w-40 h-40 rounded-full
                        bg-brand-500/5 blur-3xl pointer-events-none" />

        <div className="px-5 py-5 border-b border-surface-600 relative">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-brand-500 flex items-center
                            justify-center shadow-lg shadow-brand-900/40">
              <svg viewBox="0 0 24 24" fill="currentColor"
                className="w-4 h-4 text-surface-900">
                <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75
                         7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38
                         0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5
                         2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z" />
              </svg>
            </div>
            <div>
              <p className="font-display font-semibold text-sm text-gray-100 leading-none">
                LeadGen
              </p>
              <p className="text-[10px] text-brand-600 mt-0.5 font-mono">
                v1.0 · Production
              </p>
            </div>
          </div>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-0.5">
          {NAV.map(({ to, end, label, icon }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                `flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-sm
                 font-medium transition-all duration-150 group ${
                  isActive
                    ? "bg-brand-500/12 text-brand-400 border border-brand-500/20"
                    : "text-gray-500 hover:text-gray-200 hover:bg-surface-700"
                }`
              }
            >
              {icon}
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="px-4 py-4 border-t border-surface-600 space-y-2">
          <button
            onClick={checkApi}
            className="flex items-center gap-2 group w-full"
            title="Click to re-check API"
          >
            <span className={`w-1.5 h-1.5 rounded-full transition-colors ${
              apiStatus === "online"   ? "bg-brand-400" :
              apiStatus === "offline"  ? "bg-red-400 animate-pulse" :
                                         "bg-yellow-400 animate-pulse"
            }`} />
            <span className="text-[11px] font-mono text-gray-600
                             group-hover:text-gray-400 transition-colors">
              {apiStatus === "online"  ? "API connected" :
               apiStatus === "offline" ? "API offline"   : "Checking…"}
            </span>
          </button>
          <p className="text-[10px] text-gray-700 font-mono pl-3.5">
            localhost:8000
          </p>
        </div>
      </aside>

      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}