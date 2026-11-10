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
        // Aurora UI — cool slate surfaces + blue accent. 'clay' is kept as an
        // alias of the primary blue so legacy components restyle automatically.
        paper: {
          DEFAULT: '#F8FAFC',
          elevated: '#FFFFFF',
          inset: '#F1F5F9',
          line: '#E2E8F0',
          hover: '#EEF2F7',
        },
        ink: {
          DEFAULT: '#0F172A',
          soft: '#475569',
          mute: '#64748B',
          faint: '#94A3B8',
        },
        clay: {
          DEFAULT: '#2563EB',
          soft: '#EFF6FF',
          line: '#DBEAFE',
          deep: '#1D4ED8',
        },
        primary: {
          DEFAULT: '#2563EB',
          soft: '#EFF6FF',
          line: '#DBEAFE',
          deep: '#1D4ED8',
          50: '#EFF6FF',
          100: '#DBEAFE',
          200: '#BFDBFE',
          300: '#93C5FD',
          400: '#60A5FA',
          500: '#3B82F6',
          600: '#2563EB',
          700: '#1D4ED8',
          800: '#1E40AF',
          900: '#1E3A8A',
        },
        secondary: {
          DEFAULT: '#0D9488',
          soft: '#F0FDFA',
          line: '#CCFBF1',
          deep: '#0F766E',
          400: '#2DD4BF',
          500: '#14B8A6',
          600: '#0D9488',
          700: '#0F766E',
        },
        surface: { DEFAULT: '#FFFFFF', card: '#FFFFFF', hover: '#F1F5F9' },
        success: '#16A34A',
        warning: '#D97706',
        danger: '#DC2626',
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
          '50%': { opacity: '0.55' },
        },
      },
      boxShadow: {
        card: '0 1px 2px rgba(15,23,42,0.05), 0 4px 20px rgba(15,23,42,0.06)',
        elevated: '0 2px 4px rgba(15,23,42,0.06), 0 18px 48px rgba(15,23,42,0.12)',
        composer: '0 2px 6px rgba(15,23,42,0.08), 0 16px 48px rgba(15,23,42,0.14)',
      },
    },
  },
  plugins: [],
};