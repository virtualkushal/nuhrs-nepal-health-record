/** @type {import('tailwindcss').Config} */
// Design tokens shared with the NUHRS core platform (frontend-react).
//
// Colors are wired to CSS variables (RGB channel triplets) defined in index.css
// so the theme can be re-skinned by overriding the channels on a wrapper element
// — the patient portal uses a `.patient-theme` wrapper to switch to a blue/gold
// palette while every other dashboard keeps the default teal `:root` values.
// Channel form (`R G B`) is required so Tailwind's `/opacity` modifiers still
// compile to `rgb(... / <alpha>)`.
//
// The legacy `brand`/`surface`/`line` ramps are retained during the redesign
// transition so existing dark classes keep resolving; the page sweep migrates
// components onto the token system.
const c = (name) => `rgb(var(--color-${name}) / <alpha-value>)`;

export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        // NUHRS shared design tokens (Material-3 style, CSS-variable driven)
        primary: c("primary"),
        "on-primary": c("on-primary"),
        "primary-container": c("primary-container"),
        "on-primary-container": c("on-primary-container"),
        "primary-fixed": c("primary-fixed"),
        "primary-fixed-dim": c("primary-fixed-dim"),
        "on-primary-fixed": c("on-primary-fixed"),
        "on-primary-fixed-variant": c("on-primary-fixed-variant"),
        "inverse-primary": c("inverse-primary"),
        secondary: c("secondary"),
        "on-secondary": c("on-secondary"),
        "secondary-container": c("secondary-container"),
        "on-secondary-container": c("on-secondary-container"),
        "secondary-fixed": c("secondary-fixed"),
        "secondary-fixed-dim": c("secondary-fixed-dim"),
        "on-secondary-fixed": c("on-secondary-fixed"),
        "on-secondary-fixed-variant": c("on-secondary-fixed-variant"),
        tertiary: c("tertiary"),
        "on-tertiary": c("on-tertiary"),
        "tertiary-container": c("tertiary-container"),
        "on-tertiary-container": c("on-tertiary-container"),
        "tertiary-fixed": c("tertiary-fixed"),
        "tertiary-fixed-dim": c("tertiary-fixed-dim"),
        "on-tertiary-fixed": c("on-tertiary-fixed"),
        "on-tertiary-fixed-variant": c("on-tertiary-fixed-variant"),
        error: c("error"),
        "on-error": c("on-error"),
        "error-container": c("error-container"),
        "on-error-container": c("on-error-container"),
        background: c("background"),
        "on-background": c("on-background"),
        surface: c("surface"),
        "on-surface": c("on-surface"),
        "on-surface-variant": c("on-surface-variant"),
        "surface-bright": c("surface-bright"),
        "surface-dim": c("surface-dim"),
        "surface-variant": c("surface-variant"),
        "surface-container": c("surface-container"),
        "surface-container-low": c("surface-container-low"),
        "surface-container-lowest": c("surface-container-lowest"),
        "surface-container-high": c("surface-container-high"),
        "surface-container-highest": c("surface-container-highest"),
        "inverse-surface": c("inverse-surface"),
        "inverse-on-surface": c("inverse-on-surface"),
        outline: c("outline"),
        "outline-variant": c("outline-variant"),
        "surface-tint": c("surface-tint"),
        ok: c("ok"),
        warn: c("warn"),
        // Legacy PulseCore-inspired blue brand ramp (transition only)
        brand: {
          50: "#eff6ff",
          100: "#dbeafe",
          200: "#bfdbfe",
          300: "#93c5fd",
          400: "#60a5fa",
          500: "#3b82f6",
          600: "#2563eb",
          700: "#1d4ed8",
          800: "#1e3a8a",
          900: "#1e3a8a",
        },
        // Legacy dark navy surfaces (transition only)
        surface: {
          50: "#f8fafc",
          100: "#f1f5f9",
          200: "#e2e8f0",
          700: "#142740",
          750: "#0d1e36",
          800: "#0a1628",
          900: "#060e1f",
          950: "#030810",
        },
        line: "#1e3554",
      },
      spacing: {
        "margin-desktop": "32px",
        "margin-mobile": "16px",
        base: "8px",
        unit: "4px",
        "container-max": "1280px",
        gutter: "24px",
        "grid-gutter": "16px",
        "grid-margin": "24px",
        lg: "24px",
        md: "16px",
        sm: "8px",
        xs: "4px",
        xl: "32px",
        "stack-lg": "24px",
        "stack-md": "16px",
        "stack-sm": "8px",
        "stack-xs": "4px",
        "stack-xl": "40px",
      },
      maxWidth: { "container-max": "1280px" },
      fontFamily: {
        // Headline/display families read a CSS var so the patient theme can swap
        // to Plus Jakarta Sans without changing body/label text.
        display: ["var(--font-headline)", "sans-serif"],
        "headline-xl": ["var(--font-headline)", "sans-serif"],
        "headline-md": ["var(--font-headline)", "sans-serif"],
        "headline-lg": ["var(--font-headline)", "sans-serif"],
        "display-lg": ["var(--font-headline)", "sans-serif"],
        "title-lg": ["var(--font-headline)", "sans-serif"],
        "label-md": ["Inter", "sans-serif"],
        "label-sm": ["Inter", "sans-serif"],
        "body-md": ["Inter", "sans-serif"],
        "body-lg": ["Inter", "sans-serif"],
        body: ["Inter", "sans-serif"],
        sans: ["Inter", "sans-serif"],
      },
      fontSize: {
        "headline-xl": ["40px", { lineHeight: "48px", letterSpacing: "-0.02em", fontWeight: "700" }],
        "headline-md": ["24px", { lineHeight: "32px", fontWeight: "600" }],
        "label-md": ["14px", { lineHeight: "20px", letterSpacing: "0.01em", fontWeight: "500" }],
        "body-md": ["16px", { lineHeight: "24px", fontWeight: "400" }],
        "headline-lg": ["32px", { lineHeight: "40px", letterSpacing: "-0.01em", fontWeight: "600" }],
        "body-lg": ["18px", { lineHeight: "28px", fontWeight: "400" }],
        "label-sm": ["12px", { lineHeight: "16px", fontWeight: "600" }],
        "display-lg": ["48px", { lineHeight: "56px", letterSpacing: "-0.02em", fontWeight: "700" }],
        "title-lg": ["20px", { lineHeight: "28px", fontWeight: "600" }],
      },
      keyframes: {
        float: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-20px)" },
        },
        gradientMove: {
          "0%, 100%": { backgroundPosition: "0% 50%" },
          "50%": { backgroundPosition: "100% 50%" },
        },
      },
      animation: {
        float: "float 6s ease-in-out infinite",
        gradientMove: "gradientMove 15s ease infinite",
      },
    },
  },
  plugins: [],
};