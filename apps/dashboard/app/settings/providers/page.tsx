"use client";

import { useEffect, useState } from "react";

interface ProviderSession {
  provider_id: string;
  status: string;
  session_id: string;
}

export default function ProvidersSettingsPage() {
  const [sessions, setSessions] = useState<ProviderSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState(false);
  const [error, setError] = useState("");

  const fetchSessions = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/v1/auth/sessions");
      if (!res.ok) throw new Error("Failed to fetch sessions");
      const data = await res.json();
      setSessions(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSessions();
  }, []);

  const handleConnectChatGPT = async () => {
    setConnecting(true);
    setError("");
    try {
      const res = await fetch("http://localhost:8000/api/v1/auth/providers/ai.openai.codex/connect", {
        method: "POST"
      });
      if (!res.ok) throw new Error("Connection failed");
      await fetchSessions();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setConnecting(false);
    }
  };

  const hasCodexSession = sessions.some(s => s.provider_id === "ai.openai.codex" && s.status === "active");

  return (
    <div className="p-8 max-w-4xl mx-auto font-sans text-gray-900">
      <h1 className="text-3xl font-bold mb-8">Settings</h1>
      
      <section className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
        <h2 className="text-xl font-semibold mb-4">Connected Providers</h2>
        
        {error && <div className="bg-red-50 text-red-600 p-3 rounded mb-4 text-sm">{error}</div>}
        
        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 border rounded bg-gray-50">
            <div>
              <h3 className="font-medium text-lg">ChatGPT / OpenAI Codex</h3>
              <p className="text-sm text-gray-500">Connect to your ChatGPT account via OAuth.</p>
            </div>
            
            {loading ? (
              <span className="text-gray-400 text-sm">Loading state...</span>
            ) : hasCodexSession ? (
              <span className="px-3 py-1 bg-green-100 text-green-700 border border-green-200 rounded-full text-sm font-medium">
                Active Session
              </span>
            ) : (
              <button 
                onClick={handleConnectChatGPT}
                disabled={connecting}
                className="px-4 py-2 bg-black text-white text-sm font-medium rounded hover:bg-gray-800 disabled:opacity-50 transition-colors"
              >
                {connecting ? "Connecting..." : "Connect ChatGPT"}
              </button>
            )}
          </div>
          
          <div className="flex items-center justify-between p-4 border rounded bg-gray-50 opacity-60">
            <div>
              <h3 className="font-medium text-lg">Google Gemini</h3>
              <p className="text-sm text-gray-500">Connect to Google AI Studio via API Key.</p>
            </div>
            <span className="px-3 py-1 bg-gray-200 text-gray-700 rounded-full text-sm font-medium">
              Not Configured
            </span>
          </div>
        </div>

        <div className="mt-8 border-t pt-4">
          <h3 className="text-sm font-semibold mb-3 text-gray-600 uppercase tracking-wider">Debug: Active Sessions</h3>
          {sessions.length === 0 ? (
            <p className="text-sm text-gray-500 italic">No active sessions found.</p>
          ) : (
            <ul className="text-xs text-gray-600 space-y-2">
              {sessions.map(s => (
                <li key={s.session_id} className="font-mono bg-gray-100 p-2 rounded">
                  <span className="font-bold">{s.provider_id}</span> - {s.status} <span className="text-gray-400">({s.session_id})</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </section>
    </div>
  );
}
