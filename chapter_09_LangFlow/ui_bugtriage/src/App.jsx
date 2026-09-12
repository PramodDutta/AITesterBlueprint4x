import React, { useEffect, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const SAMPLES = ['VWO-51', 'VWO-49', 'VWO-126'];

export default function App() {
  const [key, setKey] = useState('VWO-51');
  const [messages, setMessages] = useState([]);
  const [busy, setBusy] = useState(false);
  const endRef = useRef(null);
  const sessionRef = useRef('ui-' + Math.random().toString(36).slice(2, 9));

  // Block body, not a concise arrow: an expression body would return its value and
  // React would try to call it as the cleanup function.
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, busy]);

  async function run(e) {
    e?.preventDefault();
    const ticket = key.trim();
    if (!ticket || busy) return;

    setMessages((m) => [...m, { role: 'user', text: ticket }]);
    setBusy(true);
    const started = performance.now();

    try {
      const res = await fetch('/api/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          output_type: 'chat',
          // Must be "chat", not "text": the flow's entry node is a ChatInput, and
          // input_type "text" targets a TextInput that does not exist here, so the
          // ticket key never reaches the URL template and Jira 405s.
          input_type: 'chat',
          input_value: ticket,
          session_id: sessionRef.current,
        }),
      });

      const raw = await res.text();
      let data;
      try {
        data = JSON.parse(raw);
      } catch {
        throw new Error(`LangFlow returned non-JSON (HTTP ${res.status}): ${raw.slice(0, 300)}`);
      }
      if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);

      const msg = data?.outputs?.[0]?.outputs?.[0]?.results?.message?.data;
      if (!msg?.text) throw new Error('No message in the response. Check the flow output node.');

      setMessages((m) => [
        ...m,
        {
          role: 'ai',
          text: msg.text,
          model: msg.properties?.source?.source,
          usage: msg.properties?.usage,
          secs: ((performance.now() - started) / 1000).toFixed(1),
        },
      ]);
    } catch (err) {
      setMessages((m) => [...m, { role: 'error', text: err.message }]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="app">
      <header>
        <div className="dot">🐞</div>
        <div>
          <h1>Bug Triage Agent</h1>
          <p>LangFlow · DeepSeek · Jira</p>
        </div>
        <span className="flow">AI4X_004_Via_UI</span>
      </header>

      <div className="thread">
        {messages.length === 0 && !busy && (
          <div className="empty">
            <h2>Triage a Jira ticket</h2>
            <p>Enter an issue key. The flow fetches it from Jira and DeepSeek returns severity, priority and QA comments.</p>
            <div className="chips">
              {SAMPLES.map((s) => (
                <button type="button" key={s} className="chip" onClick={() => setKey(s)}>{s}</button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m, i) =>
          m.role === 'user' ? (
            <div className="msg user" key={i}><div className="bubble-user">{m.text}</div></div>
          ) : m.role === 'error' ? (
            <div className="msg" key={i}>
              <div className="err">
                <b>Run failed</b>
                <pre>{m.text}</pre>
              </div>
            </div>
          ) : (
            <div className="msg" key={i}>
              <div className="bubble-ai">
                <div className="meta">
                  <span><b>{m.model || 'model'}</b></span>
                  <span>{m.secs}s</span>
                  {m.usage && <span>{m.usage.input_tokens} in / {m.usage.output_tokens} out</span>}
                </div>
                <div className="md">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{m.text}</ReactMarkdown>
                </div>
              </div>
            </div>
          )
        )}

        {busy && (
          <div className="msg">
            <div className="bubble-ai">
              <div className="meta"><span>Fetching the ticket and triaging…</span></div>
            </div>
          </div>
        )}
        <div ref={endRef} />
      </div>

      <footer>
        <form className="row" onSubmit={run}>
          <input
            type="text"
            value={key}
            onChange={(e) => setKey(e.target.value.toUpperCase())}
            placeholder="VWO-51"
            disabled={busy}
          />
          <button type="submit" disabled={busy || !key.trim()}>
            {busy ? <><span className="spin" /> Running</> : <>Run ▸</>}
          </button>
        </form>
        <p className="hint">Calls the flow through the vite proxy, so the API key stays out of the browser.</p>
      </footer>
    </div>
  );
}
