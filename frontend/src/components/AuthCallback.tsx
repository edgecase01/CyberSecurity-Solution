import { useEffect, useState } from "react";
import { captureTokenFromUrl } from "../lib/auth";
import Dashboard from "./Dashboard";

export default function AuthCallback() {
  const [ready, setReady] = useState(false);

  useEffect(() => {
    captureTokenFromUrl();
    setReady(true);
  }, []);

  if (!ready) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950 text-slate-300">
        Signing you in…
      </div>
    );
  }

  return <Dashboard />;
}
