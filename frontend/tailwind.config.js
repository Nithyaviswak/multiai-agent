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
        // Warm paper + deep charcoal palette. 'clay' is kept as an alias of the
        // primary indigo so legacy components restyle automatically.
        paper: {
          DEFAULT: '#F6F5F2',
          elevated: '#FFFFFF',
          inset: '#ECEAE4',
          line: '#E3E0D8',
          hover: '#F0EEE9',
        },
        ink: {
          DEFAULT: '#161B26',
          soft: '#4A5468',
          mute: '#7C8798',
          faint: '#A8B0BF',
        },
        clay: {
          DEFAULT: '#4F46E5',
          soft: '#EEF0FE',
          line: '#DFE1FB',
          deep: '#4338CA',
        },
        primary: {
          DEFAULT: '#4F46E5',
          soft: '#EEF0FE',
          line: '#DFE1FB',
          deep: '#4338CA',
          50: '#EFF0FE',
          100: '#E2E4FB',
          200: '#C7CBF8',
          300: '#A5A8F3',
          400: '#8186F0',
          500: '#6366F1',
          600: '#4F46E5',
          700: '#4338CA',
          800: '#3730A3',
          900: '#312E81',
        },
        secondary: {
          DEFAULT: '#0F766E',
          soft: '#EDFBF8',
          line: '#CFF3EC',
          deep: '#115E59',
          400: '#14B8A6',
          500: '#0D9488',
          600: '#0F766E',
          700: '#115E59',
        },
        surface: { DEFAULT: '#FFFFFF', card: '#FFFFFF', hover: '#F0EEE9' },
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
        card: '0 1px 2px rgba(22,27,38,0.04), 0 4px 20px rgba(22,27,38,0.05)',
        elevated: '0 2px 4px rgba(22,27,38,0.05), 0 18px 48px rgba(22,27,38,0.10)',
        composer: '0 2px 6px rgba(22,27,38,0.06), 0 16px 48px rgba(22,27,38,0.12)',
      },
    },
  },
  plugins: [],
};