const API_BASE = "http://localhost:8000";
const SCAN_DEBOUNCE_MS = 800;

/** @type {Map<number, ReturnType<typeof setTimeout>>} */
const pendingScans = new Map();

chrome.runtime.onInstalled.addListener(() => {
  console.info("[Cybersec Shield] Extension installed.");
});

/**
 * @param {string | undefined} url
 */
function isScannableUrl(url) {
  if (!url) return false;
  return url.startsWith("http://") || url.startsWith("https://");
}

function extractPrediction(data) {
  const prediction = data?.result?.prediction ?? {};
  return {
    is_scam: Boolean(prediction.is_scam),
    confidence: typeof prediction.confidence === "number" ? prediction.confidence : null,
    label: prediction.label ?? "unknown",
    status: data.status ?? "unknown",
    cache_hit: Boolean(data.cache_hit),
    scanned_at: data.scanned_at ?? null,
    message: data.message ?? null,
  };
}

/**
 * @param {number} tabId
 * @param {string} url
 */
async function scanTabUrl(tabId, url) {
  try {
    const response = await fetch(`${API_BASE}/scan/website`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });

    if (!response.ok) {
      throw new Error(`Scan failed (${response.status})`);
    }

    const data = await response.json();
    const summary = {
      url: data.url ?? url,
      ...extractPrediction(data),
    };

    await chrome.storage.local.set({ [`scan:${tabId}`]: summary });

    try {
      await chrome.tabs.sendMessage(tabId, {
        type: "SCAN_RESULT",
        payload: summary,
      });
    } catch {
      // Content script may not be ready on restricted pages.
    }
  } catch (error) {
    const failure = {
      url,
      is_scam: false,
      confidence: null,
      label: "error",
      status: "error",
      cache_hit: false,
      scanned_at: null,
      message: error instanceof Error ? error.message : "Scan request failed",
    };
    await chrome.storage.local.set({ [`scan:${tabId}`]: failure });
  }
}

/**
 * @param {number} tabId
 * @param {chrome.tabs.TabChangeInfo} changeInfo
 * @param {chrome.tabs.Tab} tab
 */
function handleTabUpdate(tabId, changeInfo, tab) {
  if (changeInfo.status !== "complete") return;
  if (!tab.url || !isScannableUrl(tab.url)) return;

  const existing = pendingScans.get(tabId);
  if (existing) clearTimeout(existing);

  pendingScans.set(
    tabId,
    setTimeout(() => {
      pendingScans.delete(tabId);
      scanTabUrl(tabId, tab.url);
    }, SCAN_DEBOUNCE_MS),
  );
}

chrome.tabs.onUpdated.addListener(handleTabUpdate);

chrome.tabs.onRemoved.addListener((tabId) => {
  pendingScans.delete(tabId);
  chrome.storage.local.remove(`scan:${tabId}`);
});

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message?.type !== "GET_TAB_SCAN" || !sender.tab?.id) return;

  const key = `scan:${sender.tab.id}`;
  chrome.storage.local.get(key, (stored) => {
    sendResponse({ payload: stored[key] ?? null });
  });
  return true;
});
