# UI Skill Execution Evidence Trail

This document records the exact skills read, commands executed, library choices, and design rationale applied for the DP1 Frontend Dashboard according to `docs/UI_SKILL_CONTRACT.md`.

---

## 1. Skills Read & Executed

| Skill | Installed Path | Procedure & Output |
|---|---|---|
| `ui-ux-pro-max` | `C:\Users\ACER.DESKTOP-R4G9UL6\.gemini\config\skills\ui-ux-pro-max\SKILL.md` | Inspected `scripts/search.py --help`. Executed: `python search.py "traffic operations intelligent transportation simulation dashboard" --design-system -p "DP1 Traffic Intelligence" -f markdown`. Output persisted to `frontend/design-system/dp1-traffic-intelligence/MASTER.md`. Also searched `stacks/react.csv` and `charts.csv`. |
| `Taste` (`gpt-taste` & `design-taste-frontend`) | `C:\Users\ACER.DESKTOP-R4G9UL6\.gemini\config\skills\gpt-taste\SKILL.md`, `.../design-taste-frontend\SKILL.md` | Applied strict anti-cliché rules: banned purple AI gradients and arbitrary pill tags; enforced dark technical slate canvas (`#0B0F17`) with emerald/amber/crimson signal semantics, monospace tabular figures (`JetBrains Mono`), 1px subtle borders (`rgba(255,255,255,0.08)`), and CSS grid layout over fragile flex math. Banned emojis in UI. |
| `emil-design-eng` | `C:\Users\ACER.DESKTOP-R4G9UL6\.gemini\config\skills\emil-design-eng\SKILL.md` | Read `references/detailed-guide.md`. Adopted animation decision framework: only animate state indications and spatial continuity; snappy 150-200ms `ease-out` transitions; `:active` tactile push (`scale(0.98)`); no bouncing/frivolous motion; mandatory `prefers-reduced-motion` support. |
| `pick-ui-library` | `C:\Users\ACER.DESKTOP-R4G9UL6\.gemini\antigravity\scratch\.agents\skills\pick-ui-library\SKILL.md` | Selected opinionated, minimal dependencies: **Recharts** for timeseries/comparison dashboards, **Lucide-react** for clean SVG icons, **Sonner** for notifications, and **clsx** for classnames. Banned redundant heavy component libraries. |
| `break-ui` | `C:\Users\ACER.DESKTOP-R4G9UL6\.gemini\antigravity\scratch\.agents\skills\break-ui\SKILL.md` | Identified adversarial test cases to handle: zero items, null metrics, very long scenario identifiers, offline/disconnected backend state, and missing artifact files. |

---

## 2. Design System Artifacts Generated

- `frontend/design-system/dp1-traffic-intelligence/MASTER.md`: Master design tokens, typography, colors, layout rules, and anti-patterns.
- `frontend/design-system/dp1-traffic-intelligence/overview.md`: Operations overview workspace guidance.
- `frontend/design-system/dp1-traffic-intelligence/controller-lab.md`: Policy comparison lab guidelines.
- `frontend/design-system/dp1-traffic-intelligence/run-explorer.md`: Individual run queue timeseries and decision inspector.
- `frontend/design-system/dp1-traffic-intelligence/research-evaluation.md`: Matrix evaluation workspace with 95% bootstrap CIs and directional fairness.
- `frontend/design-system/dp1-traffic-intelligence/live-monitor.md`: Real-time junction SVG schematic and atomic telemetry.

---

## 3. Library Selection Rationale (`pick-ui-library`)

- **Frontend Framework:** React 18 + Vite (JavaScript / JSX, strictly no TypeScript/TSX per prompt).
- **Charts:** `recharts` — standard for dashboard metrics, timeseries queue lengths, and confidence intervals.
- **Icons:** `lucide-react` — clean, accessible SVG icons; zero emojis.
- **Styling:** Vanilla CSS design tokens with Tailwind CSS utility classes and `clsx`.
- **Notifications:** `sonner` — lightweight, accessible toast system.

---

## 4. Visual & Animation Review Findings

| Before | After | Why |
|---|---|---|
| Generic cards with heavy solid borders | Dark slate panel (`#111827`) with `1px rgba(255,255,255,0.08)` border | Elevated technical feel; prevents card clutter in data-dense layouts. |
| Emoji icons in navigation (🚦, 📈) | Accessible SVG icons from `lucide-react` | Professional ITS operations standard. |
| Missing metrics displaying as `0` | Explicitly rendered as `"—"` (null/unavailable) | Scientific integrity; avoids falsely claiming zero wait time or queue. |
| Static status text | Live pulsing indicator with automatic 5s staleness detection | Clear operational visibility of simulation lifecycle. |
| Linear slow transitions | `150ms cubic-bezier(0.16, 1, 0.3, 1)` ease-out | Snappy, responsive interaction without feeling sluggish. |

---

## 5. Phase 7B: Marathahalli Real-Road Site Model Integration

Following the design system tokens, anti-cliché guidelines, and micro-animation standards, Phase 7B adds:

1. **`SiteModelView.jsx` Workspace:**
   - **Topology & SUMO Render Tab:** High-resolution network schematic alongside SUMO GUI renders (`/network/marathahalli/marathahalli_network_topology.png`, `sumo_gui_render.png`).
   - **3-Tier Grade Separation Tab:** Detailed architectural cards explaining the elevated flyover (HAL Rd <-> Whitefield, 4 lanes, 60 km/h, 70% bypass), ORR mainline underpass (K.R. Puram <-> Sarjapur, 6 lanes, 70% bypass), and surface signal junction (`marathahalli_tls`, turning traffic & bus transit).
   - **Phasing Machine & Detectors Tab:** Interactive breakdown of the 6-phase cycle with exact 16-character SUMO state strings, 3.0s yellow (`yyygrrrryyygrrrr`), 2.0s all-red clearance (`rrrrrrrrrrrrrrrr`), and induction/lane-area detector locations.
   - **Data Grounding & Provenance Matrix Tab:** Rigorous scientific transparency table distinguishing verified inputs (BTP Marathahalli Yamlur PDF signal plan, OpenCity municipal GIS lane widths, OSM alignment) from synthetic assumptions (unmeasured vehicle demand volumes).

2. **Network Switchers Across Workspaces:**
   - **Navbar:** Added `Site Model` navigation item with active route indicator.
   - **`LiveMonitorView.jsx`:** Network selector enabling users to switch between Synthetic 4-Way and Marathahalli Bridge Site, dynamically swapping available scenarios (`balanced`, `imbalanced_orr`, `imbalanced_varthur`, `surge_orr_north`).
   - **`ResearchView.jsx`:** Matrix Experiment Launcher supports `--network marathahalli` and displays site matrix presets (600 cells) alongside synthetic presets (720 cells).

