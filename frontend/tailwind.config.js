/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      // ── Fonts ──────────────────────────────────────────────────────────────
      fontFamily: {
        display: ['"Plus Jakarta Sans"', 'sans-serif'],
        body:    ['"DM Sans"', 'sans-serif'],
        sans:    ['"DM Sans"', 'sans-serif'],  // override Tailwind default
      },

      // ── Color tokens ───────────────────────────────────────────────────────
      colors: {
        neu: {
          base:         '#E0E5EC',   // page + card background — everything is this
          fg:           '#3D4852',   // primary text  (7.5:1 contrast — AAA)
          muted:        '#6B7280',   // secondary text (4.6:1 contrast — AA)
          accent:       '#6C63FF',   // violet CTA
          'accent-lt':  '#8B84FF',   // lighter violet for hover
          teal:         '#38B2AC',   // success / positive indicator
          'risk-hi':    '#EF4444',
          'risk-md':    '#F59E0B',
          'risk-lo':    '#10B981',
        },
      },

      // ── Border radius ──────────────────────────────────────────────────────
      borderRadius: {
        neu:    '32px',   // cards / containers
        'neu-sm': '16px', // buttons / inputs / smaller elements
      },

      // ── Box shadows (the core of the neumorphic system) ────────────────────
      // All shadows use rgba so they blend naturally with the #E0E5EC surface.
      // Light source: top-left  →  white highlight
      // Shadow falls: bottom-right  →  cool blue-grey
      boxShadow: {
        // Extruded — element rises from the surface
        'neu-out':    '9px 9px 16px rgb(163,177,198,0.6), -9px -9px 16px rgba(255,255,255,0.5)',
        // Lifted — hover state, deeper raise
        'neu-out-lg': '12px 12px 20px rgb(163,177,198,0.7), -12px -12px 20px rgba(255,255,255,0.6)',
        // Small extruded — for stat cards, badges, small elements
        'neu-out-sm': '5px 5px 10px rgb(163,177,198,0.6), -5px -5px 10px rgba(255,255,255,0.5)',
        // Inset — element carved into the surface (inputs, wells)
        'neu-in':     'inset 6px 6px 10px rgb(163,177,198,0.6), inset -6px -6px 10px rgba(255,255,255,0.5)',
        // Deep inset — focused inputs, deep wells
        'neu-in-lg':  'inset 10px 10px 20px rgb(163,177,198,0.7), inset -10px -10px 20px rgba(255,255,255,0.6)',
        // Small inset — pills, track elements, pressed state on small buttons
        'neu-in-sm':  'inset 3px 3px 6px rgb(163,177,198,0.6), inset -3px -3px 6px rgba(255,255,255,0.5)',
        // Primary button active — works on colored (violet) background
        'neu-btn-active': 'inset 4px 4px 8px rgba(0,0,0,0.2), inset -2px -2px 4px rgba(255,255,255,0.12)',
      },

      // ── Keyframes ──────────────────────────────────────────────────────────
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%':      { transform: 'translateY(-8px)' },
        },
        'fade-in': {
          '0%':   { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
      animation: {
        float:    'float 3s ease-in-out infinite',
        'fade-in': 'fade-in 0.4s ease-out forwards',
      },
    },
  },
  plugins: [],
}
