
import React, {
  createContext, useContext, useState,
  useCallback, useEffect, useRef,
} from "react";
import { createPortal } from "react-dom";


const ToastContext = createContext(null);

let _toastId = 0;

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const add = useCallback((message, type = "info", duration = 3500) => {
    const id = ++_toastId;
    setToasts((prev) => [...prev, { id, message, type, leaving: false }]);

    // Start leave animation just before removing
    setTimeout(() => {
      setToasts((prev) =>
        prev.map((t) => (t.id === id ? { ...t, leaving: true } : t))
      );
    }, duration - 300);

    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, duration);

    return id;
  }, []);

  const dismiss = useCallback((id) => {
    setToasts((prev) =>
      prev.map((t) => (t.id === id ? { ...t, leaving: true } : t))
    );
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 300);
  }, []);

  const api = {
    success: (msg, dur) => add(msg, "success", dur),
    error:   (msg, dur) => add(msg, "error",   dur ?? 5000),
    info:    (msg, dur) => add(msg, "info",    dur),
    warning: (msg, dur) => add(msg, "warning", dur),
    dismiss,
  };

  return (
    <ToastContext.Provider value={api}>
      {children}
      <ToastContainer toasts={toasts} onDismiss={dismiss} />
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used inside <ToastProvider>");
  return ctx;
}


function ToastContainer({ toasts, onDismiss }) {
  const root = typeof document !== "undefined"
    ? document.getElementById("toast-root")
    : null;

  if (!root) return null;

  return createPortal(
    <>
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} onDismiss={onDismiss} />
      ))}
    </>,
    root
  );
}


const TOAST_STYLES = {
  success: {
    bar:  "bg-brand-500",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.2}
        className="w-4 h-4 text-brand-400 shrink-0">
        <path d="M20 6 9 17l-5-5" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
  },
  error: {
    bar:  "bg-red-500",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.2}
        className="w-4 h-4 text-red-400 shrink-0">
        <circle cx="12" cy="12" r="10" />
        <path d="M12 8v4m0 4h.01" strokeLinecap="round" />
      </svg>
    ),
  },
  warning: {
    bar:  "bg-yellow-500",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.2}
        className="w-4 h-4 text-yellow-400 shrink-0">
        <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"
          strokeLinecap="round" strokeLinejoin="round" />
        <path d="M12 9v4m0 4h.01" strokeLinecap="round" />
      </svg>
    ),
  },
  info: {
    bar:  "bg-blue-500",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.2}
        className="w-4 h-4 text-blue-400 shrink-0">
        <circle cx="12" cy="12" r="10" />
        <path d="M12 16v-4m0-4h.01" strokeLinecap="round" />
      </svg>
    ),
  },
};

function ToastItem({ toast, onDismiss }) {
  const style = TOAST_STYLES[toast.type] || TOAST_STYLES.info;

  return (
    <div
      className={`
        pointer-events-auto flex items-start gap-3 w-80 max-w-full
        bg-surface-800 border border-surface-600 rounded-xl shadow-2xl
        overflow-hidden
        ${toast.leaving ? "animate-toast-out" : "animate-toast-in"}
      `}
    >
      <div className={`w-1 self-stretch rounded-l-xl ${style.bar} shrink-0`} />

      {/* Icon + message */}
      <div className="flex items-start gap-2.5 py-3 pr-2 flex-1 min-w-0">
        {style.icon}
        <p className="text-sm text-gray-200 leading-snug break-words">
          {toast.message}
        </p>
      </div>

      <button
        onClick={() => onDismiss(toast.id)}
        className="self-start mt-2.5 mr-2.5 text-gray-600 hover:text-gray-300
                   transition-colors shrink-0"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}
          className="w-3.5 h-3.5">
          <path d="M18 6 6 18M6 6l12 12" strokeLinecap="round" />
        </svg>
      </button>
    </div>
  );
}