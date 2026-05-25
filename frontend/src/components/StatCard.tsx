import { ReactNode } from "react";

type StatCardProps = {
  label: string;
  value: string;
  delta: string;
  icon: ReactNode;
  accent: "cyan" | "rose";
};

export default function StatCard({ label, value, delta, icon, accent }: StatCardProps) {
  const accentClasses =
    accent === "cyan"
      ? "from-cyber-500/20 to-cyan-900/10 text-cyber-400"
      : "from-threat-500/20 to-rose-900/10 text-threat-400";

  return (
    <div className="glass group relative overflow-hidden rounded-2xl p-6 shadow-glow transition hover:border-white/20">
      <div className={`absolute inset-0 bg-gradient-to-br ${accentClasses} opacity-60`} />
      <div className="relative flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-slate-400">{label}</p>
          <p className="mt-2 text-3xl font-semibold tracking-tight text-white">{value}</p>
          <p className="mt-2 text-xs text-slate-400">{delta}</p>
        </div>
        <div className="rounded-xl border border-white/10 bg-slate-900/60 p-3">{icon}</div>
      </div>
    </div>
  );
}
