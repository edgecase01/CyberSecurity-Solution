import { useEffect, useState } from "react";
import { enqueueEmailScan } from "../lib/auth";
import { useAuth } from "../context/AuthContext";
import ChatBot from "./ChatBot";
import PasswordAnalyzer from "./PasswordAnalyzer";
import StatCard from "./StatCard";

export default function Dashboard() {
  const { token, setToken } = useAuth();
  const [scanStatus, setScanStatus] = useState<string | null>(null);
  const [totalScanned, setTotalScanned] = useState<string | null>(null);
  const [threatsBlocked, setThreatsBlocked] = useState<string | null>(null);
  const [recentScans, setRecentScans] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const fetchStats = async () => {
      if (!token) {
        setLoading(false);
        return;
      }
      try {
        setLoading(true);
        const response = await fetch("http://localhost:8000/api/stats", {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        const data = await response.json();
        setTotalScanned(data.total_scanned);
        setThreatsBlocked(data.threats_blocked);
        setRecentScans(data.recent_scans);
      } catch (error) {
        console.error("Failed to fetch stats:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, [token]);

  async function handleScanInbox() {
    setScanStatus("Scanning inbox…");
    try {
      const result = await enqueueEmailScan();
      setScanStatus(`Scan queued (task ${result.task_id.slice(0, 8)}…)`);
    } catch {
      setScanStatus("Failed to queue inbox scan. Are you signed in?");
    }
  }

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(34,211,238,0.08),_transparent_35%),#020617]">
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <header className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-sm font-medium uppercase tracking-[0.2em] text-cyber-400">
              Cybersec Shield
            </p>
            <h1 className="mt-2 text-3xl font-bold tracking-tight text-white sm:text-4xl">
              Security Dashboard
            </h1>
            <p className="mt-2 max-w-2xl text-slate-400">
              Monitor email protection, analyze passwords locally, and chat with your AI security
              assistant.
            </p>
          </div>
          <div className="flex flex-col items-end gap-2 self-start">
            <div className="glass inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm text-slate-300">
              <span className="h-2 w-2 rounded-full bg-emerald-400" />
              Systems operational
            </div>
            {token ? (
              <div className="flex flex-col items-end gap-2">
                <button
                  type="button"
                  onClick={handleScanInbox}
                  className="rounded-full border border-cyan-500/40 bg-cyan-500/10 px-4 py-2 text-xs font-medium text-cyan-300 hover:bg-cyan-500/20"
                >
                  Scan Gmail inbox
                </button>
                {scanStatus && <p className="text-xs text-slate-500">{scanStatus}</p>}
                <button
                  type="button"
                  onClick={() => {
                    setToken(null);
                    localStorage.removeItem("cybersec_access_token");
                    setScanStatus(null);
                  }}
                  className="rounded-full border border-white/10 px-4 py-2 text-xs text-slate-400 hover:bg-white/5"
                >
                  Sign out
                </button>
              </div>
            ) : (
              <a
                href="http://localhost:8000/auth/login"
                className="rounded-full bg-cyan-500 px-4 py-2 text-sm font-semibold text-slate-950 hover:bg-cyan-400"
              >
                Sign in with Google
              </a>
            )}
          </div>
        </header>

        {loading ? (
          <div className="flex justify-center items-center h-48">
            <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-cyan-500"></div>
          </div>
        ) : (
          <div className="grid gap-6 md:grid-cols-2">
            <StatCard
              label="Total Emails Scanned"
              value={totalScanned !== null ? totalScanned.toString() : "N/A"}
              delta=""
              accent="cyan"
              icon={(
                <svg className="h-6 w-6 text-cyber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1.5}
                    d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                  />
                </svg>
              )}
            />
            <StatCard
              label="Threats Blocked"
              value={threatsBlocked !== null ? threatsBlocked.toString() : "N/A"}
              delta=""
              accent="rose"
              icon={(
                <svg className="h-6 w-6 text-threat-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1.5}
                    d="M12 9v2m0 4h.01M4.93 4.93l14.14 14.14M12 3a9 9 0 100 18 9 9 0 000-18z"
                  />
                </svg>
              )}
            />
            {/* You can add a third StatCard for recentScans if needed, or display it differently */}
          </div>
        )}

        <div className="mt-8 grid gap-6 lg:grid-cols-2">
          <PasswordAnalyzer />
          <ChatBot />
        </div>
      </div>
    </div>
  );
}
