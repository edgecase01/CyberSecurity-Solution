import { useMemo, useState } from "react";
import zxcvbn from "zxcvbn";

const strengthLabels = ["Very weak", "Weak", "Fair", "Strong", "Very strong"];
const strengthColors = [
  "bg-threat-500",
  "bg-orange-500",
  "bg-amber-400",
  "bg-lime-400",
  "bg-emerald-400",
];

export default function PasswordAnalyzer() {
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  const analysis = useMemo(() => {
    if (!password) {
      return null;
    }
    return zxcvbn(password);
  }, [password]);

  const score = analysis?.score ?? 0;
  const feedback = analysis?.feedback;

  return (
    <section className="glass rounded-2xl p-6">
      <div className="mb-6 flex items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-white">Password Analyzer</h2>
          <p className="mt-1 text-sm text-slate-400">
            Checked locally with zxcvbn — your password never leaves the browser.
          </p>
        </div>
        <span className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-300">
          Client-side only
        </span>
      </div>

      <label className="block text-sm font-medium text-slate-300" htmlFor="password-input">
        Test a password
      </label>
      <div className="relative mt-2">
        <input
          id="password-input"
          type={showPassword ? "text" : "password"}
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          placeholder="Type a password to analyze…"
          autoComplete="off"
          className="w-full rounded-xl border border-white/10 bg-slate-900/70 px-4 py-3 pr-28 text-white outline-none ring-cyber-500/40 placeholder:text-slate-500 focus:ring-2"
        />
        <button
          type="button"
          onClick={() => setShowPassword((value) => !value)}
          className="absolute right-2 top-1/2 -translate-y-1/2 rounded-lg px-3 py-1.5 text-xs font-medium text-slate-300 hover:bg-white/5"
        >
          {showPassword ? "Hide" : "Show"}
        </button>
      </div>

      <div className="mt-5">
        <div className="mb-2 flex items-center justify-between text-sm">
          <span className="text-slate-400">Strength</span>
          <span className="font-medium text-white">
            {password ? strengthLabels[score] : "—"}
          </span>
        </div>
        <div className="flex gap-2">
          {strengthLabels.map((_, index) => (
            <div
              key={index}
              className={`h-2 flex-1 rounded-full transition ${
                password && index <= score ? strengthColors[score] : "bg-slate-800"
              }`}
            />
          ))}
        </div>
        {analysis && (
          <p className="mt-2 text-xs text-slate-500">
            Estimated crack time: {analysis.crack_times_display.offline_slow_hashing_1e4_per_second}
          </p>
        )}
      </div>

      {feedback && (feedback.warning || feedback.suggestions.length > 0) && (
        <div className="mt-5 rounded-xl border border-white/10 bg-slate-900/50 p-4">
          <p className="text-sm font-medium text-white">Feedback</p>
          {feedback.warning && (
            <p className="mt-2 text-sm text-amber-300">{feedback.warning}</p>
          )}
          {feedback.suggestions.length > 0 && (
            <ul className="mt-3 space-y-2 text-sm text-slate-300">
              {feedback.suggestions.map((suggestion) => (
                <li key={suggestion} className="flex gap-2">
                  <span className="text-cyber-400">•</span>
                  <span>{suggestion}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </section>
  );
}
