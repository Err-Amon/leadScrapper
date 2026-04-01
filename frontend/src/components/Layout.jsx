import React, { useState, useEffect } from "react";
import { Outlet, NavLink, useLocation } from "react-router-dom";
import { healthCheck } from "../services/api";

const NAV = [
  {
    to: "/",
    label: "New Search",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} className="w-5 h-5">
        <circle cx="11" cy="11" r="8" />
        <path d="m21 21-4.35-4.35" strokeLinecap="round" />
      </svg>
    ),
  },
  {
    to: "/history",
    label: "Task History",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} className="w-5 h-5">
        <rect x="3" y="4" width="18" height="18" rx="2" />
        <path d="M16 2v4M8 2v4M3 10h18" strokeLinecap="round" />
      </svg>
    ),
  },
];

export default function Layout() {
  const location = useLocation();
  const [apiStatus, setApiStatus] = useState("checking");

  useEffect(() => {
    healthCheck()
      .then(() => setApiStatus("online"))
      .catch(() => setApiStatus("offline"));
  }, []);

  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <aside className="w-60 shrink-0 bg-surface-800 border-r border-surface-600 flex flex-col">
        {/* Logo */}
        <div className="px-6 py-5 border-b border-surface-600">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-brand-500 flex items-center justify-center">
              <svg viewBox="0 0 24 24" fill="currentColor" className="w-4 h-4 text-surface-900">
                <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z" />
              </svg>
            </div>
            <div>
              <p className="font-display font-700 text-sm text-gray-100 leading-none">LeadGen</p>
              <p className="text-[10px] text-gray-500 mt-0.5 font-mono">v1.0 · Phase 1</p>
            </div>
          </div>
        </div>

        {/* Nav links */}
        <nav className="flex-1 px-3 py-4 space-y-1">
          {NAV.map(({ to, label, icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 ${
                  isActive
                    ? "bg-brand-500/15 text-brand-400 border border-brand-500/20"
                    : "text-gray-400 hover:text-gray-200 hover:bg-surface-700"
                }`
              }
            >
              {icon}
              {label}
            </NavLink>
          ))}
        </nav>

        {/* API status indicator */}
        <div className="px-4 py-4 border-t border-surface-600">
          <div className="flex items-center gap-2">
            <span
              className={`w-2 h-2 rounded-full ${
                apiStatus === "online"
                  ? "bg-brand-400"
                  : apiStatus === "offline"
                  ? "bg-red-400"
                  : "bg-yellow-400 animate-pulse"
              }`}
            />
            <span className="text-xs font-mono text-gray-500">
              API{" "}
              {apiStatus === "online"
                ? "connected"
                : apiStatus === "offline"
                ? "offline"
                : "checking…"}
            </span>
          </div>
          <p className="text-[10px] text-gray-600 mt-1 font-mono">localhost:8000</p>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}
