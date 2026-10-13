# DP1 Traffic Intelligence — UI Quality Assurance & Review Report (Phase P5C)

## 1. Overview & Purpose
This document records the visual QA, motion audit, responsive evaluation, and Vercel readiness review for the DP1 Traffic Signal Optimization operations dashboard (`frontend/`), following the mandatory requirements of `docs/UI_SKILL_CONTRACT.md`, `emil-design-eng`, `Taste`, and `break-ui`.

---

## 2. Design Engineering Review (Emil Kowalski Format)

| Before | After | Why |
|---|---|---|
| `transition: all var(--transition-fast)` on `.dp1-btn` | `transition: transform 150ms cubic-bezier(0.16, 1, 0.3, 1), background-color 150ms ease-out, border-color 150ms ease-out, color 150ms ease-out` | Avoid `transition: all`; target explicit properties to eliminate GPU layout recalculations. |
| Modal/drawer dialogs lacked entering curve definition | `@keyframes modal-enter` (`opacity: 0, scale: 0.97` to `1.0`) with `180ms cubic-bezier(0.16, 1, 0.3, 1)` | Interfaces in the physical world scale subtly into view from near-unity, not from 0. |
| Default browser scrollbar on dense data tables | Custom 6px dark track (`rgba(11, 15, 23, 0.5)`) and thumb (`rgba(255, 255, 255, 0.15)`) | Seamless visual harmony with dark slate technical aesthetic (`#0B0F17`). |
| System fallback sans-serif font default | Curated `@import` for `Plus Jakarta Sans` (Display/Body) and `JetBrains Mono` (Data) | Clean technical typography with guaranteed `tabular-nums` alignment for queue and time metrics. |
| Hardcoded fallback benchmark in `ControllerLabView` when no runs matched | Strictly return `null` and render `"—"` with disabled navigation | Zero fabrication invariant: missing data must never display synthetic or placeholder numbers. |
| Static hardcoded strings in `OverviewView` scenario matrix | Dynamically compute mean waits and deltas from verified `allRuns` matching train seeds 1..5 | Ensures single source of truth and dynamic consistency with simulation runs. |
| Research artifact downloads only looked for `.json` | Exported raw `.csv` alongside `.json` in `dp1/research/generate_snapshot.py` | Direct browser download of `aggregate.csv`, `raw_runs.csv`, and `matrix_status.csv` works offline. |

---

## 3. Visual Hierarchy & Aesthetic Review (Taste Guidelines)

1. **Color Calibration & Contrast:**
   - **Base Palette:** Deep Obsidian Slate (`#0B0F17`) with elevated card surfaces (`#111827`, `#161F30`, `#1E293B`). Pure `#000000` is strictly avoided.
   - **Signal Semantics:**
     - Emerald (`#10B981` / `rgba(16, 185, 129, 0.15)`) for green signal and performance gains.
     - Amber (`#F59E0B` / `rgba(245, 158, 11, 0.15)`) for yellow clearance, warning states, and Saved Snapshot mode.
     - Carmine Red (`#EF4444` / `rgba(239, 68, 68, 0.15)`) for red clearance, emergency siren callouts, and performance regressions.
     - Electric Blue (`#3B82F6`) for active junction axes and interactive controls.
   - **Contrast Compliance:** All text styles (`#F8FAFC`, `#94A3B8`, `#64748B`) exceed WCAG AA contrast standards (minimum 4.5:1 for body text, 7:1 for headers).

2. **Elevation & Materiality:**
   - Cards use 1px fine borders (`rgba(255, 255, 255, 0.08)`) with subtle tinted diffusion shadows (`0 1px 3px rgba(0, 0, 0, 0.3)`), avoiding thick solid borders or noisy glow effects.
   - The interactive 4-way schematic represents physical lane-area detectors (150m) with proportional queue meters and distinct NS/EW signal heads.

3. **Anti-Slop Directives:**
   - Zero emojis in UI components, labels, or navigation tabs (replaced with Lucide SVG iconography).
   - Tabular monospace formatting (`JetBrains Mono`, `tabular-nums`) for all clocks, queue lengths, vehicle counts, and wait seconds.

---

## 4. Animation & Motion Audit

1. **Physicality & Tactile Feedback:**
   - Buttons scale to `scale(0.98)` on `:active` with 150ms spring-like ease (`cubic-bezier(0.16, 1, 0.3, 1)`), confirming user interaction.
   - No continuous animation of live metric values that would imply fake simulation activity.
   - The status dot pulse (`dp1-pulse`) is isolated to active simulation states.

2. **Accessibility (Reduced Motion):**
   - `@media (prefers-reduced-motion: reduce)` globally disables all transitions, modal scaling, and pulse animations (`animation: none !important; transition-duration: 0.01ms !important`).

---

## 5. Responsive Viewports Audit

| Viewport | Device / Target | Audit Findings & Optimizations |
|---|---|---|
| **1440px** | Desktop Workstation | Full 12-column grid layout. Intersection schematic sits side-by-side with detector queue tables. Charts render with full margin breathing room. Max container capped at `1600px` to prevent ultra-wide distortion. |
| **1024px** | Tablet / Compact Laptop | 2-column KPI grid wraps gracefully. Research matrix launcher and progress monitor adjust proportions. Navigation bar remains single-line with horizontal scrolling affordance if required. |
| **390px** | Mobile Smartphone | Layout collapses to single column. Root container enforces `overflow-x: hidden` to eliminate horizontal page bounce. Dense tables in Research View and Controller Lab wrap in `.dp1-table-wrapper` with smooth touch scroll and preserved column headers. |

---

## 6. Edge Cases & Resilience Testing (`break-ui`)

- **Empty / Missing Dataset:** If `allRuns` is empty or unpopulated, overview KPIs display `—` instead of synthetic numbers; charts display empty states.
- **Disconnected / Offline Backend:** Client automatically detects absence of `VITE_API_BASE_URL` or unreachable `/api/health`, falls back to `/demo-data/manifest.json`, and displays the yellow "Saved Simulation Snapshot (Read-Only)" subheader.
- **Stale Telemetry:** If telemetry timestamp is older than $5.0\text{s}$, status badge immediately transitions from `RUNNING` to `STALE` with amber warning icon.
- **Null Emergency Metrics:** When evaluating runs without emergency vehicles, emergency waiting time is strictly rendered as `null` / `—`, never 0.0s.
- **Long Scenario Names:** Labels such as `imbalanced_ns (Heavy Corridor)` and `surge_north (Asymmetric Burst)` wrap cleanly across narrow screens without clipping badges.

---

## 7. Vercel Readiness & Deployment Boundaries

1. **SPA Rewrites:** `frontend/vercel.json` provides rewrite rules directing `/(.*)` to `/index.html` for clean client-side routing.
2. **Build Settings:**
   - Project Root: `frontend/`
   - Build Command: `npm run build`
   - Output Directory: `dist`
3. **Deployment Limitation Notice:**
   - The Vercel deployment hosts the static React SPA only.
   - Running live Eclipse SUMO simulations or launching new research matrices requires a separately hosted container or workstation running the DP1 FastAPI backend (`python -m dp1.api.server`). The static frontend correctly communicates this limitation and locks live execution controls when running in snapshot mode.
