/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        serif: ['"Instrument Serif"', 'Georgia', 'serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      colors: {
        // Warm paper palette inspired by Claude's iOS app.
        paper: {
          DEFAULT: '#F2EFE9',
          elevated: '#FBFAF7',
          inset: '#E9E5DC',
          line: '#E0DBD0',
        },
        ink: {
          DEFAULT: '#3D3929',
          soft: '#5E5948',
          mute: '#8A8474',
          faint: '#B3AC9A',
        },
        clay: {
          DEFAULT: '#D97757',
          soft: '#F2E3DB',
          line: '#E8C8BB',
          deep: '#C15F3F',
        },
        surface: { DEFAULT: '#FBFAF7', card: '#FBFAF7', hover: '#F4F1EA' },
        primary: {
          DEFAULT: '#D97757',
          50: '#FBF0EC',
          100: '#F5DFD7',
          200: '#EDC6B8',
          300: '#E3A78F',
          400: '#DD8A6B',
          500: '#D97757',
          600: '#C15F3F',
          700: '#A34E33',
        },
        secondary: {
          DEFAULT: '#8A8474',
          400: '#9C9686',
          500: '#8A8474',
          600: '#6E6959',
        },
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-out',
        'slide-up': 'slideUp 0.5s ease-out',
        'slide-down': 'slideDown 0.3s ease-out',
        'scale-in': 'scaleIn 0.3s ease-out',
        'pulse-soft': 'pulseSoft 2s ease-in-out infinite',
        'spin-slow': 'spin 3s linear infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(24px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideDown: {
          '0%': { opacity: '0', transform: 'translateY(-12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        scaleIn: {
          '0%': { opacity: '0', transform: 'scale(0.95)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
        pulseSoft: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.6' },
        },
      },
      boxShadow: {
        card: '0 1px 2px rgba(61,57,41,0.04), 0 4px 20px rgba(61,57,41,0.05)',
        elevated: '0 2px 4px rgba(61,57,41,0.05), 0 16px 48px rgba(61,57,41,0.10)',
        composer: '0 2px 6px rgba(61,57,41,0.06), 0 12px 40px rgba(61,57,41,0.12)',
      },
    },
  },
  plugins: [],
};