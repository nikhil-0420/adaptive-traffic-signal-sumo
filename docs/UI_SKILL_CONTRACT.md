# Mandatory Antigravity UI Skill Contract — DP1 Dashboard

This contract applies to every implementation or visual-refinement task touching `frontend/`. These skills are not optional suggestions and must be invoked, read and applied by the Antigravity agent:

- `ui-ux-pro-max` — design system, product/dashboard pattern, color, typography, chart choice, React-specific and accessibility guidance.
- `Taste` — premium design taste and aesthetic judgment.
- `emil-design-eng` — animation and design-engineering principles from `emilkowalski/skills`.
- The associated installed `emilkowalski/skills` UI/animation skills, especially `pick-ui-library`, `find-animation-opportunities`, `animate`, `review-animations`, `improve-animations` and `break-ui`; also discover and use any installed React/layout/interaction/microinteraction skills that are directly relevant rather than assuming this list is exhaustive.

## Required workflow

1. **Resolve the actual installed skill locations.** Search the IDE's installed skill catalog and project/agent skill directories. Read the actual `SKILL.md` and any references required by those skills. Do not guess file paths or pretend a skill ran.
2. **Run ui-ux-pro-max's design-system process before implementing the visual UI.** Read its `SKILL.md`, inspect the installed version's CLI help, and run the documented `--design-system` workflow with a query focused on an intelligent traffic-operations/results dashboard and the React stack. Persist the master design system plus page-specific overrides within this repository. Read the generated files before writing components. Run its React stack guidance and relevant chart/UX guidance where supported by that installed version.
3. **Use Taste for product-level choices.** Evaluate hierarchy, whitespace, layout proportions, type, color, depth, contrast, and visual signature. Avoid mechanical card grids and a template-like result. Do not just cite Taste in the final response.
4. **Use emil-design-eng while coding motion.** Before introducing UI libraries, invoke `pick-ui-library` if installed. Run `find-animation-opportunities` and only animate elements where motion explains a change. Use `animate` to choose properties, easing, duration and choreography for substantial motion. Then run `review-animations`; use `improve-animations` to get a self-contained remediation plan when needed. Run `break-ui` against edge cases. Read the installed skill instructions first and follow their exact invocation conventions.
5. **Implement against a reusable design system.** Persist color, type, spacing, radius, shadow/surface and easing/duration tokens. Use page/component overrides only when they have a real reason. Use real project results in charts and labels. A premium UI is not just gradients, large rounded cards or animation. Use `emil-design-eng` and the installed `emilkowalski/skills` companions to make explicit choices about easing curves, duration, shadows, layout proportions, focus/press states and chart transitions; do not invent skill invocations or assume subskill names without inspecting the installed package.
6. **Record evidence.** Create `docs/UI_SKILL_EXECUTION.md` with: skill names/paths read; exact commands invoked and their actual outputs or summary; design-system artifact paths; selected UI/chart/motion libraries and why; what changed based on Taste; `review-animations`/`break-ui` findings and fixes. Create `docs/UI_QA_REPORT.md` after the final review with viewports and outstanding issues. Do not copy complete skill files into these reports.

## Visual and motion acceptance criteria

- Specific visual identity appropriate for a research-grade traffic simulation, not a generic admin or “AI dashboard” template.
- Clear reading order between current run/signal state, key operational metrics, controller comparisons and detailed traces.
- The Research & Evaluation page must make matrix coverage, selected demand level, policy, seed count, paired deltas/intervals and directional fairness understandable without turning into an unreadable spreadsheet. Use readable uncertainty cues and visibly label incomplete experiments.
- Deliberate proportions and density: charts readable at desktop widths, filters and critical statuses still useful at mobile width, tables handle overflow intentionally.
- Thoughtful depth using surface contrast, fine/transparent borders and restrained layered shadows rather than heavy solid borders on every card. Avoid using shadows on every element indiscriminately.
- Every animation has a purpose, correctly chosen easing/duration, no unnecessary bouncing, no fake activity, no excessive stagger, and no animation implying metric changes that did not happen.
- `prefers-reduced-motion` is respected. Keyboard focus, semantic controls, contrast and accessible labels are tested.
- Loading, empty, error, disconnected, stale, saved-snapshot, live, completed, and failed states are visually and semantically distinct.
- No screenshot, claim, metric, or demo content is presented as live unless generated by an active API session.

## If a skill is missing

Search all available installed-skill directories/catalogs and check the exact package installation status. If still unavailable, document the missing skill clearly in `docs/UI_SKILL_EXECUTION.md`, do not claim compliance, and continue only with the remaining available skills if necessary to avoid blocking non-visual work. The user asked for these skills specifically, so do not silently replace them with generic prompting.
