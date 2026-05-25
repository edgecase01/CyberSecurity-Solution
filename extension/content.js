const BANNER_ID = "cybersec-shield-warning-banner";

/**
 * @param {{ is_scam: boolean; confidence: number | null; label: string }} payload
 */
function showWarningBanner(payload) {
  removeWarningBanner();

  const banner = document.createElement("div");
  banner.id = BANNER_ID;
  banner.setAttribute("role", "alert");
  banner.setAttribute("aria-live", "assertive");

  const confidence =
    payload.confidence !== null ? `${Math.round(payload.confidence * 100)}% confidence` : "";

  banner.innerHTML = `
    <div class="cybersec-banner__inner">
      <div class="cybersec-banner__icon" aria-hidden="true">⚠</div>
      <div class="cybersec-banner__text">
        <strong>Threat detected — Cybersec Shield</strong>
        <span>This site was flagged as a potential scam (${payload.label}${confidence ? ` · ${confidence}` : ""}). Leave immediately and do not enter credentials.</span>
      </div>
      <button type="button" class="cybersec-banner__dismiss" aria-label="Dismiss warning">✕</button>
    </div>
  `;

  banner.querySelector(".cybersec-banner__dismiss")?.addEventListener("click", () => {
    banner.remove();
  });

  document.documentElement.prepend(banner);
  document.documentElement.style.setProperty("scroll-padding-top", "72px", "important");
}

function removeWarningBanner() {
  document.getElementById(BANNER_ID)?.remove();
}

/**
 * @param {{ is_scam: boolean; confidence?: number | null; label?: string } | null | undefined} payload
 */
function applyScanResult(payload) {
  if (payload?.is_scam) {
    showWarningBanner(payload);
  } else {
    removeWarningBanner();
  }
}

chrome.runtime.onMessage.addListener((message) => {
  if (message?.type === "SCAN_RESULT") {
    applyScanResult(message.payload);
  }
});

chrome.runtime.sendMessage({ type: "GET_TAB_SCAN" }, (response) => {
  if (chrome.runtime.lastError) return;
  applyScanResult(response?.payload);
});
