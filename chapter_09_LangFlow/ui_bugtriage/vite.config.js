import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

// The browser calls /api/run on the vite dev server, which forwards to LangFlow and
// injects the API key. Two reasons: it sidesteps CORS, and the key never ships in
// client-side JS where devtools would show it.
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const target = env.LANGFLOW_URL || 'http://localhost:7860';
  const flowId = env.LANGFLOW_FLOW_ID || '';

  return {
    plugins: [react()],
    server: {
      port: 5180,
      open: true,
      proxy: {
        '/api/run': {
          target,
          changeOrigin: true,
          rewrite: () => `/api/v1/run/${flowId}?stream=false`,
          configure: (proxy) => {
            proxy.on('proxyReq', (proxyReq) => {
              if (env.LANGFLOW_API_KEY) proxyReq.setHeader('x-api-key', env.LANGFLOW_API_KEY);
            });
          },
        },
      },
    },
  };
});
