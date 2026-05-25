import { useEffect, useState } from "react";
import AuthCallback from "./components/AuthCallback";
import Dashboard from "./components/Dashboard";

export default function App() {
  const [path, setPath] = useState(window.location.pathname);

  useEffect(() => {
    const onPopState = () => setPath(window.location.pathname);
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  if (path === "/auth/callback" || path.startsWith("/auth/callback")) {
    return <AuthCallback />;
  }

  return <Dashboard />;
}
