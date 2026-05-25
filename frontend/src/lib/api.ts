const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export async function sendChatMessage(message: string): Promise<string> {
  const response = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });

  if (!response.ok) {
    throw new Error(`Chat request failed (${response.status})`);
  }

  const data: { reply: string } = await response.json();
  return data.reply;
}
