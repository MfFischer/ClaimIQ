/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50:  '#EBF2FB',
          100: '#C3D9F4',
          200: '#9BC0ED',
          300: '#74ADE8',
          400: '#4D91DC',
          500: '#2D72C0',
          600: '#1A56A0',
          700: '#144280',
          800: '#0F3363',
          900: '#081F3D',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      animation: {
        'fade-in':    'fadeIn 0.5s ease-out both',
        'fade-up':    'fadeUp 0.55s ease-out both',
        'slide-up':   'slideUp 0.4s ease-out both',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'float':      'float 3.5s ease-in-out infinite',
        'scale-in':   'scaleIn 0.35s cubic-bezier(0.34, 1.56, 0.64, 1) both',
        'glow-pulse': 'glowPulse 2.5s ease-in-out infinite',
        'shimmer':    'shimmer 2.5s infinite',
        'counter':    'counterUp 1.5s ease-out both',
        'beam':       'beam 3s ease-in-out infinite',
      },
      keyframes: {
        fadeIn:    { from: { opacity: '0' }, to: { opacity: '1' } },
        fadeUp:    { from: { opacity: '0', transform: 'translateY(20px)' }, to: { opacity: '1', transform: 'translateY(0)' } },
        slideUp:   { from: { opacity: '0', transform: 'translateY(14px)' }, to: { opacity: '1', transform: 'translateY(0)' } },
        float:     { '0%,100%': { transform: 'translateY(0)' }, '50%': { transform: 'translateY(-10px)' } },
        scaleIn:   { from: { opacity: '0', transform: 'scale(0.88)' }, to: { opacity: '1', transform: 'scale(1)' } },
        glowPulse: {
          '0%,100%': { boxShadow: '0 0 20px rgba(26,86,160,0.25)' },
          '50%':     { boxShadow: '0 0 40px rgba(26,86,160,0.5), 0 0 60px rgba(77,145,220,0.2)' },
        },
        shimmer: {
          from: { backgroundPosition: '-200% center' },
          to:   { backgroundPosition: '200% center' },
        },
        beam: {
          '0%,100%': { opacity: '0.3', transform: 'scaleY(0.8)' },
          '50%':     { opacity: '1',   transform: 'scaleY(1)' },
        },
      },
      boxShadow: {
        'glow':    '0 0 28px rgba(26,86,160,0.3)',
        'glow-lg': '0 0 50px rgba(26,86,160,0.35), 0 0 80px rgba(77,145,220,0.15)',
        'card':    '0 1px 4px rgba(0,0,0,0.04), 0 4px 16px rgba(0,0,0,0.05)',
        'card-md': '0 2px 8px rgba(0,0,0,0.05), 0 8px 28px rgba(0,0,0,0.07)',
        'card-lg': '0 4px 16px rgba(0,0,0,0.06), 0 16px 48px rgba(0,0,0,0.09)',
      },
    },
  },
  plugins: [],
}
