// Vercel serverless proxy: browser -> /api/run -> LangFlow.
//
// Same job as the vite proxy in vite.config.js, but for the deployed site: it keeps
// LANGFLOW_API_KEY server-side and avoids CORS by being same-origin.
//
// IMPORTANT: LANGFLOW_URL must be reachable from the public internet. A Vercel
// function cannot see your machine's localhost:7860 - "localhost" there is the
// function's own container. Use a tunnel (cloudflared / ngrok) or a hosted LangFlow.

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST');
    return res.status(405).json({ error: 'Use POST.' });
  }

  const base = process.env.LANGFLOW_URL;
  const flowId = process.env.LANGFLOW_FLOW_ID;
  const apiKey = process.env.LANGFLOW_API_KEY;

  if (!base || !flowId) {
    return res.status(503).json({
      error:
        'LANGFLOW_URL and LANGFLOW_FLOW_ID are not set on this deployment. ' +
        'Add them in Vercel under Settings > Environment Variables. LANGFLOW_URL must be ' +
        'a public address, not localhost - a Vercel function cannot reach your machine.',
    });
  }

  if (/^https?:\/\/(localhost|127\.0\.0\.1|0\.0\.0\.0)/i.test(base)) {
    return res.status(503).json({
      error:
        `LANGFLOW_URL is set to "${base}", which this function cannot reach. ` +
        'From a serverless function, localhost is its own container. Expose LangFlow with ' +
        '`cloudflared tunnel --url http://localhost:7860` and use the URL it prints.',
    });
  }

  const target = `${base.replace(/\/+$/, '')}/api/v1/run/${flowId}?stream=false`;
  const body = typeof req.body === 'string' ? req.body : JSON.stringify(req.body ?? {});

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 55000);

  try {
    const upstream = await fetch(target, {
      method: 'POST',
      headers: {
        'content-type': 'application/json',
        ...(apiKey ? { 'x-api-key': apiKey } : {}),
      },
      body,
      signal: controller.signal,
    });

    const text = await upstream.text();
    try {
      return res.status(upstream.status).json(JSON.parse(text));
    } catch {
      return res.status(502).json({
        error: `LangFlow replied with a non-JSON body (HTTP ${upstream.status}).`,
        detail: text.slice(0, 500),
      });
    }
  } catch (err) {
    if (err.name === 'AbortError') {
      return res.status(504).json({ error: 'LangFlow did not respond within 55 seconds.' });
    }
    return res.status(502).json({
      error: 'Could not reach LangFlow: ' + err.message,
      detail: `Tried ${target}. Is the tunnel still running?`,
    });
  } finally {
    clearTimeout(timer);
  }
}
