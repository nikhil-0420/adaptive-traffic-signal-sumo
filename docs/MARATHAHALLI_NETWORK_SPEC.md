# Deferred Phase 7A/7B — Marathahalli Bridge Site-Network Reconstruction Specification

**Sequencing gate:** This specification must not be executed until the full synthetic-network upgrade P0–P6 has been implemented, verified, documented and frozen. This is an engineering build specification for a later extension, not a reason to delay the current DQN, emergency priority, research evaluation, FastAPI, React/Vite/JSX dashboard, design QA or Vercel work.

**Purpose:** After P6 is complete, add a separate SUMO model grounded in the road layout around Marathahalli Bridge, Varthur Road and Outer Ring Road (ORR), Bengaluru. Do not replace the synthetic network or overwrite its results. This is not a claim that exact lane-level geometry or signal timing has already been verified.

## 1. Non-negotiable interpretation

Before Phase 7A, the project intentionally continues to use its existing synthetic four-way road for the initial upgrade. After P6, the intended additional model is a **site-grounded Marathahalli Bridge network**, constructed from available geospatial data and cross-checked against map views. The existing generated synthetic junction must remain available as the original regression/reference network and must not be deleted or replaced.

Important: OpenCity datasets are useful but do not automatically provide a complete traffic-engineering model. The BBMP Roads Centerline Map represents the geographic centre of roads; the Bengaluru Road Width Map describes road width. Neither description guarantees lane-level geometry, permitted turns, elevation/grade separation, signal-head placement, pedestrian phases, or current controller timing. Those items require corroboration and must have a source/confidence label.

## 2. Source-first workflow

Start from OpenCity's available Bengaluru datasets:

- **BBMP Roads Centerline Map** (KML): https://data.opencity.in/dataset/bbmp-roads-centerline-map
- **Bengaluru Road Width Map** (KML): https://data.opencity.in/dataset/bengaluru-road-width-map
- **Bengaluru Ward-wise Street Map** (CSV/KML; use the relevant Marathahalli ward/streets when useful): https://data.opencity.in/dataset/bengaluru-ward-wise-street-map

Use the OpenCity map/data view to identify and inspect the target area. Prefer downloadable geospatial vectors and attributes over tracing a screenshot when they are available. Record access date, dataset title, provider, URL, published update date if shown, licence/usage note, local filename, and any transformations performed.

Cross-check road connectivity and road hierarchy with a current road-map layer (for example OpenStreetMap where available), aerial/satellite imagery, relevant project documents already in `docs/`, and the available Bengaluru Traffic Police timing document. Use each source only for facts it can support. A road-centreline source is not proof of lane count; a timing document is not proof that every visible node shares that timing plan.

If Antigravity cannot download or inspect a required dataset, do not fabricate the missing geometry. Stop at a clear blocker, report the exact URL/action that failed, and ask the project owner to provide the downloaded KML/KMZ/CSV or a screenshot/export from the site view. Continue independent tasks only where safe.

## 3. Required geography and topology review

Inspect the road layout around **Marathahalli Bridge / Varthur Road × Outer Ring Road**, not just a four-arm cross. Existing public descriptions indicate grade-separated roads and connecting/service-road movements in this area; validate the current arrangement against present map evidence instead of treating this old description as ground truth. Specifically record whether the model extent contains:

- The Varthur Road bridge/overpass and the ORR below/adjacent to it.
- Service roads, ramps/connectors, merges/diverges and U-turn links visible in the chosen extent.
- Actual at-grade intersections, their stop lines, and traffic-signal locations (only where supported by evidence).
- Directional flow, road widths, known lane counts, lane changes, turn movements and speed limits where source data supports them.
- Pedestrian crossings/footpaths or exclusive pedestrian stages when they are relevant and verified.

A grade-separated crossing must not be modelled as a conflict junction simply because two road shapes cross on a 2D map. Keep the topologies disconnected where vehicles cannot move between levels; visual z/height alone is not a substitute for correct connectivity. Include ramps/connectors only where the road evidence supports them.

## 4. Scope control for a few-week implementation

Model the **surrounding road network at realistic topology** but start control experiments at **one verified signal-controlled junction/node (or one documented signal group)** selected from the site evidence. This controls schedule risk while allowing realistic approach routes and queue spillback. Do not make every junction signal-controlled by default. Do not claim to have reproduced the entire interchange or a real timing plan unless the network and signal phases have been evidenced.

During deferred Phase 7A, before code generation, produce `docs/MARATHAHALLI_NETWORK_AUDIT.md` containing:

1. A screenshot/export of the OpenCity/map view with the study extent marked (for reviewer orientation, not as the only geometry source).
2. A topology diagram and edge/node inventory.
3. A table of important roads with direction, approximate width, lane-count value or `unknown`, turn connectivity, grade/level, source, confidence (`verified`, `inferred`, `unknown`) and rationale.
4. A signal-node inventory: location, controlled movements, phase groups, clearance times, source, confidence, and any unresolved items.
5. The chosen first control node and why it is appropriate for adaptive control.
6. A list of assumptions and what would change if a better source becomes available.

Never silently turn `unknown` into a guessed fact. A defensible explicitly documented assumption is preferable to fake precision.

## 5. SUMO network implementation contract

- Keep the current network as `synthetic` (or equivalent), with current CLI behavior available for regression checks.
- Add an explicit network selector, e.g. `--network synthetic|marathahalli`, with `synthetic` as the backward-compatible default until site-network acceptance tests pass.
- Store the new network and configuration in a clear site-specific location such as `network/marathahalli/` or an equivalent structure justified by current conventions. Keep original source data, transformed/trimmed study-area inputs, and generated SUMO files clearly distinguished.
- Build generated SUMO networks using supported import/generation tools (`netconvert`, OSM import, or a documented source-vector conversion pipeline). Do not hand-edit generated `*.net.xml` files; fix source data/config and regenerate.
- Where the current `dp1/network.py` can no longer describe the real network, separate network loading/generation from the controller logic rather than contorting the real map into the synthetic 4-way template.
- Ensure routes are connected and legal. Add realistic turn/movement options based on map topology. Keep vehicle class and demand assumptions explicit; if demand counts are not sourced from actual observations, call them **synthetic demand scenarios on a real-layout-inspired network**, not measured Marathahalli traffic.
- Do not claim exact real-world lane count, speed, phase schedule or demand when only a map view suggests it.

## 6. Controller compatibility and signal phases

Current controllers assume one synthetic junction and two opposing axes. First inspect whether the verified target node genuinely has a comparable two-phase plan. Do not automatically copy the current `105 s NS / 95 s EW` timing adaptation to the site network.

- If a documented, verified controlled node has two compatible phases, map it to the existing controller/state-machine contract while keeping phase labels and movement permissions explicit.
- If it needs more than two phases, generalize the **phase-plan abstraction** and safe state machine to ordered allowed stages (green → yellow/clearance → next legal green), and make controller observations/actions phase-aware. The RL action must remain a request to hold/advance, never direct signal-string mutation. Preserve and test existing synthetic behavior.
- If signal locations or phase plan cannot be verified, generate and validate the road topology first, mark signal logic `unverified`, and do not report site-network controller results as operationally faithful until the owner approves the proposed signal assumptions.
- Do not create fictitious traffic lights at the overpass/underpass crossing.

## 7. Required network QA and acceptance tests (run only after P6 freeze and P7A owner review preparation)

Before using the site network in AI/research experiments:

1. Validate source provenance and retain transformed source metadata.
2. Run SUMO network checks and inspect the generated network visually in SUMO-GUI (or an available equivalent). Save a screenshot of the model for QA.
3. Check that road shapes, directions, connectors, grade separation and turn connections match the network audit; list known omissions.
4. Check for disconnected routes, invalid routes, unconnected edge fragments and impossible turns. Run route-generation smoke tests for every approach/OD pattern.
5. Confirm traffic signals are placed only at verified/modelled controlled nodes and every active phase is legal for the connected movements.
6. Test route generation for the same seed twice and verify equivalent vehicle manifests/hashes.
7. Verify the synthetic network still runs and that its historical baseline has not been overwritten.
8. Add regression tests for network selection, route connectivity, controlled-node existence, phase legality, and grade-separated paths not being accidentally connected.
9. Add `network_name`, `network_model_version`, `source_snapshot_id`, `signal_plan_id`, and `assumption_status` to each run/experiment manifest.

**Gate:** no DQN training or site-network research matrix until the owner can review `docs/MARATHAHALLI_NETWORK_AUDIT.md`, the SUMO-GUI network screenshot, route-connectivity checks and signal-plan inventory. Antigravity must stop and report these artifacts for review at this gate.

## 8. Site network and research results

- Keep pre-upgrade `results/baseline_pre_upgrade/` and legacy synthetic output intact.
- Make the verified Marathahalli site network the primary network for the new research evaluation.
- Rebuild demand scenarios for actual modelled entries/movements. Preserve comparable low/medium/heavy multipliers, but describe them as controlled synthetic demand unless authoritative traffic-count data is imported and documented.
- Run the same policies on the same network, same demand configuration and same seed-generated background trips. Do not compare one policy on the synthetic network with another on the site network.
- When this network is integrated during P7B, the React dashboard must display the network identity and source/assumption status in every site run/experiment detail and add a Network/Site Model view with map/topology, selected control node, source provenance and known limitations. This is not a P0–P6 dashboard requirement.
- The final report should distinguish: (a) legacy synthetic-network results, (b) Marathahalli geometry-grounded simulation results, and (c) any real-world measurements (only if actual authoritative counts/telemetry exist). Never conflate them.
