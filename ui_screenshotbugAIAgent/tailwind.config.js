/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        // The Testing Academy light palette
        paper: '#faf9f5',
        panel: '#f7f4ea',
        sand: '#f0eee5',
        dune: '#f0ead8',
        edge: '#e8e4d8',
        ink: '#2a2620',
        muted: '#6e6a5e',
        clay: '#d97757',
        clayDark: '#bd5d3a',
        moss: '#3f7d43',
        teal: '#0f766e',
      },
      fontFamily: {
        sans: ['"Inter"', 'ui-sans-serif', 'system-ui', '-apple-system', 'Segoe UI', 'sans-serif'],
        serif: ['"Instrument Serif"', 'Georgia', 'ui-serif', 'serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace'],
      },
      boxShadow: {
        card: '0 1px 2px rgba(42,38,32,0.04), 0 8px 24px -12px rgba(42,38,32,0.12)',
      },
    },
  },
  plugins: [],
};
