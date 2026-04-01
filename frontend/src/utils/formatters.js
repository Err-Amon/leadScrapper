
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
    const parsed = new URL(url.startsWith("http") ? url : `https://${url}`);
    return parsed.hostname.replace(/^www\./, "");
  } catch {
    return url;
  }
}

export function formatRating(rating) {
  if (rating === null || rating === undefined || rating === "") return "—";
  return `${parseFloat(rating).toFixed(1)} ★`;
}

export function formatDate(isoString) {
  if (!isoString) return "—";
  return new Date(isoString).toLocaleString("en-US", {
    month:  "short",
    day:    "numeric",
    hour:   "2-digit",
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


export function formatSocialLinks(raw) {
  if (!raw || typeof raw !== "string") return [];
  return raw
    .split("|")
    .map((s) => s.trim())
    .filter(Boolean);
}


export function socialIcon(url) {
  if (!url) return "🔗";
  const lower = url.toLowerCase();
  if (lower.includes("facebook.com"))  return "FB";
  if (lower.includes("twitter.com") || lower.includes("x.com")) return "𝕏";
  if (lower.includes("instagram.com")) return "IG";
  if (lower.includes("linkedin.com"))  return "IN";
  if (lower.includes("youtube.com"))   return "YT";
  if (lower.includes("tiktok.com"))    return "TK";
  return "🔗";
}

export function formatEnrichStatus(status) {
  switch (status) {
    case "running":
      return { label: "Enriching…", colorClass: "text-yellow-400" };
    case "completed":
      return { label: "Enriched",   colorClass: "text-brand-400" };
    case "failed":
      return { label: "Enrich failed", colorClass: "text-red-400" };
    default:
      return { label: "Not enriched",  colorClass: "text-gray-600" };
  }
}