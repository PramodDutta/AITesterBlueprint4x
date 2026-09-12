import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  AlertTriangle,
  ArrowUpRight,
  Bug,
  CheckCircle2,
  Clipboard,
  Eye,
  ImageIcon,
  Loader2,
  RotateCcw,
  Sparkles,
  Upload,
  X,
} from 'lucide-react';

const SEVERITIES = [
  'S1 - blocks release',
  'S2 - major function broken',
  'S3 - minor issue',
  'S4 - cosmetic',
];

const STAGES = [
  'Uploading the screenshot',
  'Reading the image',
  'Drafting the report',
  'Filing the ticket',
  'Attaching the screenshot',
];

const MAX_BYTES = 15 * 1024 * 1024;

/* ---------------------------------------------------------------- primitives */

function Badge({ tone = 'neutral', children }) {
  const tones = {
    neutral: 'bg-sand text-muted border-edge',
    clay: 'bg-clay/10 text-clayDark border-clay/25',
    moss: 'bg-moss/10 text-moss border-moss/25',
    warn: 'bg-amber-400/15 text-amber-700 border-amber-500/30',
  };
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium ${tones[tone]}`}
    >
      {children}
    </span>
  );
}

function Field({ label, hint, children }) {
  return (
    <label className="block">
      <div className="mb-1.5 flex items-baseline justify-between gap-3">
        <span className="text-sm font-medium text-ink">{label}</span>
        {hint && <span className="text-xs text-muted">{hint}</span>}
      </div>
      {children}
    </label>
  );
}

const inputCls =
  'w-full rounded-lg border border-edge bg-white px-3 py-2.5 text-sm text-ink ' +
  'placeholder:text-muted/60 outline-none transition ' +
  'focus:border-clay focus:ring-2 focus:ring-clay/20';

/* ----------------------------------------------------------------- dropzone */

function Dropzone({ file, previewUrl, onPick, onClear, disabled }) {
  const inputRef = useRef(null);
  const [dragging, setDragging] = useState(false);

  const accept = useCallback(
    (candidate) => {
      if (!candidate) return;
      if (!candidate.type.startsWith('image/')) {
        onPick(null, 'That is not an image. Upload a PNG or JPG screenshot.');
        return;
      }
      if (candidate.size > MAX_BYTES) {
        onPick(null, 'That image is over 15MB. Groq caps a request at 20MB.');
        return;
      }
      onPick(candidate, null);
    },
    [onPick]
  );

  // Testers screenshot then paste. Supporting Ctrl+V removes the save-to-disk step.
  useEffect(() => {
    const onPaste = (e) => {
      if (disabled) return;
      const item = [...(e.clipboardData?.items || [])].find((i) => i.type.startsWith('image/'));
      if (item) {
        e.preventDefault();
        accept(item.getAsFile());
      }
    };
    window.addEventListener('paste', onPaste);
    return () => window.removeEventListener('paste', onPaste);
  }, [accept, disabled]);

  if (file && previewUrl) {
    return (
      <div className="relative overflow-hidden rounded-xl border border-edge bg-white">
        <img src={previewUrl} alt="Screenshot preview" className="max-h-72 w-full object-contain" />
        <div className="flex items-center justify-between gap-3 border-t border-edge bg-panel px-3 py-2">
          <span className="truncate font-mono text-xs text-muted">
            {file.name} · {(file.size / 1024).toFixed(0)} KB
          </span>
          <button
            type="button"
            onClick={onClear}
            disabled={disabled}
            className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium text-muted transition hover:bg-edge hover:text-ink disabled:opacity-40"
          >
            <X size={13} /> Replace
          </button>
        </div>
      </div>
    );
  }

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        if (!disabled) setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragging(false);
        if (!disabled) accept(e.dataTransfer.files?.[0]);
      }}
      onClick={() => !disabled && inputRef.current?.click()}
      className={`flex cursor-pointer flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed px-6 py-12 text-center transition ${
        dragging ? 'border-clay bg-clay/5' : 'border-edge bg-white hover:border-clay/50 hover:bg-panel'
      } ${disabled ? 'pointer-events-none opacity-50' : ''}`}
    >
      <div className="rounded-full bg-panel p-3">
        <ImageIcon size={22} className="text-clay" strokeWidth={1.75} />
      </div>
      <div>
        <p className="text-sm font-medium text-ink">Drop a screenshot, or click to browse</p>
        <p className="mt-1 flex items-center justify-center gap-1.5 text-xs text-muted">
          <Clipboard size={12} /> You can also just paste with Ctrl+V
        </p>
      </div>
      <input
        ref={inputRef}
        type="file"
        accept="image/png,image/jpeg"
        className="hidden"
        onChange={(e) => accept(e.target.files?.[0])}
      />
    </div>
  );
}

/* ------------------------------------------------------------------- result */

function ResultCard({ result, onReset }) {
  const lowConfidence = String(result.confidence).toLowerCase() === 'low';

  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-moss/25 bg-moss/5 p-4">
        <div className="flex items-start gap-3">
          <CheckCircle2 size={20} className="mt-0.5 shrink-0 text-moss" />
          <div className="min-w-0 flex-1">
            <p className="text-sm font-semibold text-ink">Bug filed</p>
            <p className="mt-0.5 text-sm text-muted">
              The screenshot is attached to the ticket.
            </p>
            {result.jira_key && (
              <a
                href={result.jira_url}
                target="_blank"
                rel="noreferrer"
                className="mt-2.5 inline-flex items-center gap-1.5 rounded-lg bg-ink px-3 py-1.5 font-mono text-sm font-medium text-paper transition hover:bg-ink/85"
              >
                {result.jira_key}
                <ArrowUpRight size={14} />
              </a>
            )}
          </div>
        </div>
      </div>

      {lowConfidence && (
        <div className="rounded-xl border border-amber-500/30 bg-amber-400/10 p-4">
          <div className="flex items-start gap-3">
            <AlertTriangle size={18} className="mt-0.5 shrink-0 text-amber-600" />
            <div>
              <p className="text-sm font-semibold text-ink">The model is not confident</p>
              <p className="mt-0.5 text-sm text-muted">
                It could not clearly identify a defect in this screenshot. Read the draft
                before assigning it. This is the model refusing to invent a bug, which is
                the behaviour you want.
              </p>
            </div>
          </div>
        </div>
      )}

      <div className="rounded-xl border border-edge bg-white p-5 shadow-card">
        <div className="mb-3 flex flex-wrap items-center gap-2">
          {result.severity && <Badge tone="clay">{result.severity}</Badge>}
          <Badge tone={lowConfidence ? 'warn' : 'moss'}>
            {result.confidence || 'unknown'} confidence
          </Badge>
          {result.suggested_component && <Badge>{result.suggested_component}</Badge>}
        </div>

        <h3 className="font-serif text-xl leading-snug text-ink">{result.summary}</h3>

        {Array.isArray(result.steps_to_reproduce) && result.steps_to_reproduce.length > 0 && (
          <section className="mt-5">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-muted">
              Steps to reproduce
            </h4>
            <ol className="mt-2 space-y-1.5">
              {result.steps_to_reproduce.map((s, i) => (
                <li key={i} className="flex gap-2.5 text-sm text-ink">
                  <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-panel font-mono text-[11px] text-muted">
                    {i + 1}
                  </span>
                  <span>{s}</span>
                </li>
              ))}
            </ol>
          </section>
        )}

        <div className="mt-5 grid gap-4 sm:grid-cols-2">
          {result.expected_result && (
            <div>
              <h4 className="text-xs font-semibold uppercase tracking-wider text-muted">Expected</h4>
              <p className="mt-1.5 text-sm text-ink">{result.expected_result}</p>
            </div>
          )}
          {result.actual_result && (
            <div>
              <h4 className="text-xs font-semibold uppercase tracking-wider text-muted">Actual</h4>
              <p className="mt-1.5 text-sm text-ink">{result.actual_result}</p>
            </div>
          )}
        </div>

        {Array.isArray(result.visual_observations) && result.visual_observations.length > 0 && (
          <section className="mt-5 rounded-lg border border-edge bg-panel p-4">
            <h4 className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-muted">
              <Eye size={13} /> Read from the screenshot
            </h4>
            <ul className="mt-2 space-y-1.5">
              {result.visual_observations.map((o, i) => (
                <li key={i} className="flex gap-2 text-sm text-ink">
                  <span className="mt-2 h-1 w-1 shrink-0 rounded-full bg-clay" />
                  <span>{o}</span>
                </li>
              ))}
            </ul>
          </section>
        )}
      </div>

      <button
        onClick={onReset}
        className="inline-flex items-center gap-2 rounded-lg border border-edge bg-white px-4 py-2.5 text-sm font-medium text-ink transition hover:bg-panel"
      >
        <RotateCcw size={15} /> File another
      </button>
    </div>
  );
}

/* ---------------------------------------------------------------------- app */

export default function App() {
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [logs, setLogs] = useState('');
  const [steps, setSteps] = useState('');
  const [severity, setSeverity] = useState(SEVERITIES[2]);
  const [environment, setEnvironment] = useState('');

  const [busy, setBusy] = useState(false);
  const [stage, setStage] = useState(0);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  useEffect(() => {
    if (!file) {
      setPreviewUrl(null);
      return;
    }
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  // The proxy gives one response at the end, so walk the stage labels on a timer
  // to show that something is happening rather than freezing on a spinner.
  useEffect(() => {
    if (!busy) return;
    const t = setInterval(() => setStage((s) => Math.min(s + 1, STAGES.length - 1)), 2600);
    return () => clearInterval(t);
  }, [busy]);

  const reset = () => {
    setResult(null);
    setError(null);
    setFile(null);
    setLogs('');
    setSteps('');
    setEnvironment('');
    setStage(0);
  };

  async function submit(e) {
    e.preventDefault();
    if (!file || busy) return;

    setBusy(true);
    setStage(0);
    setError(null);
    setResult(null);

    const body = new FormData();
    body.append('screenshot', file, file.name);
    body.append('Error logs', logs);
    body.append('Steps you took', steps);
    body.append('Severity', severity);
    body.append('Environment', environment);

    try {
      const res = await fetch('/api/report', { method: 'POST', body });
      const data = await res.json().catch(() => null);

      if (!res.ok || !data || data.ok === false) {
        setError({
          message: data?.error || `The request failed with status ${res.status}.`,
          detail: data?.detail,
        });
      } else {
        setResult(data);
      }
    } catch (err) {
      setError({ message: 'Could not reach the server: ' + err.message });
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="grain min-h-screen">
      <header className="border-b border-edge bg-paper/80 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-5 py-4">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-clay">
              <Bug size={17} className="text-white" strokeWidth={2.25} />
            </div>
            <div className="leading-tight">
              <p className="text-sm font-semibold text-ink">The Testing Academy</p>
              <p className="text-xs text-muted">AI Tester Blueprint · Chapter 08</p>
            </div>
          </div>
          <Badge tone="clay">
            <Sparkles size={12} /> Groq vision · n8n · Jira
          </Badge>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-5 py-10">
        <div className="max-w-2xl">
          <h1 className="font-serif text-4xl leading-tight text-ink sm:text-5xl">
            File a bug from a screenshot
          </h1>
          <p className="mt-3 text-base leading-relaxed text-muted">
            Upload what you saw. A vision model reads the image, drafts the steps to
            reproduce and the visual detail you would otherwise retype, then files it in
            Jira with the screenshot attached. It reports only what is actually visible.
          </p>
        </div>

        <div className="mt-9 grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
          <form onSubmit={submit} className="space-y-5 rounded-2xl border border-edge bg-white/70 p-6 shadow-card">
            <Field label="Screenshot" hint="PNG or JPG, required">
              <Dropzone
                file={file}
                previewUrl={previewUrl}
                disabled={busy}
                onPick={(f, msg) => {
                  if (msg) setError({ message: msg });
                  else setError(null);
                  if (f) setFile(f);
                }}
                onClear={() => setFile(null)}
              />
            </Field>

            <Field label="Error logs" hint="optional">
              <textarea
                rows={3}
                value={logs}
                onChange={(e) => setLogs(e.target.value)}
                disabled={busy}
                placeholder="Console output, stack trace, network error"
                className={`${inputCls} resize-y font-mono text-xs`}
              />
            </Field>

            <Field label="Steps you took" hint="optional">
              <textarea
                rows={2}
                value={steps}
                onChange={(e) => setSteps(e.target.value)}
                disabled={busy}
                placeholder="What were you doing when this appeared?"
                className={`${inputCls} resize-y`}
              />
            </Field>

            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Severity">
                <select
                  value={severity}
                  onChange={(e) => setSeverity(e.target.value)}
                  disabled={busy}
                  className={inputCls}
                >
                  {SEVERITIES.map((s) => (
                    <option key={s}>{s}</option>
                  ))}
                </select>
              </Field>
              <Field label="Environment" hint="optional">
                <input
                  type="text"
                  value={environment}
                  onChange={(e) => setEnvironment(e.target.value)}
                  disabled={busy}
                  placeholder="Chrome 141 / staging / macOS"
                  className={inputCls}
                />
              </Field>
            </div>

            <button
              type="submit"
              disabled={!file || busy}
              className="inline-flex w-full items-center justify-center gap-2 rounded-lg bg-clay px-4 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-clayDark disabled:cursor-not-allowed disabled:bg-edge disabled:text-muted"
            >
              {busy ? (
                <>
                  <Loader2 size={16} className="animate-spin" /> {STAGES[stage]}…
                </>
              ) : (
                <>
                  <Upload size={16} /> Draft and file the bug
                </>
              )}
            </button>

            <p className="text-center text-xs text-muted">
              The draft is written by a model. Read it before you assign it.
            </p>
          </form>

          <div>
            {error && (
              <div className="rounded-xl border border-red-300 bg-red-50 p-4">
                <div className="flex items-start gap-3">
                  <AlertTriangle size={18} className="mt-0.5 shrink-0 text-red-600" />
                  <div className="min-w-0">
                    <p className="text-sm font-semibold text-ink">That did not work</p>
                    <p className="mt-1 text-sm text-muted">{error.message}</p>
                    {error.detail && (
                      <pre className="mt-2 max-h-40 overflow-auto rounded-lg bg-white p-2.5 font-mono text-[11px] leading-relaxed text-muted">
                        {error.detail}
                      </pre>
                    )}
                  </div>
                </div>
              </div>
            )}

            {result && <ResultCard result={result} onReset={reset} />}

            {!result && !error && (
              <div className="flex h-full min-h-[280px] flex-col items-center justify-center rounded-2xl border border-dashed border-edge bg-white/40 px-6 text-center">
                <div className="rounded-full bg-panel p-3">
                  <Bug size={20} className="text-muted" strokeWidth={1.75} />
                </div>
                <p className="mt-3 text-sm font-medium text-ink">The draft appears here</p>
                <p className="mt-1 max-w-xs text-sm text-muted">
                  Summary, steps to reproduce, what the model could read off the image, and
                  the Jira key once it is filed.
                </p>
              </div>
            )}
          </div>
        </div>
      </main>

      <footer className="mx-auto max-w-6xl px-5 pb-10 pt-4">
        <p className="border-t border-edge pt-5 text-xs text-muted">
          AI Tester Blueprint · Chapter 08 · workflow 09 on n8n. The browser never talks to
          n8n directly: requests go through a serverless proxy so the webhook URL stays
          server-side.
        </p>
      </footer>
    </div>
  );
}
