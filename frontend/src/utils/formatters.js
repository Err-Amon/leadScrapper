
export function formatPhone(phone) {
  if (!phone) return "—";
  return phone;
}

export function formatEmail(email) {
  if (!email) return "—";
  return email;
}

export function formatWebsite(url) {
  if (!url) return "—";
  try {
    const parsed = new URL(url);
    return parsed.hostname.replace(/^www\./, "");
  } catch {
    return url;
  }
}

export function formatRating(rating) {
  if (rating === null || rating === undefined) return "—";
  return `${parseFloat(rating).toFixed(1)} ★`;
}

export function formatDate(isoString) {
  if (!isoString) return "—";
  return new Date(isoString).toLocaleString("en-US", {
    month: "short",
    day:   "numeric",
    hour:  "2-digit",
    minute: "2-digit",
  });
}

export function formatProgress(progress, total) {
  if (!total || total === 0) return 0;
  return Math.min(100, Math.round((progress / total) * 100));
}

export function truncate(str, max = 30) {
  if (!str) return "—";
  return str.length > max ? str.slice(0, max) + "…" : str;
}
