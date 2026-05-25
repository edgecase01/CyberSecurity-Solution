import { FormEvent, useEffect, useRef, useState } from "react";
import { sendChatMessage } from "../lib/api";

type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
};

const starterMessage: ChatMessage = {
  id: "welcome",
  role: "assistant",
  content:
    "Hi — I'm your Cybersecurity Assistant. Ask about phishing, passwords, malware, or suspicious links.",
};

export default function ChatBot() {
  const [messages, setMessages] = useState<ChatMessage[]>([starterMessage]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || loading) {
      return;
    }

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: trimmed,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);
    setError(null);

    try {
      const reply = await sendChatMessage(trimmed);
      setMessages((prev) => [
        ...prev,
        { id: crypto.randomUUID(), role: "assistant", content: reply },
      ]);
    } catch {
      setError("Unable to reach the chatbot. Is the backend running on port 8000?");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="glass flex h-full min-h-[420px] flex-col rounded-2xl">
      <div className="border-b border-white/10 px-6 py-4">
        <h2 className="text-lg font-semibold text-white">Security Chatbot</h2>
        <p className="mt-1 text-sm text-slate-400">Powered by the backend `/chat` endpoint.</p>
      </div>

      <div className="flex-1 space-y-4 overflow-y-auto px-4 py-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                message.role === "user"
                  ? "bg-cyber-600/80 text-white"
                  : "border border-white/10 bg-slate-900/70 text-slate-200"
              }`}
            >
              {message.content}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="rounded-2xl border border-white/10 bg-slate-900/70 px-4 py-3 text-sm text-slate-400">
              Analyzing…
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {error && <p className="px-4 pb-2 text-sm text-threat-400">{error}</p>}

      <form onSubmit={handleSubmit} className="border-t border-white/10 p-4">
        <div className="flex gap-2">
          <input
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder="Ask about a threat, email, or password…"
            className="flex-1 rounded-xl border border-white/10 bg-slate-900/70 px-4 py-3 text-sm text-white outline-none ring-cyber-500/40 placeholder:text-slate-500 focus:ring-2"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="rounded-xl bg-cyber-500 px-4 py-3 text-sm font-semibold text-slate-950 transition hover:bg-cyber-400 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Send
          </button>
        </div>
      </form>
    </section>
  );
}
