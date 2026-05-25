const API_BASE = "http://localhost:8000";

const els = {
  tabUrl: document.getElementById("tab-url"),
  statusBadge: document.getElementById("status-badge"),
  statusCard: document.getElementById("status-card"),
  verdict: document.getElementById("verdict"),
  confidence: document.getElementById("confidence"),
  statusMessage: document.getElementById("status-message"),
  rescanBtn: document.getElementById("rescan-btn"),
};

function renderScan(scan) {
  if (!scan) {
    setUi("unknown", "No scan data yet", "—", "—", "Visit a website to trigger a scan.");
    return;
  }

  if (scan.status === "error") {
    setUi(
      "error",
      "Scan error",
      "Unavailable",
      "—",
      scan.message ?? "Could not reach the backend. Start Docker / FastAPI on port 8000.",
    );
    return;
  }

  if (scan.is_scam) {
    setUi(
      "danger",
      "Threat detected",
      scan.label ?? "scam",
      formatConfidence(scan.confidence),
      "This site was flagged. Avoid entering credentials or downloading files.",
    );
    return;
  }

  setUi(
    "safe",
    "Looks safe",
    scan.label ?? "legitimate",
    formatConfidence(scan.confidence),
    scan.cache_hit
      ? "Result served from cache (24h)."
      : "No threats detected for this URL.",
  );
}

/**
 * @param {"safe"|"danger"|"error"|"unknown"} state
 */
function setUi(state, badge, verdict, confidence, message) {
  const styles = {
    safe: {
      badge: "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30",
      ring: "border-emerald-500/20",
    },
    danger: {
      badge: "bg-rose-500/20 text-rose-300 border border-rose-500/30",
      ring: "border-rose-500/30 shadow-[0_0_30px_rgba(244,63,94,0.15)]",
    },
    error: {
      badge: "bg-amber-500/20 text-amber-300 border border-amber-500/30",
      ring: "border-amber-500/20",
    },
    unknown: {
      badge: "bg-slate-800 text-slate-300",
      ring: "border-white/10",
    },
  };

  const style = styles[state] ?? styles.unknown;
  els.statusBadge.textContent = badge;
  els.statusBadge.className = `shrink-0 rounded-full px-3 py-1 text-xs font-semibold ${style.badge}`;
  els.statusCard.className = `relative rounded-2xl border bg-white/5 p-4 ${style.ring}`;
  els.verdict.textContent = verdict;
  els.confidence.textContent = confidence;
  els.statusMessage.textContent = message;
}

/** @param {number | null} value */
function formatConfidence(value) {
  if (value === null || value === undefined) return "—";
  return `${Math.round(value * 100)}%`;
}

/**
 * @param {number} tabId
 */
async function loadTabScan(tabId) {
  const key = `scan:${tabId}`;
  const stored = await chrome.storage.local.get(key);
  return stored[key] ?? null;
}

async function refresh() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.id || !tab.url?.startsWith("http")) {
    els.tabUrl.textContent = tab?.url ?? "No active web page";
    renderScan(null);
    return;
  }

  els.tabUrl.textContent = tab.url;
  const scan = await loadTabScan(tab.id);
  renderScan(scan);
}

async function rescanActiveTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.id || !tab.url?.startsWith("http")) return;

  els.statusMessage.textContent = "Rescanning…";
  els.rescanBtn.disabled = true;

  try {
    const response = await fetch(`${API_BASE}/scan/website`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: tab.url }),
    });
    const data = await response.json();
    const summary = {
      url: data.url ?? tab.url,
      is_scam: Boolean(data?.result?.prediction?.is_scam),
      confidence: data?.result?.prediction?.confidence ?? null,
      label: data?.result?.prediction?.label ?? "unknown",
      status: data.status,
      cache_hit: Boolean(data.cache_hit),
      scanned_at: data.scanned_at,
      message: data.message,
    };
    await chrome.storage.local.set({ [`scan:${tab.id}`]: summary });
    await chrome.tabs.sendMessage(tab.id, { type: "SCAN_RESULT", payload: summary });
    renderScan(summary);
  } catch (error) {
    renderScan({
      url: tab.url,
      is_scam: false,
      confidence: null,
      label: "error",
      status: "error",
      cache_hit: false,
      scanned_at: null,
      message: error instanceof Error ? error.message : "Rescan failed",
    });
  } finally {
    els.rescanBtn.disabled = false;
  }
}

els.rescanBtn.addEventListener("click", rescanActiveTab);
chrome.storage.onChanged.addListener(() => refresh());
refresh();
