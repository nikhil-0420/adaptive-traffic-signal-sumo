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
                    "phase": "EW_GREEN",
                    "axis": "EW",
                    "duration_s": 105.0,
                    "movements": "Varthur West (HAL) & Varthur East (Whitefield) surface legs (BTP Phase 1)",
                    "state_string": "rrrrGGGgrrrrGGGg",
                },
                {
                    "phase": "EW_YELLOW",
                    "axis": "EW",
                    "duration_s": 3.0,
                    "state_string": "rrrryyyyrrrryyyy",
                },
                {
                    "phase": "ALL_RED_1",
                    "axis": "ALL_RED",
                    "duration_s": 2.0,
                    "state_string": "rrrrrrrrrrrrrrrr",
                },
                {
                    "phase": "NS_GREEN",
                    "axis": "NS",
                    "duration_s": 95.0,
                    "movements": "ORR South (Kadubeesanahalli) & ORR North (K.R. Puram) surface legs (BTP Phase 2)",
                    "state_string": "GGGgrrrrGGGgrrrr",
                },
                {
                    "phase": "NS_YELLOW",
                    "axis": "NS",
                    "duration_s": 3.0,
                    "state_string": "yyyyrrrryyyyrrrr",
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
        geometry_extents={
            "simulation_model_span": {
                "width_m": 700.0,
                "height_m": 700.0,
                "x_range": [0.0, 700.0],
                "y_range": [0.0, 700.0],
                "center": [350.0, 332.0],
                "description": "Local Cartesian domain modeled in SUMO netconvert (350m approach arms)",
            },
            "geographic_crop_bbox": {
                "lat_min": 12.950,
                "lat_max": 12.964,
                "lon_min": 77.694,
                "lon_max": 77.708,
                "width_km": 1.52,
                "height_km": 1.55,
                "description": "OpenCity / BBMP municipal GIS crop bounding box (14 mdeg x 14 mdeg)",
            },
        },
        provenance_table=[
            {
                "attribute": "Road Alignment & Arterial Centerlines",
                "status": "Verified",
                "source": "OpenCity GIS + OSM",
                "notes": "Exact physical geometries for Varthur Rd, ORR, and 4 directional service slip roads.",
            },
            {
                "attribute": "Grade Separation Architecture (3 Tiers)",
                "status": "Verified",
                "source": "Satellite imagery + BDA infrastructure records",
                "notes": "Elevated 4-lane flyover, at-grade/underpass 6-lane mainline, surface signal crossroads.",
            },
            {
                "attribute": "Signal Phase Clearance (Yellow/All-Red)",
                "status": "Verified",
                "source": "DP1 Safety Contract & BTP standard clearance",
                "notes": "Strictly 3s yellow and 2s all-red clearance preserved across all phase changes.",
            },
            {
                "attribute": "BTP Signal Cycle & Split Durations",
                "status": "Verified",
                "source": "BTP Airport PS Marathalli Bridge plan",
                "notes": "Phase 1 Varthur Rd (HAL-WF) = 105s net green; Phase 2 ORR (Kadu-KR Puram) = 95s net green.",
            },
            {
                "attribute": "Lane Counts per Approach Carriageway",
                "status": "Inferred",
                "source": "OpenCity road-width GIS dataset",
                "notes": "Inferred from 14-18m road width attributes, mapping 2 lanes per surface crossroads leg.",
            },
            {
                "attribute": "Grade Separation Volume Split",
                "status": "Inferred",
                "source": "Standard traffic engineering guidelines (HCM)",
                "notes": "70% through traffic on flyover/underpass; 30% through + 100% turns at surface junction.",
            },
            {
                "attribute": "Ramp Curvature & Connection Radii",
                "status": "Inferred",
                "source": "Geometric cubic spline interpolation",
                "notes": "Inferred smooth cubic bezier splines between arterial centerlines and surface ramps.",
            },
            {
                "attribute": "Real-Time Traffic Demand Counts",
                "status": "Unknown (Synthetic Demand)",
                "source": "Controlled SUMO vehicle generators",
                "notes": "Controlled synthetic demand matrices (balanced, imbalanced_orr, imbalanced_varthur, surge).",
            },
        ],
        topology_image_url="/network/marathahalli/marathahalli_network_topology.png",
        sumo_gui_image_url="/network/marathahalli/sumo_gui_render.png",
    )
