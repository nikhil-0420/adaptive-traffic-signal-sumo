"""Marathahalli site-model endpoint exposing road network facts and provenance."""
from fastapi import APIRouter
from ..schemas import SiteModelResponse

router = APIRouter(prefix="/site-model", tags=["Site Model"])


@router.get("", response_model=SiteModelResponse)
def get_site_model():
    """Return Marathahalli real-road network facts, geometry, and provenance table."""
    return SiteModelResponse(
        network_id="marathahalli",
        name="Marathahalli Bridge Junction (Varthur Rd / Outer Ring Rd)",
        location="Marathahalli, Bengaluru, Karnataka 560037 (12.9562° N, 77.7011° E)",
        description=(
            "Geographically grounded SUMO network model of the Marathahalli Bridge intersection. "
            "Integrates OpenCity road-width GIS datasets, OSM centerlines, and BTP signal timing adaptations."
        ),
        grounding_sources=[
            {
                "name": "BTP Marathahalli Yamlur Signal Plan",
                "type": "Traffic Signal Plan (PDF)",
                "detail": "Bengaluru Traffic Police signal timing structure adapted with 3s yellow and 2s all-red clearance.",
            },
            {
                "name": "OpenCity Bengaluru Road GIS",
                "type": "Geospatial Centerlines & Widths",
                "detail": "OpenCity municipal GIS road widths confirming 4-lane Varthur Rd and 6-lane Outer Ring Road.",
            },
            {
                "name": "OpenStreetMap Real-World Alignment",
                "type": "Physical Street Network",
                "detail": "Elevation profiles, ramp alignments, and directional service road slip lanes.",
            },
        ],
        grade_separation={
            "flyover": {
                "name": "Varthur Road Elevated Flyover",
                "lanes": 4,
                "direction": "East-West (HAL Airport Rd <-> Whitefield)",
                "function": "Carries ~70% of through traffic overhead, completely bypassing the surface signal.",
            },
            "underpass": {
                "name": "Outer Ring Road Mainline Underpass",
                "lanes": 6,
                "direction": "North-South (K.R. Puram <-> Kadubeesanahalli / Sarjapur)",
                "function": "Carries ~70% of through IT corridor traffic beneath, completely bypassing the surface signal.",
            },
            "surface_level": {
                "name": "Marathahalli Surface Signalized Junction",
                "tls_id": "marathahalli_tls",
                "lanes_per_leg": 2,
                "function": "Controls turning traffic, right-turns, bus transit, and remaining surface through movements.",
            },
        },
        surface_junction={
            "tls_id": "marathahalli_tls",
            "control_type": "2-Stage Signal with All-Red Clearance",
            "stages": [
                {
                    "phase": "NS_GREEN",
                    "axis": "NS",
                    "duration_s": 105.0,
                    "movements": "ORR South (Kadubeesanahalli) & ORR North (K.R. Puram) surface legs",
                    "state_string": "GGGgrrrrGGGgrrrr",
                },
                {
                    "phase": "NS_YELLOW",
                    "axis": "NS",
                    "duration_s": 3.0,
                    "state_string": "yyyyrrrryyyyrrrr",
                },
                {
                    "phase": "ALL_RED_1",
                    "axis": "ALL_RED",
                    "duration_s": 2.0,
                    "state_string": "rrrrrrrrrrrrrrrr",
                },
                {
                    "phase": "EW_GREEN",
                    "axis": "EW",
                    "duration_s": 95.0,
                    "movements": "Varthur West (HAL) & Varthur East (Whitefield) surface legs",
                    "state_string": "rrrrGGGgrrrrGGGg",
                },
                {
                    "phase": "EW_YELLOW",
                    "axis": "EW",
                    "duration_s": 3.0,
                    "state_string": "rrrryyyyrrrryyyy",
                },
                {
                    "phase": "ALL_RED_2",
                    "axis": "ALL_RED",
                    "duration_s": 2.0,
                    "state_string": "rrrrrrrrrrrrrrrr",
                },
            ],
            "detectors": [
                {"id": "det_hal_0", "approach": "W", "lane": 0, "length_m": 24.9},
                {"id": "det_hal_1", "approach": "W", "lane": 1, "length_m": 24.9},
                {"id": "det_wf_0", "approach": "E", "lane": 0, "length_m": 24.9},
                {"id": "det_wf_1", "approach": "E", "lane": 1, "length_m": 24.9},
                {"id": "det_orr_s_0", "approach": "S", "lane": 0, "length_m": 24.9},
                {"id": "det_orr_s_1", "approach": "S", "lane": 1, "length_m": 24.9},
                {"id": "det_orr_n_0", "approach": "N", "lane": 0, "length_m": 24.9},
                {"id": "det_orr_n_1", "approach": "N", "lane": 1, "length_m": 24.9},
            ],
        },
        provenance_table=[
            {
                "attribute": "Road Alignment & Centerlines",
                "status": "Verified",
                "source": "OpenCity GIS + OSM",
                "notes": "Exact physical geometries for Varthur Rd, ORR, and 4 service slip roads.",
            },
            {
                "attribute": "Grade Separation (Flyover + Underpass)",
                "status": "Verified",
                "source": "Satellite imagery + BDA infrastructure records",
                "notes": "4-lane flyover above, 6-lane mainline below, surface roundabout/signal between.",
            },
            {
                "attribute": "Signal Phase Clearance (Yellow/All-Red)",
                "status": "Verified",
                "source": "DP1 Safety Contract & BTP standard clearance",
                "notes": "Strictly 3s yellow and 2s all-red clearance preserved across all phase changes.",
            },
            {
                "attribute": "Surface Signal Phasing Structure",
                "status": "Inferred",
                "source": "BTP Yamlur corridor document adaptation",
                "notes": "Adapted as 2-stage alternating surface greens without pedestrian exclusive phase.",
            },
            {
                "attribute": "Grade Separation Volume Split",
                "status": "Inferred",
                "source": "Standard traffic engineering guidelines (HCM)",
                "notes": "70% through traffic assigned to flyover/underpass; 30% through + 100% turns at surface.",
            },
            {
                "attribute": "Real-Time Traffic Sensor Telemetry",
                "status": "Unknown (Synthetic Demand)",
                "source": "SUMO Lane-Area Detectors (E2)",
                "notes": "Controlled synthetic demand matrices (balanced, imbalanced_orr, imbalanced_varthur, surge).",
            },
        ],
        topology_image_url="/network/marathahalli/marathahalli_network_topology.png",
        sumo_gui_image_url="/network/marathahalli/sumo_gui_render.png",
    )
