export const colors = {
  background: "oklch(0.985 0.003 95)", // #F7F7F5
  foreground: "oklch(0.27 0.02 265)", // #1F2937 ink
  ink: "oklch(0.27 0.02 265)",
  subtext: "oklch(0.55 0.015 260)", // #6B7280
  hairline: "oklch(0.27 0.02 265 / 0.08)",
  
  brand: {
    beige: "oklch(0.945 0.018 75)", // #F4EDE4
    rose: "oklch(0.87 0.035 25)", // #E8CFCB
    pista: "oklch(0.9 0.04 150)", // #CFE4D3
    lavender: "oklch(0.87 0.04 295)", // #DCD7F8
  },
  
  semantic: {
    info: "oklch(0.83 0.04 265)", // #BFC8E8
    success: "oklch(0.79 0.07 150)", // #9BC5A2
    warning: "oklch(0.85 0.08 75)", // #EBCFA7
    risk: "oklch(0.76 0.08 25)", // #D9A6A6
  },
  
  ui: {
    card: "oklch(1 0 0)",
    cardForeground: "var(--ink)",
    popover: "oklch(1 0 0)",
    popoverForeground: "var(--ink)",
    primary: "oklch(0.27 0.02 265)",
    primaryForeground: "oklch(0.985 0.003 95)",
    secondary: "var(--beige)",
    secondaryForeground: "var(--ink)",
    muted: "oklch(0.96 0.005 90)",
    mutedForeground: "var(--subtext)",
    accent: "var(--lavender)",
    accentForeground: "var(--ink)",
    destructive: "var(--risk)",
    destructiveForeground: "oklch(0.27 0.02 265)",
    border: "oklch(0.27 0.02 265 / 0.08)",
    input: "oklch(0.27 0.02 265 / 0.12)",
    ring: "oklch(0.6 0.04 260)",
  },

  charts: {
    chart1: "var(--info)",
    chart2: "var(--pista)",
    chart3: "var(--lavender)",
    chart4: "var(--warning)",
    chart5: "var(--rose)",
  },

  sidebar: {
    background: "oklch(0.97 0.005 90)",
    foreground: "var(--ink)",
    primary: "var(--ink)",
    primaryForeground: "oklch(0.985 0.003 95)",
    accent: "oklch(0.94 0.01 90)",
    accentForeground: "var(--ink)",
    border: "var(--hairline)",
    ring: "var(--ring)",
  }
};
