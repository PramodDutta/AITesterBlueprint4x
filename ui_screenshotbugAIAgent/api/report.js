// Serverless proxy: browser -> /api/report -> n8n webhook.
//
// This exists so the browser never talks to n8n directly. That kills the CORS
// problem (same-origin request) and keeps the n8n URL out of client-side code,
// where anyone could read it from devtools and POST to it.
//
// Set N8N_WEBHOOK_URL in the Vercel project (Settings > Environment Variables) to
// the production webhook of workflow 09, e.g.
//   https://<your-n8n-host>/webhook/screenshot-bug-report

export const config = {
  api: {
    // The body is multipart/form-data carrying an image. Parsing it here would
    // destroy the boundary, so forward the raw bytes untouched.
    bodyParser: false,
  },
};

async function readRawBody(req) {
  // Vercel may have already buffered the body depending on content type.
  if (Buffer.isBuffer(req.body)) return req.body;
  if (typeof req.body === 'string') return Buffer.from(req.body);

  const chunks = [];
  for await (const chunk of req) {
    chunks.push(typeof chunk === 'string' ? Buffer.from(chunk) : chunk);
  }
  return Buffer.concat(chunks);
}

export default async function handler(req, res) {
  if (req.method === 'OPTIONS') {
    res.setHeader('Allow', 'POST, OPTIONS');
    return res.status(204).end();
  }

  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST, OPTIONS');
    return res.status(405).json({ ok: false, error: 'Use POST.' });
  }

  const target = process.env.N8N_WEBHOOK_URL;
  if (!target) {
    return res.status(503).json({
      ok: false,
      error:
        'N8N_WEBHOOK_URL is not set on this deployment. Add it in Vercel under ' +
        'Settings > Environment Variables, pointing at the production webhook URL ' +
        'of workflow 09, then redeploy.',
    });
  }

  const contentType = req.headers['content-type'];
  if (!contentType || !contentType.includes('multipart/form-data')) {
    return res.status(415).json({
      ok: false,
      error: 'Expected multipart/form-data with a screenshot part.',
    });
  }

  let body;
  try {
    body = await readRawBody(req);
  } catch (err) {
    return res.status(400).json({ ok: false, error: 'Could not read the upload: ' + err.message });
  }

  if (!body || body.length === 0) {
    return res.status(400).json({ ok: false, error: 'Empty request body.' });
  }

  // n8n runs a vision call and two Jira calls, so give it room before giving up.
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 55000);

  try {
    const upstream = await fetch(target, {
      method: 'POST',
      headers: {
        'content-type': contentType,
        'content-length': String(body.length),
      },
      body,
      signal: controller.signal,
    });

    const text = await upstream.text();

    if (!upstream.ok) {
      return res.status(upstream.status === 404 ? 502 : upstream.status).json({
        ok: false,
        error:
          upstream.status === 404
            ? 'n8n returned 404. The workflow is probably not Active, or the webhook ' +
              'path does not match. A test URL only listens while you click "Test step".'
            : 'n8n returned ' + upstream.status + '.',
        detail: text.slice(0, 600),
      });
    }

    // The Respond to UI node returns JSON, but a misconfigured workflow can return
    // an empty body or HTML. Surface that clearly rather than throwing.
    try {
      return res.status(200).json(JSON.parse(text));
    } catch {
      return res.status(502).json({
        ok: false,
        error:
          'n8n replied with a non-JSON body. Check that workflow 09 ends in a ' +
          '"Respond to Webhook" node and that the Webhook node uses ' +
          'Response Mode: "Using Respond to Webhook Node".',
        detail: text.slice(0, 600),
      });
    }
  } catch (err) {
    if (err.name === 'AbortError') {
      return res.status(504).json({
        ok: false,
        error: 'n8n did not respond within 55 seconds. The run may still have filed the bug.',
      });
    }
    return res.status(502).json({ ok: false, error: 'Could not reach n8n: ' + err.message });
  } finally {
    clearTimeout(timeout);
  }
}
