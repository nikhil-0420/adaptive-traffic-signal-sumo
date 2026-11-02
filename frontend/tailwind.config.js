/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ground: 'var(--color-ground)',
        panel: 'var(--color-panel)',
        raised: 'var(--color-raised)',
        inset: 'var(--color-inset)',
        hairline: 'var(--color-hairline)',
        line: 'var(--color-line)',
        accent: {
          DEFAULT: 'var(--color-accent)',
          hover: 'var(--color-accent-hover)',
        },
        ink: {
          DEFAULT: 'var(--color-ink)',
          2: 'var(--color-ink-2)',
          secondary: 'var(--color-ink-2)',
          muted: 'var(--color-ink-muted)',
        },
        petrol: {
          DEFAULT: 'var(--color-petrol)',
          deep: 'var(--color-petrol-deep)',
          bright: 'var(--color-petrol-bright)',
          hover: 'var(--color-petrol-hover)',
          subtle: 'var(--color-petrol-subtle)',
          tint: 'var(--color-petrol-tint)',
        },
        signal: {
          green: 'var(--color-signal-green)',
          'green-tint': 'var(--color-signal-green-tint)',
          'green-text': 'var(--color-signal-green-text)',
          yellow: 'var(--color-signal-yellow)',
          'yellow-tint': 'var(--color-signal-yellow-tint)',
          'yellow-text': 'var(--color-signal-yellow-text)',
          red: 'var(--color-signal-red)',
          'red-tint': 'var(--color-signal-red-tint)',
          'red-text': 'var(--color-signal-red-text)',
        },
        emergency: {
          DEFAULT: 'var(--color-emergency)',
          tint: 'var(--color-emergency-tint)',
        }
      },
      fontFamily: {
        display: ['"Barlow Condensed"', '"Plus Jakarta Sans"', 'sans-serif'],
        sans: ['"Plus Jakarta Sans"', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
      },
      transitionTimingFunction: {
        spring: 'cubic-bezier(0.32, 0.72, 0, 1)',
      },
      transitionDuration: {
        '250': '250ms',
        '400': '400ms',
        '700': '700ms',
      }
    },
  },
  plugins: [],
}
