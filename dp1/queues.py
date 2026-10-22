"""Queue measurement engine for DP1.

Provides precise, multi-metric queue characterization per approach:
1. Sensor-visible queue from simulated E2 lane-area detectors (metres).
2. Per-lane queue lengths and vehicle counts.
3. Longitudinal approach queue (maximum extent across parallel lanes, NEVER summed).
4. Total queued vehicle count across approach lanes.
5. Saturation / coverage boundary flag (queue reaches physical detector limit).
6. Ground-truth queue extent computed microscopically from vehicle positions, speeds, and gaps.
7. Waiting time and arrival rate tracking.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import traci


@dataclass
class LaneQueueInfo:
    lane_id: str
    lane_index: int
    detector_id: Optional[str]
    detector_queue_m: float
    detector_veh_count: int
    mean_speed_mps: float
    is_saturated: bool
    ground_truth_queue_m: float
    ground_truth_veh_count: int


@dataclass
class ApproachQueueInfo:
    approach: str                  # "N", "S", "E", "W"
    name: str                      # e.g. "ORR North (KR Puram)"
    axis: str                      # "NS" or "EW"
    edge_id: str
    detector_length_m: float
    
    # Primary controller-visible metrics
    longitudinal_queue_m: float    # max across lanes
    total_queued_vehicles: int     # sum of queued vehicles across lanes
    is_saturated: bool             # true if any lane queue reaches detector length
    sensor_status: str = "MEASURING" # "SATURATED", "CONFIRMED_ZERO", "MEASURING", "OFFLINE"
    
    # Ground-truth microscopic metrics (for validation, distinct from sensor)
    ground_truth_queue_m: float = 0.0   # contiguous stopped cluster from stop line
    ground_truth_veh_count: int = 0
    
    # Dynamics and waiting
    total_waiting_time_s: float = 0.0
    recent_arrival_rate_vpm: float = 0.0 # vehicles/minute arrival delta
    
    # Per-lane details
    lanes: List[LaneQueueInfo] = field(default_factory=list)
    
    # Telemetry metadata
    timestamp: float = 0.0
    freshness_s: float = 0.0
    data_valid: bool = True


APPROACH_DEFINITIONS = {
    "marathahalli": {
        "N": {
            "name": "ORR North (KR Puram)",
            "axis": "NS",
            "edge": "leg_orr_n_in",
            "lanes": ["leg_orr_n_in_0", "leg_orr_n_in_1"],
            "detectors": ["det_orr_n_0", "det_orr_n_1"],
            "det_length_m": 24.9,
        },
        "S": {
            "name": "ORR South (Kadubeesanahalli)",
            "axis": "NS",
            "edge": "leg_orr_s_in",
            "lanes": ["leg_orr_s_in_0", "leg_orr_s_in_1"],
            "detectors": ["det_orr_s_0", "det_orr_s_1"],
            "det_length_m": 24.9,
        },
        "E": {
            "name": "Varthur East (Whitefield)",
            "axis": "EW",
            "edge": "leg_wf_in",
            "lanes": ["leg_wf_in_0", "leg_wf_in_1"],
            "detectors": ["det_wf_0", "det_wf_1"],
            "det_length_m": 24.9,
        },
        "W": {
            "name": "Varthur West (HAL Airport Rd)",
            "axis": "EW",
            "edge": "leg_hal_in",
            "lanes": ["leg_hal_in_0", "leg_hal_in_1"],
            "detectors": ["det_hal_0", "det_hal_1"],
            "det_length_m": 24.9,
        },
    },
    "synthetic": {
        "N": {
            "name": "North Approach",
            "axis": "NS",
            "edge": "N_in",
            "lanes": ["N_in_0", "N_in_1"],
            "detectors": ["det_N_0", "det_N_1"],
            "det_length_m": 150.0,
        },
        "S": {
            "name": "South Approach",
            "axis": "NS",
            "edge": "S_in",
            "lanes": ["S_in_0", "S_in_1"],
            "detectors": ["det_S_0", "det_S_1"],
            "det_length_m": 150.0,
        },
        "E": {
            "name": "East Approach",
            "axis": "EW",
            "edge": "E_in",
            "lanes": ["E_in_0", "E_in_1"],
            "detectors": ["det_E_0", "det_E_1"],
            "det_length_m": 150.0,
        },
        "W": {
            "name": "West Approach",
            "axis": "EW",
            "edge": "W_in",
            "lanes": ["W_in_0", "W_in_1"],
            "detectors": ["det_W_0", "det_W_1"],
            "det_length_m": 150.0,
        },
    },
}


class QueueMeasurementEngine:
    """Manages queue observation, lane aggregation, and ground-truth validation."""

    def __init__(self, network: str = "synthetic"):
        self.network = network.lower().strip()
        self.definitions = APPROACH_DEFINITIONS.get(self.network, APPROACH_DEFINITIONS["synthetic"])
        self._prev_counts: Dict[str, int] = {a: 0 for a in ("N", "S", "E", "W")}
        self._last_time: float = 0.0

    def measure_all(self, t: float) -> Dict[str, ApproachQueueInfo]:
        """Perform comprehensive queue measurement across all four controlled approaches."""
        results = {}
        dt = max(1.0, t - self._last_time) if self._last_time > 0 else 1.0
        self._last_time = t

        for arm, spec in self.definitions.items():
            lane_infos = []
            det_len = spec["det_length_m"]
            sat_threshold = det_len - 0.5  # within 0.5m of physical detector limit

            approach_data_valid = True
            for idx, lane_id in enumerate(spec["lanes"]):
                det_id = spec["detectors"][idx] if idx < len(spec["detectors"]) else None
                det_q = 0.0
                det_vehs = 0
                mean_spd = 0.0
                is_sat = False

                if det_id:
                    try:
                        det_q = float(traci.lanearea.getJamLengthMeters(det_id))
                        det_vehs = int(traci.lanearea.getLastStepVehicleNumber(det_id))
                        mean_spd = float(traci.lanearea.getLastStepMeanSpeed(det_id))
                        is_sat = bool(det_q >= sat_threshold)
                    except Exception:
                        det_q = 0.0
                        det_vehs = 0
                        mean_spd = 0.0
                        is_sat = False
                        approach_data_valid = False

                # Ground truth microscopic computation on this lane
                gt_q, gt_vehs = self._compute_lane_ground_truth(lane_id)

                lane_infos.append(LaneQueueInfo(
                    lane_id=lane_id,
                    lane_index=idx,
                    detector_id=det_id,
                    detector_queue_m=round(det_q, 2),
                    detector_veh_count=det_vehs,
                    mean_speed_mps=round(mean_spd, 2),
                    is_saturated=is_sat,
                    ground_truth_queue_m=round(gt_q, 2),
                    ground_truth_veh_count=gt_vehs,
                ))

            # Longitudinal approach queue is the MAXIMUM across lanes (not the sum!)
            longitudinal_q = max((l.detector_queue_m for l in lane_infos), default=0.0)
            total_vehs = sum(l.detector_veh_count for l in lane_infos)
            approach_sat = any(l.is_saturated for l in lane_infos)
            
            gt_approach_q = max((l.ground_truth_queue_m for l in lane_infos), default=0.0)
            gt_approach_vehs = sum(l.ground_truth_veh_count for l in lane_infos)

            # Determine explicit semantic status (never silence missing as healthy zero)
            if not approach_data_valid:
                status_label = "OFFLINE"
            elif approach_sat:
                status_label = "SATURATED"
            elif longitudinal_q == 0.0:
                status_label = "CONFIRMED_ZERO"
            else:
                status_label = "MEASURING"

            # Waiting time across approach lanes
            total_wait = 0.0
            for lane_id in spec["lanes"]:
                try:
                    total_wait += float(traci.lane.getWaitingTime(lane_id))
                except Exception:
                    pass

            # Arrival rate estimate (delta in vehicles per minute)
            prev_c = self._prev_counts.get(arm, total_vehs)
            delta_v = max(0, total_vehs - prev_c)
            arrival_vpm = round((delta_v / dt) * 60.0, 1)
            self._prev_counts[arm] = total_vehs

            results[arm] = ApproachQueueInfo(
                approach=arm,
                name=spec["name"],
                axis=spec["axis"],
                edge_id=spec["edge"],
                detector_length_m=det_len,
                longitudinal_queue_m=round(longitudinal_q, 2),
                total_queued_vehicles=total_vehs,
                is_saturated=approach_sat,
                sensor_status=status_label,
                ground_truth_queue_m=round(gt_approach_q, 2),
                ground_truth_veh_count=gt_approach_vehs,
                total_waiting_time_s=round(total_wait, 1),
                recent_arrival_rate_vpm=arrival_vpm,
                lanes=lane_infos,
                timestamp=t,
                freshness_s=0.0,
                data_valid=approach_data_valid,
            )

        return results

    def _compute_lane_ground_truth(self, lane_id: str) -> tuple[float, int]:
        """Compute ground-truth contiguous stopped queue from stop line upstream.
        
        Rules:
        - Stopped threshold: speed < 0.1 m/s (or halting < 1.4 m/s).
        - Contiguous queue gap rule: gap between consecutive stopped vehicles <= 7.5m.
        - Queue extent: distance from lane stop line to back of furthest vehicle in cluster.
        """
        try:
            lane_len = traci.lane.getLength(lane_id)
            veh_ids = traci.lane.getLastStepVehicleIDs(lane_id)
        except Exception:
            return 0.0, 0

        if not veh_ids:
            return 0.0, 0

        # Collect vehicles on lane with their distance to stop line (lane_len - pos)
        veh_data = []
        for vid in veh_ids:
            try:
                pos = traci.vehicle.getLanePosition(vid)
                spd = traci.vehicle.getSpeed(vid)
                v_len = traci.vehicle.getLength(vid)
                dist_to_stop = max(0.0, lane_len - pos)
                veh_data.append((dist_to_stop, spd, v_len))
            except Exception:
                continue

        if not veh_data:
            return 0.0, 0

        # Sort by distance to stop line ascending (closest to stop line first)
        veh_data.sort(key=lambda x: x[0])

        cluster_count = 0
        furthest_extent = 0.0
        last_back = 0.0

        for dist_to_front, spd, v_len in veh_data:
            dist_to_back = dist_to_front + v_len
            # Stopped vehicle threshold
            if spd < 1.4:
                # If first vehicle, must be near stop line (<= 15m)
                if cluster_count == 0:
                    if dist_to_front <= 15.0:
                        cluster_count += 1
                        furthest_extent = dist_to_back
                        last_back = dist_to_back
                    else:
                        break  # gap between stop line and first stopped car too large
                else:
                    gap = dist_to_front - last_back
                    if gap <= 7.5:
                        cluster_count += 1
                        furthest_extent = dist_to_back
                        last_back = dist_to_back
                    else:
                        break  # contiguous queue broken
            else:
                if cluster_count > 0:
                    break  # moving vehicle breaks the stopped queue

        return min(lane_len, furthest_extent), cluster_count


def queues_to_legacy_dict(measurements: Dict[str, ApproachQueueInfo]) -> Dict[str, float]:
    """Convert detailed approach measurements to legacy {arm: queue_m} dict for backwards compatibility."""
    return {arm: info.longitudinal_queue_m for arm, info in measurements.items()}
