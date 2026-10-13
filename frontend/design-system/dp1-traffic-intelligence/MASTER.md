# DP1 Traffic Intelligence — Master Design System

Generated via `ui-ux-pro-max` design-system workflow and calibrated with `Taste` and `emil-design-eng`.

## 1. Product & Architecture Identity
- **Product Type:** Intelligent Transportation System (ITS) & Simulation Operations Workspace
- **Pattern:** Data-Dense Dashboard + Drill-Down Inspector
- **Target Aesthetic:** High-agency, technical, operational precision (Air Traffic Control / Traffic Management Center aesthetic).
- **Core Philosophy:** Unseen details compound; no decorative slop, no fake maps, no emojis, no meaningless gradient fills. Data integrity is visual priority #1.

---

## 2. Color Palette & Semantics

| Token | Role | Hex Value | Usage / Semantic Purpose |
|---|---|---|---|
| `--bg-base` | Canvas Background | `#0B0F17` | Deep technical slate background (reduces eye strain during operations) |
| `--bg-surface` | Card / Panel Surface | `#111827` | Neutral surface for operational modules |
| `--bg-surface-elevated` | Popover / Modal Surface | `#1E293B` | Elevated inspection overlay surface |
| `--border-subtle` | Standard Border | `rgba(255, 255, 255, 0.08)` | 1px crisp separation; no heavy solid borders |
| `--border-active` | Focus / Selected Border | `rgba(59, 130, 246, 0.5)` | Active state indicator |
| `--text-primary` | Primary Content | `#F8FAFC` | High contrast (15:1+), primary headings, metrics |
| `--text-secondary` | Labels / Descriptions | `#94A3B8` | Clear WCAG AA 4.5:1+ contrast on panels |
| `--text-muted` | Metadata / Timestamp | `#64748B` | Provenance tags, seed identifiers |
| `--signal-green` | Traffic Green / Arrived | `#10B981` | Active green phase, improved delta, arrived vehicles |
| `--signal-yellow` | Traffic Yellow / Clearance | `#F59E0B` | Active yellow phase (3s warning), moderate queue |
| `--signal-red` | Traffic Red / Clearance Red | `#EF4444` | Active all-red clearance (2s), emergency vehicle, congested queue |
| `--accent-primary` | Operations Primary | `#3B82F6` | Primary action buttons, active tab pill |
| `--accent-secondary` | Axis EW Indicator | `#60A5FA` | East-West queue lines, secondary series |
| `--accent-tertiary` | Axis NS Indicator | `#38BDF8` | North-South queue lines |
| `--emergency-accent` | Emergency Vehicle | `#DC2626` | High-priority ambulance indicator, siren highlight |

---

## 3. Typography & Hierarchy

- **Primary Typeface:** `Geist Sans`, `Inter`, or `system-ui` (clean geometric sans-serif for high legibility).
- **Monospace Typeface:** `JetBrains Mono`, `Fira Code`, or `ui-monospace` (used for all numeric metrics, timestamps, seeds, and queue lengths).
- **Type Scale:**
  - `Display / KPI`: `2rem` (32px), `font-weight: 700`, `letter-spacing: -0.02em` (tabular numbers).
  - `Section Heading (H2)`: `1.25rem` (20px), `font-weight: 600`, `letter-spacing: -0.01em`.
  - `Subheading (H3)`: `0.9375rem` (15px), `font-weight: 600`.
  - `Body`: `0.875rem` (14px), `line-height: 1.5`, `color: var(--text-secondary)`.
  - `Micro / Badge`: `0.75rem` (12px), `font-weight: 500`, uppercase, tracking +0.05em.

---

## 4. Spacing, Layout, & Density

- **Density:** 7/10 (High density, space-efficient, maximum operational visibility without clutter).
- **Grid Structure:** CSS Grid (`grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4`), avoid percentage flex math.
- **Max Container Width:** `max-w-[1600px] mx-auto px-4 md:px-6`.
- **Card Materiality:**
  - `background: var(--bg-surface)`
  - `border: 1px solid var(--border-subtle)`
  - `border-radius: 8px` (clean engineering radius, not bulbous 24px)
  - `box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3)`

---

## 5. Animation & Interaction Framework (`emil-design-eng`)

- **Duration:** 150ms – 200ms for micro-interactions (hover, focus, tab change); 300ms for modal/drawer transitions.
- **Easing:** `cubic-bezier(0.16, 1, 0.3, 1)` (snappy ease-out, starts fast, arrives gently).
- **Motion Purpose:** Only animate to communicate state change or spatial continuity:
  - Telemetry updates: pulse signal indicator gently on state changes.
  - Buttons: `transform: scale(0.98)` on `:active` for tactile push feedback.
  - No continuous decorative bouncing, no animated hero text.
- **Accessibility:** Mandatory `@media (prefers-reduced-motion: reduce) { * { transition-duration: 0.01ms !important; animation-duration: 0.01ms !important; } }`.

---

## 6. Strict Banned Anti-Patterns

1. **NO EMOJIS:** All indicators and buttons use SVG primitives or Lucide icons (`Check`, `AlertTriangle`, `Play`, `Square`, `ArrowRight`).
2. **NO FAKE MAPS:** No static satellite pictures or decorative map tiles that do not reflect simulated detector data.
3. **NO FABRICATED METRICS:** In read-only snapshot mode, clearly label the dataset with source timestamp and disable live controls.
4. **NO INTER ARBITRARY GRADIENTS:** No purple/magenta glows. Clean technical slate and emerald/amber/crimson signal indicators only.
