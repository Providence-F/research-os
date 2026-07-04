/** @type {import('tailwindcss').Config} */

export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    container: {
      center: true,
    },
    extend: {
      colors: {
        ink: "#141413",
        canvas: "#faf9f5",
        mid: "#b0aea5",
        line: "#e8e6dc",
        "text-2": "#5e5d59",
        accent: {
          orange: "#d97757",
          deep: "#b85b44",
          blue: "#6a9bcc",
          green: "#788c5d",
        },
        status: {
          done: "#788c5d",
          failed: "#c62828",
          planned: "#6a9bcc",
        },
        cluster: {
          v07: "#5b8c7e",
          v08: "#c97a4a",
          v09: "#7a5cb0",
          v010: "#4a7c59",
          v05: "#7a7a7a",
          early: "#9c9a92",
        },
      },
      fontFamily: {
        sans: ['Poppins', '"Noto Sans SC"', 'Inter', '-apple-system', 'sans-serif'],
        serif: ['Lora', '"Noto Serif SC"', 'Georgia', 'serif'],
        mono: ['"JetBrains Mono"', '"SF Mono"', 'monospace'],
      },
      fontSize: {
        hero: ['64px', { lineHeight: '70px', fontWeight: '400' }],
        h2: ['32px', { lineHeight: '38px', fontWeight: '500' }],
        h3: ['20px', { lineHeight: '26px', fontWeight: '600' }],
        body: ['16px', { lineHeight: '1.6', fontWeight: '400' }],
        meta: ['13px', { fontWeight: '400' }],
      },
      maxWidth: {
        content: '1400px',
      },
      spacing: {
        'section-pt': '96px',
        'section-pb': '48px',
        'container-x': '64px',
        'card': '32px',
        'card-lg': '48px',
      },
      transitionTimingFunction: {
        'anthropic': 'cubic-bezier(0.16, 1, 0.3, 1)',
      },
    },
  },
  plugins: [],
};
