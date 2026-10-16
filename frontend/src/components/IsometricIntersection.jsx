import React, { useRef, useEffect, useState, useCallback } from 'react';
import {
  Play,
  Pause,
  RotateCcw,
  FastForward,
  Siren,
  Eye,
  Sliders,
  ChevronRight,
  ChevronLeft,
  Activity,
  Layers,
  Shield,
  Gauge,
  ZoomIn,
  ZoomOut,
  Maximize2,
  Tag,
  Move
} from 'lucide-react';
import { api } from '../api/client';

export function IsometricIntersection({
  runId = 'marathahalli_imbalanced_orr_adaptive_s121',
  network = null,
  liveTelemetry = null,
  isLiveMode = false,
  onRunChange = null,
  availableRuns = [],
  className = '',
}) {
  const canvasRef = useRef(null);
  const containerRef = useRef(null);

  // Replay State
  const [replayData, setReplayData] = useState(null);
  const [loadingReplay, setLoadingReplay] = useState(false);
  const [isPlaying, setIsPlaying] = useState(!isLiveMode);
  const [currentFrameIdx, setCurrentFrameIdx] = useState(0);
  const [playbackSpeed, setPlaybackSpeed] = useState(1); // 0.5, 1, 2, 5, 10
  const [viewMode, setViewMode] = useState('isometric'); // 'isometric' | 'topdown'
  const [showDetectors, setShowDetectors] = useState(true);
  const [showLabels, setShowLabels] = useState(true);

  // Viewport Zoom & Pan State
  const [zoom, setZoom] = useState(1.0); // 0.6 to 3.5
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const dragStartRef = useRef({ x: 0, y: 0 });
  const panStartRef = useRef({ x: 0, y: 0 });

  // Animation Loop Ref
  const animFrameRef = useRef(null);
  const lastTickTimeRef = useRef(Date.now());
  const frameAccumulatorRef = useRef(0);

  // Zoom & Pan Handlers
  const handleZoomIn = () => {
    setZoom((z) => Math.min(3.5, Number((z + 0.25).toFixed(2))));
  };

  const handleZoomOut = () => {
    setZoom((z) => Math.max(0.6, Number((z - 0.25).toFixed(2))));
  };

  const handleResetView = () => {
    setZoom(1.0);
    setPan({ x: 0, y: 0 });
  };

  // Mouse wheel non-passive zoom
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const handleWheelNative = (e) => {
      e.preventDefault();
      const delta = e.deltaY < 0 ? 0.15 : -0.15;
      setZoom((z) => Math.min(3.5, Math.max(0.6, Number((z + delta).toFixed(2)))));
    };

    canvas.addEventListener('wheel', handleWheelNative, { passive: false });
    return () => {
      canvas.removeEventListener('wheel', handleWheelNative);
    };
  }, []);

  // Mouse drag-to-pan handlers
  const handleMouseDown = (e) => {
    if (e.button !== 0) return; // Left mouse button only
    setIsDragging(true);
    dragStartRef.current = { x: e.clientX, y: e.clientY };
    panStartRef.current = { ...pan };
  };

  const handleMouseMove = (e) => {
    if (!isDragging) return;
    const dx = e.clientX - dragStartRef.current.x;
    const dy = e.clientY - dragStartRef.current.y;
    setPan({
      x: panStartRef.current.x + dx,
      y: panStartRef.current.y + dy,
    });
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  useEffect(() => {
    if (!isDragging) return;
    const onWindowMouseMove = (e) => {
      const dx = e.clientX - dragStartRef.current.x;
      const dy = e.clientY - dragStartRef.current.y;
      setPan({
        x: panStartRef.current.x + dx,
        y: panStartRef.current.y + dy,
      });
    };
    const onWindowMouseUp = () => setIsDragging(false);

    window.addEventListener('mousemove', onWindowMouseMove);
    window.addEventListener('mouseup', onWindowMouseUp);
    return () => {
      window.removeEventListener('mousemove', onWindowMouseMove);
      window.removeEventListener('mouseup', onWindowMouseUp);
    };
  }, [isDragging]);

  // Detect whether run is Marathahalli real-road topology vs Synthetic 4-way cross
  const isMarathahalli = Boolean(
    network === 'marathahalli' ||
    (runId && (runId.includes('marathahalli') || runId.includes('orr') || runId.includes('varthur') || runId.includes('hal') || runId.includes('wf'))) ||
    (replayData && replayData.network === 'marathahalli') ||
    (liveTelemetry && (liveTelemetry.run_id?.includes('marathahalli') || liveTelemetry.network === 'marathahalli'))
  );

  // Fetch replay dataset
  const loadReplay = useCallback(async (targetRunId) => {
    setLoadingReplay(true);
    try {
      const data = await api.getReplay(targetRunId);
      if (data && data.frames && data.frames.length > 0) {
        setReplayData(data);
        setCurrentFrameIdx(0);
      } else {
        setReplayData(null);
      }
    } catch (err) {
      console.warn('Failed to load replay:', err);
      setReplayData(null);
    } finally {
      setLoadingReplay(false);
    }
  }, []);

  useEffect(() => {
    if (!isLiveMode) {
      loadReplay(runId);
    }
  }, [runId, isLiveMode, loadReplay]);

  // Current frame determination
  const activeFrame = isLiveMode && liveTelemetry
    ? {
        t: liveTelemetry.sim_time_s || 0,
        phase: liveTelemetry.phase || 'GREEN',
        axis: liveTelemetry.axis || 'NS',
        tl_state: liveTelemetry.traffic_light_state || 'GGggrrrrGGggrrrr',
        queues_m: liveTelemetry.queues_m || { N: 0, S: 0, E: 0, W: 0 },
        emergency_approaching: Boolean(liveTelemetry.emergency_approaching),
        emergency_dist_m: liveTelemetry.emergency_dist_m,
        vehicles: liveTelemetry.vehicles || [],
      }
    : replayData && replayData.frames && replayData.frames.length > 0
    ? replayData.frames[Math.min(currentFrameIdx, replayData.frames.length - 1)]
    : null;

  // Playback loop
  useEffect(() => {
    if (isLiveMode || !isPlaying || !replayData || !replayData.frames.length) return;

    let mounted = true;
    const tick = () => {
      const now = Date.now();
      const dt = (now - lastTickTimeRef.current) / 1000;
      lastTickTimeRef.current = now;

      // step_s is typically 1.0s in SUMO
      const frameStep = (replayData.step_s || 1.0);
      frameAccumulatorRef.current += (dt * playbackSpeed) / frameStep;

      if (frameAccumulatorRef.current >= 1.0) {
        const advanceFrames = Math.floor(frameAccumulatorRef.current);
        frameAccumulatorRef.current -= advanceFrames;

        setCurrentFrameIdx((prev) => {
          const next = prev + advanceFrames;
          if (next >= replayData.frames.length) {
            return 0; // loop
          }
          return next;
        });
      }

      if (mounted) {
        animFrameRef.current = requestAnimationFrame(tick);
      }
    };

    lastTickTimeRef.current = Date.now();
    animFrameRef.current = requestAnimationFrame(tick);

    return () => {
      mounted = false;
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    };
  }, [isPlaying, playbackSpeed, replayData, isLiveMode]);

  // Canvas Rendering
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Handle high DPI
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    const w = rect.width;
    const h = rect.height;
    if (w <= 0 || h <= 0) return;

    const targetW = Math.floor(w * dpr);
    const targetH = Math.floor(h * dpr);
    if (canvas.width !== targetW || canvas.height !== targetH) {
      canvas.width = targetW;
      canvas.height = targetH;
    }

    // Always reset transform matrix to prevent scale compounding across frames
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, w, h);

    // Background Gradient (Deep Cockpit Blue-Gray)
    const bgGrad = ctx.createRadialGradient(w / 2, h / 2, 20, w / 2, h / 2, Math.max(w, h));
    bgGrad.addColorStop(0, '#0f1624');
    bgGrad.addColorStop(1, '#080c14');
    ctx.fillStyle = bgGrad;
    ctx.fillRect(0, 0, w, h);

    const cx = (w / 2) + pan.x;
    const cy = (h / 2) + pan.y;

    const isIso = viewMode === 'isometric';
    const origX = isMarathahalli ? 350.0 : 300.0;
    const origY = isMarathahalli ? 350.0 : 300.0;
    const viewSpanM = isMarathahalli ? 375 : 280;
    const baseScale = (Math.min(w, h) / (viewSpanM * (isMarathahalli ? (isIso ? 1.70 : 1.95) : 1.85))) * zoom;

    // Coordinate transforms
    const worldToScreen = (wx, wy, z = 0) => {
      const u = wx - origX;
      const v = wy - origY;
      if (!isIso) {
        // Orthographic Top-Down (SUMO: +y is North, canvas: +y is Down)
        return {
          x: cx + u * baseScale,
          y: cy - v * baseScale - (z * baseScale * 0.35),
        };
      }
      // Isometric 2.5D: 30 degree tilt
      const cos30 = Math.cos(Math.PI / 6);
      const sin30 = Math.sin(Math.PI / 6);
      const isoX = (u - v) * cos30;
      const isoY = (u + v) * sin30;
      return {
        x: cx + isoX * baseScale,
        y: cy - (isoY * baseScale * 0.72) - (z * baseScale * 1.85),
      };
    };

    // Vector angle transform to screen heading
    const sumoAngleToScreen = (deg) => {
      const rad = (deg * Math.PI) / 180;
      // In SUMO: 0=N, 90=E, 180=S, 270=W
      const vx = Math.sin(rad);
      const vy = Math.cos(rad);
      const p1 = worldToScreen(origX, origY, 0);
      const p2 = worldToScreen(origX + vx * 10, origY + vy * 10, 0);
      return Math.atan2(p2.y - p1.y, p2.x - p1.x);
    };

    // Drawing primitives
    const drawRoadQuad = (x1, y1, x2, y2, x3, y3, x4, y4, fill, z = 0) => {
      const p1 = worldToScreen(x1, y1, z);
      const p2 = worldToScreen(x2, y2, z);
      const p3 = worldToScreen(x3, y3, z);
      const p4 = worldToScreen(x4, y4, z);
      ctx.fillStyle = fill;
      ctx.beginPath();
      ctx.moveTo(p1.x, p1.y);
      ctx.lineTo(p2.x, p2.y);
      ctx.lineTo(p3.x, p3.y);
      ctx.lineTo(p4.x, p4.y);
      ctx.closePath();
      ctx.fill();
    };

    const drawLine = (x1, y1, x2, y2, color, width, dash = [], z = 0) => {
      const pA = worldToScreen(x1, y1, z);
      const pB = worldToScreen(x2, y2, z);
      ctx.strokeStyle = color;
      ctx.lineWidth = width;
      ctx.setLineDash(dash);
      ctx.beginPath();
      ctx.moveTo(pA.x, pA.y);
      ctx.lineTo(pB.x, pB.y);
      ctx.stroke();
      ctx.setLineDash([]);
    };

    const drawCorridor = (x1, y1, x2, y2, widthM, fill, z = 0) => {
      const dx = x2 - x1;
      const dy = y2 - y1;
      const len = Math.hypot(dx, dy);
      if (len < 0.001) return;
      const nx = (-dy / len) * (widthM / 2);
      const ny = (dx / len) * (widthM / 2);
      drawRoadQuad(
        x1 + nx, y1 + ny,
        x2 + nx, y2 + ny,
        x2 - nx, y2 - ny,
        x1 - nx, y1 - ny,
        fill,
        z
      );
    };

    const drawCurvedRoad = (pts, widthM, fill, z = 0) => {
      if (pts.length < 2) return;
      for (let i = 0; i < pts.length - 1; i++) {
        drawCorridor(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], widthM, fill, z);
      }
    };

    // ==========================================
    // 1. GROUND GRID & TERRAIN
    // ==========================================
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.025)';
    ctx.lineWidth = 1;
    const gridRange = isMarathahalli ? 340 : 240;
    const gridStep = 40;
    for (let gx = -gridRange; gx <= gridRange; gx += gridStep) {
      const pA = worldToScreen(origX + gx, origY - gridRange, 0);
      const pB = worldToScreen(origX + gx, origY + gridRange, 0);
      ctx.beginPath();
      ctx.moveTo(pA.x, pA.y);
      ctx.lineTo(pB.x, pB.y);
      ctx.stroke();

      const pC = worldToScreen(origX - gridRange, origY + gx, 0);
      const pD = worldToScreen(origX + gridRange, origY + gx, 0);
      ctx.beginPath();
      ctx.moveTo(pC.x, pC.y);
      ctx.lineTo(pD.x, pD.y);
      ctx.stroke();
    }

    if (isMarathahalli) {
      // =========================================================================
      // MARATHAHALLI BRIDGE REAL ROAD NETWORK TOPOLOGY (SUMO 1:1 GEOMETRY)
      // =========================================================================

      // (A) Grade-0 Outer Arterials
      // West: HAL Airport Road (0..170, y=350)
      drawCorridor(0, 350, 170, 350, 17.5, '#131b29', 0);
      drawCorridor(0, 350, 170, 350, 14.0, '#1a2333', 0);
      drawLine(0, 350, 170, 350, 'rgba(245, 158, 11, 0.75)', 1.5, [], 0);

      // East: Whitefield / Varthur (530..700, y=350)
      drawCorridor(530, 350, 700, 350, 17.5, '#131b29', 0);
      drawCorridor(530, 350, 700, 350, 14.0, '#1a2333', 0);
      drawLine(530, 350, 700, 350, 'rgba(245, 158, 11, 0.75)', 1.5, [], 0);

      // (B) Outer Ring Road (ORR) North-South Corridor (Underpass / Mainline)
      // South Outer: (350, 0) to (350, 170)
      drawCorridor(350, 0, 350, 170, 19.5, '#111827', 0);
      drawCorridor(350, 0, 350, 170, 16.0, '#182130', 0);

      // ORR Mainline Underpass: (350, 170) through (350, 530) - Trench below Flyover
      drawCorridor(350, 170, 350, 530, 20.0, '#0c121e', 0); // Trench wall base
      drawCorridor(350, 170, 350, 530, 16.0, '#141c2a', 0); // Underpass deck

      // North Outer: (350, 530) to (350, 700)
      drawCorridor(350, 530, 350, 700, 19.5, '#111827', 0);
      drawCorridor(350, 530, 350, 700, 16.0, '#182130', 0);

      // ORR Underpass Centerline & Dash lines
      drawLine(350 - 0.2, 0, 350 - 0.2, 700, 'rgba(16, 185, 129, 0.85)', 1.5, [], 0);
      drawLine(350 + 0.2, 0, 350 + 0.2, 700, 'rgba(16, 185, 129, 0.85)', 1.5, [], 0);
      drawLine(350 - 4.2, 0, 350 - 4.2, 700, 'rgba(255, 255, 255, 0.3)', 1, [4, 6], 0);
      drawLine(350 + 4.2, 0, 350 + 4.2, 700, 'rgba(255, 255, 255, 0.3)', 1, [4, 6], 0);

      // (C) Surface Connector Ramps & Signalized Approach Legs
      // Ramps connecting outer splits to surface junction nodes
      drawCorridor(170, 350, 305, 332, 14.0, '#1a2333', 0); // HAL Ramp
      drawCorridor(530, 350, 395, 332, 14.0, '#1a2333', 0); // Whitefield Ramp
      drawCorridor(350, 530, 350, 375, 14.0, '#1a2333', 0); // ORR North Ramp
      drawCorridor(350, 170, 350, 290, 14.0, '#1a2333', 0); // ORR South Ramp

      // Surface Crossroads Legs entering marathahalli_tls (350, 332)
      drawCorridor(305, 332, 350, 332, 14.0, '#222f44', 0); // West Leg (HAL)
      drawCorridor(395, 332, 350, 332, 14.0, '#222f44', 0); // East Leg (WF)
      drawCorridor(350, 375, 350, 332, 14.0, '#222f44', 0); // North Leg (ORR N)
      drawCorridor(350, 290, 350, 332, 14.0, '#222f44', 0); // South Leg (ORR S)

      // (D) Channelized Free-Flow Left Turn Slips
      const slipW_N = [[192.8, 359.6], [231.0, 378.7], [321.3, 469.1], [340.4, 507.2]];
      const slipN_E = [[359.6, 507.2], [378.7, 469.1], [469.1, 378.7], [507.2, 359.6]];
      const slipE_S = [[508.3, 341.0], [469.1, 321.3], [378.7, 231.0], [359.6, 192.8]];
      const slipS_W = [[340.4, 192.8], [321.3, 231.0], [231.0, 321.3], [200.2, 336.7]];

      drawCurvedRoad(slipW_N, 6.0, '#162030', 0);
      drawCurvedRoad(slipN_E, 6.0, '#162030', 0);
      drawCurvedRoad(slipE_S, 6.0, '#162030', 0);
      drawCurvedRoad(slipS_W, 6.0, '#162030', 0);

      // (E) Surface Conflict Box (marathahalli_tls at 350, 332)
      drawRoadQuad(
        350 - 8.5, 332 - 8.5,
        350 + 8.5, 332 - 8.5,
        350 + 8.5, 332 + 8.5,
        350 - 8.5, 332 + 8.5,
        '#233047',
        0
      );
      // Yellow Cross-Hatch Box
      drawLine(350 - 8, 332 - 8, 350 + 8, 332 + 8, 'rgba(234, 179, 8, 0.35)', 1, [], 0);
      drawLine(350 - 8, 332 + 8, 350 + 8, 332 - 8, 'rgba(234, 179, 8, 0.35)', 1, [], 0);

      // Stop Lines & Zebra Crossings at marathahalli_tls
      drawLine(341, 326, 341, 338, 'rgba(255, 255, 255, 0.95)', 2.5, [], 0); // West Stop Line
      drawLine(359, 326, 359, 338, 'rgba(255, 255, 255, 0.95)', 2.5, [], 0); // East Stop Line
      drawLine(344, 343, 356, 343, 'rgba(255, 255, 255, 0.95)', 2.5, [], 0); // North Stop Line
      drawLine(344, 321, 356, 321, 'rgba(255, 255, 255, 0.95)', 2.5, [], 0); // South Stop Line

      // (F) 25m Lane-Area E2 Detectors & Real-Time Queue Fill
      if (showDetectors && activeFrame) {
        const qN = activeFrame.queues_m?.N || 0;
        const qS = activeFrame.queues_m?.S || 0;
        const qE = activeFrame.queues_m?.E || 0;
        const qW = activeFrame.queues_m?.W || 0;
        const detSpan = 25.0; // 25m stop line span

        // West: det_hal (x in [315, 340], y = 328.8)
        drawRoadQuad(340 - detSpan, 328.8 - 3.2, 340, 328.8 - 3.2, 340, 328.8 + 3.2, 340 - detSpan, 328.8 + 3.2, 'rgba(56, 189, 248, 0.1)', 0);
        if (qW > 0) {
          const fillW = Math.min(detSpan, qW);
          drawRoadQuad(340 - fillW, 328.8 - 3.2, 340, 328.8 - 3.2, 340, 328.8 + 3.2, 340 - fillW, 328.8 + 3.2, 'rgba(239, 68, 68, 0.35)', 0);
        }

        // East: det_wf (x in [360, 385], y = 335.2)
        drawRoadQuad(360, 335.2 - 3.2, 360 + detSpan, 335.2 - 3.2, 360 + detSpan, 335.2 + 3.2, 360, 335.2 + 3.2, 'rgba(56, 189, 248, 0.1)', 0);
        if (qE > 0) {
          const fillE = Math.min(detSpan, qE);
          drawRoadQuad(360, 335.2 - 3.2, 360 + fillE, 335.2 - 3.2, 360 + fillE, 335.2 + 3.2, 360, 335.2 + 3.2, 'rgba(239, 68, 68, 0.35)', 0);
        }

        // North: det_orr_n (x = 346.8, y in [342.4, 367.4])
        drawRoadQuad(346.8 - 3.2, 342.4, 346.8 + 3.2, 342.4, 346.8 + 3.2, 342.4 + detSpan, 346.8 - 3.2, 342.4 + detSpan, 'rgba(56, 189, 248, 0.1)', 0);
        if (qN > 0) {
          const fillN = Math.min(detSpan, qN);
          drawRoadQuad(346.8 - 3.2, 342.4, 346.8 + 3.2, 342.4, 346.8 + 3.2, 342.4 + fillN, 346.8 - 3.2, 342.4 + fillN, 'rgba(239, 68, 68, 0.35)', 0);
        }

        // South: det_orr_s (x = 353.2, y in [296.6, 321.6])
        drawRoadQuad(353.2 - 3.2, 321.6 - detSpan, 353.2 + 3.2, 321.6 - detSpan, 353.2 + 3.2, 321.6, 353.2 - 3.2, 321.6, 'rgba(56, 189, 248, 0.1)', 0);
        if (qS > 0) {
          const fillS = Math.min(detSpan, qS);
          drawRoadQuad(353.2 - 3.2, 321.6 - fillS, 353.2 + 3.2, 321.6 - fillS, 353.2 + 3.2, 321.6, 353.2 - 3.2, 321.6, 'rgba(239, 68, 68, 0.35)', 0);
        }
      }

      // (G) 3D Traffic Light Head at marathahalli_tls (350, 332)
      const isNsGreen = activeFrame?.phase === 'GREEN' && activeFrame?.axis === 'NS';
      const isNsYellow = activeFrame?.phase === 'YELLOW' && activeFrame?.axis === 'NS';
      const isEwGreen = activeFrame?.phase === 'GREEN' && activeFrame?.axis === 'EW';
      const isEwYellow = activeFrame?.phase === 'YELLOW' && activeFrame?.axis === 'EW';
      const isAllRed = activeFrame?.phase === 'ALL_RED';

      const tlsPosts = [
        { wx: 350 - 9.0, wy: 332 + 9.0, green: isNsGreen, yellow: isNsYellow, red: isAllRed || isEwGreen || isEwYellow },
        { wx: 350 + 9.0, wy: 332 + 9.0, green: isEwGreen, yellow: isEwYellow, red: isAllRed || isNsGreen || isNsYellow },
        { wx: 350 + 9.0, wy: 332 - 9.0, green: isNsGreen, yellow: isNsYellow, red: isAllRed || isEwGreen || isEwYellow },
        { wx: 350 - 9.0, wy: 332 - 9.0, green: isEwGreen, yellow: isEwYellow, red: isAllRed || isNsGreen || isNsYellow },
      ];

      tlsPosts.forEach((c) => {
        const basePt = worldToScreen(c.wx, c.wy, 0);
        const topPt = worldToScreen(c.wx, c.wy, isIso ? 6.0 : 0);
        if (isIso) {
          ctx.strokeStyle = '#64748b';
          ctx.lineWidth = 2.5;
          ctx.beginPath();
          ctx.moveTo(basePt.x, basePt.y);
          ctx.lineTo(topPt.x, topPt.y);
          ctx.stroke();
        }
        ctx.fillStyle = '#0f172a';
        ctx.strokeStyle = '#38bdf8';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.roundRect(topPt.x - 5, topPt.y - 10, 10, 20, 3);
        ctx.fill();
        ctx.stroke();

        const rCol = c.red ? '#ef4444' : '#450a0a';
        const yCol = c.yellow ? '#f59e0b' : '#451a03';
        const gCol = c.green ? '#10b981' : '#022c22';

        const drawBulb = (offY, col, on) => {
          ctx.fillStyle = col;
          ctx.beginPath();
          ctx.arc(topPt.x, topPt.y + offY, 2.3, 0, Math.PI * 2);
          ctx.fill();
          if (on) {
            ctx.save();
            ctx.shadowColor = col;
            ctx.shadowBlur = 9;
            ctx.fillStyle = col;
            ctx.beginPath();
            ctx.arc(topPt.x, topPt.y + offY, 2.5, 0, Math.PI * 2);
            ctx.fill();
            ctx.restore();
          }
        };
        drawBulb(-5.5, rCol, c.red);
        drawBulb(0, yCol, c.yellow);
        drawBulb(5.5, gCol, c.green);
      });

      // (H) ELEVATED VARTHUR ROAD FLYOVER (Bridge Overpass Z = +7.0m)
      // Elevated bridge crosses over the ORR Underpass along y = 350.0 from x = 170 to x = 530
      if (isIso) {
        // 1. Soft Shadow on the ORR Underpass below
        drawRoadQuad(170, 343, 530, 343, 530, 357, 170, 357, 'rgba(0, 0, 0, 0.45)', 0);

        // 2. Concrete Bridge Piers / Columns
        [275, 310, 390, 425].forEach((px) => {
          const pierBaseL = worldToScreen(px, 345, 0);
          const pierTopL = worldToScreen(px, 345, 6.5);
          const pierBaseR = worldToScreen(px, 355, 0);
          const pierTopR = worldToScreen(px, 355, 6.5);
          ctx.fillStyle = '#334155';
          ctx.strokeStyle = '#1e293b';
          ctx.lineWidth = 1;
          ctx.beginPath();
          ctx.moveTo(pierBaseL.x, pierBaseL.y);
          ctx.lineTo(pierTopL.x, pierTopL.y);
          ctx.lineTo(pierTopR.x, pierTopR.y);
          ctx.lineTo(pierBaseR.x, pierBaseR.y);
          ctx.closePath();
          ctx.fill();
          ctx.stroke();
        });
      }

      // Flyover Deck Segments with rising/descending elevation
      // West Ramp (170..275, z: 0 -> 6.5m)
      const rampW_steps = 5;
      for (let s = 0; s < rampW_steps; s++) {
        const xA = 170 + (s * (275 - 170)) / rampW_steps;
        const xB = 170 + ((s + 1) * (275 - 170)) / rampW_steps;
        const zMid = ((s + 0.5) / rampW_steps) * 6.5;
        drawRoadQuad(xA, 343.5, xB, 343.5, xB, 356.5, xA, 356.5, '#1e293b', zMid);
      }

      // Elevated Main Bridge Span over ORR Underpass (275..425, z = 7.0m)
      drawRoadQuad(275, 343.5, 425, 343.5, 425, 356.5, 275, 356.5, '#243247', 7.0);

      // East Ramp (425..530, z: 6.5m -> 0)
      for (let s = 0; s < rampW_steps; s++) {
        const xA = 425 + (s * (530 - 425)) / rampW_steps;
        const xB = 425 + ((s + 1) * (530 - 425)) / rampW_steps;
        const zMid = (1 - (s + 0.5) / rampW_steps) * 6.5;
        drawRoadQuad(xA, 343.5, xB, 343.5, xB, 356.5, xA, 356.5, '#1e293b', zMid);
      }

      // Bridge Parapet Railings & Cyan Neon Strip
      drawLine(275, 343.5, 425, 343.5, '#38bdf8', 2.0, [], 7.0);
      drawLine(275, 356.5, 425, 356.5, '#38bdf8', 2.0, [], 7.0);
      // Double Yellow Centerline on Flyover
      drawLine(170, 350, 530, 350, 'rgba(245, 158, 11, 0.85)', 1.5, [], 7.0);
      drawLine(170, 346.8, 530, 346.8, 'rgba(255, 255, 255, 0.35)', 1, [4, 6], 7.0);
      drawLine(170, 353.2, 530, 353.2, 'rgba(255, 255, 255, 0.35)', 1, [4, 6], 7.0);

    } else {
      // =========================================================================
      // SYNTHETIC 4-WAY CROSSROAD TOPOLOGY (ORIGINAL VERIFIED REFERENCE)
      // =========================================================================
      const rw = 7.5;
      const armL = 220;
      const curbW = rw + 2.2;
      drawRoadQuad(300 - curbW, 300 - armL, 300 + curbW, 300 - armL, 300 + curbW, 300 + armL, 300 - curbW, 300 + armL, '#131b29');
      drawRoadQuad(300 - armL, 300 - curbW, 300 + armL, 300 - curbW, 300 + armL, 300 + curbW, 300 - armL, 300 + curbW, '#131b29');
      drawRoadQuad(300 - rw, 300 - armL, 300 + rw, 300 - armL, 300 + rw, 300 + armL, 300 - rw, 300 + armL, '#1a2333');
      drawRoadQuad(300 - armL, 300 - rw, 300 + armL, 300 - rw, 300 + armL, 300 + rw, 300 - armL, 300 + rw, '#1a2333');

      // Conflict Box
      drawRoadQuad(300 - rw, 300 - rw, 300 + rw, 300 - rw, 300 + rw, 300 + rw, 300 - rw, 300 + rw, '#202b3f');
      drawLine(300 - rw, 300 - rw, 300 + rw, 300 + rw, 'rgba(234, 179, 8, 0.22)', 1);
      drawLine(300 - rw, 300 + rw, 300 + rw, 300 - rw, 'rgba(234, 179, 8, 0.22)', 1);

      // Center double yellow lines
      drawLine(300 - 0.15, 300 + rw, 300 - 0.15, 300 + armL, 'rgba(245, 158, 11, 0.75)', 1.5);
      drawLine(300 + 0.15, 300 + rw, 300 + 0.15, 300 + armL, 'rgba(245, 158, 11, 0.75)', 1.5);
      drawLine(300 - 0.15, 300 - armL, 300 - 0.15, 300 - rw, 'rgba(245, 158, 11, 0.75)', 1.5);
      drawLine(300 + 0.15, 300 - armL, 300 + 0.15, 300 - rw, 'rgba(245, 158, 11, 0.75)', 1.5);
      drawLine(300 + rw, 300 - 0.15, 300 + armL, 300 - 0.15, 'rgba(245, 158, 11, 0.75)', 1.5);
      drawLine(300 + rw, 300 + 0.15, 300 + armL, 300 + 0.15, 'rgba(245, 158, 11, 0.75)', 1.5);
      drawLine(300 - armL, 300 - 0.15, 300 - rw, 300 - 0.15, 'rgba(245, 158, 11, 0.75)', 1.5);
      drawLine(300 - armL, 300 + 0.15, 300 - rw, 300 + 0.15, 'rgba(245, 158, 11, 0.75)', 1.5);

      // White dashed lane dividers
      const laneDivOffset = 3.2;
      const dashPattern = [4, 6];
      drawLine(300 - laneDivOffset, 300 + rw, 300 - laneDivOffset, 300 + armL, 'rgba(255, 255, 255, 0.35)', 1, dashPattern);
      drawLine(300 + laneDivOffset, 300 + rw, 300 + laneDivOffset, 300 + armL, 'rgba(255, 255, 255, 0.35)', 1, dashPattern);
      drawLine(300 - laneDivOffset, 300 - armL, 300 - laneDivOffset, 300 - rw, 'rgba(255, 255, 255, 0.35)', 1, dashPattern);
      drawLine(300 + laneDivOffset, 300 - armL, 300 + laneDivOffset, 300 - rw, 'rgba(255, 255, 255, 0.35)', 1, dashPattern);
      drawLine(300 + rw, 300 - laneDivOffset, 300 + armL, 300 - laneDivOffset, 'rgba(255, 255, 255, 0.35)', 1, dashPattern);
      drawLine(300 + rw, 300 + laneDivOffset, 300 + armL, 300 + laneDivOffset, 'rgba(255, 255, 255, 0.35)', 1, dashPattern);
      drawLine(300 - armL, 300 - laneDivOffset, 300 - rw, 300 - laneDivOffset, 'rgba(255, 255, 255, 0.35)', 1, dashPattern);
      drawLine(300 - armL, 300 + laneDivOffset, 300 - rw, 300 + laneDivOffset, 'rgba(255, 255, 255, 0.35)', 1, dashPattern);

      // Stop lines
      drawLine(300 - rw, 300 + rw + 4, 300, 300 + rw + 4, 'rgba(255, 255, 255, 0.95)', 3);
      drawLine(300, 300 - rw - 4, 300 + rw, 300 - rw - 4, 'rgba(255, 255, 255, 0.95)', 3);
      drawLine(300 + rw + 4, 300, 300 + rw + 4, 300 + rw, 'rgba(255, 255, 255, 0.95)', 3);
      drawLine(300 - rw - 4, 300 - rw, 300 - rw - 4, 300, 'rgba(255, 255, 255, 0.95)', 3);

      // Synthetic E2 Detectors
      if (showDetectors && activeFrame) {
        const qN = activeFrame.queues_m?.N || 0;
        const qS = activeFrame.queues_m?.S || 0;
        const qE = activeFrame.queues_m?.E || 0;
        const qW = activeFrame.queues_m?.W || 0;
        const detLen = 150.0;
        const nStop = 300 + rw + 4;
        drawRoadQuad(300 - 6.4, nStop, 300, nStop, 300, nStop + detLen, 300 - 6.4, nStop + detLen, 'rgba(56, 189, 248, 0.05)');
        if (qN > 0) drawRoadQuad(300 - 6.4, nStop, 300, nStop, 300, nStop + Math.min(detLen, qN), 300 - 6.4, nStop + Math.min(detLen, qN), 'rgba(239, 68, 68, 0.28)');
        const sStop = 300 - rw - 4;
        drawRoadQuad(300, sStop - detLen, 300 + 6.4, sStop - detLen, 300 + 6.4, sStop, 300, sStop, 'rgba(56, 189, 248, 0.05)');
        if (qS > 0) drawRoadQuad(300, sStop - Math.min(detLen, qS), 300 + 6.4, sStop - Math.min(detLen, qS), 300 + 6.4, sStop, 300, sStop, 'rgba(239, 68, 68, 0.28)');
        const eStop = 300 + rw + 4;
        drawRoadQuad(eStop, 300, eStop + detLen, 300, eStop + detLen, 300 + 6.4, eStop, 300 + 6.4, 'rgba(56, 189, 248, 0.05)');
        if (qE > 0) drawRoadQuad(eStop, 300, eStop + Math.min(detLen, qE), 300, eStop + Math.min(detLen, qE), 300 + 6.4, eStop, 300 + 6.4, 'rgba(239, 68, 68, 0.28)');
        const wStop = 300 - rw - 4;
        drawRoadQuad(wStop - detLen, 300 - 6.4, wStop, 300 - 6.4, wStop, 300, wStop - detLen, 300, 'rgba(56, 189, 248, 0.05)');
        if (qW > 0) drawRoadQuad(wStop - Math.min(detLen, qW), 300 - 6.4, wStop, 300 - 6.4, wStop, 300, wStop - Math.min(detLen, qW), 300, 'rgba(239, 68, 68, 0.28)');
      }

      // Synthetic Signal Posts
      const isNsGreen = activeFrame?.phase === 'GREEN' && activeFrame?.axis === 'NS';
      const isNsYellow = activeFrame?.phase === 'YELLOW' && activeFrame?.axis === 'NS';
      const isEwGreen = activeFrame?.phase === 'GREEN' && activeFrame?.axis === 'EW';
      const isEwYellow = activeFrame?.phase === 'YELLOW' && activeFrame?.axis === 'EW';
      const isAllRed = activeFrame?.phase === 'ALL_RED';

      const corners = [
        { id: 'NW', wx: 300 - 9.5, wy: 300 + 9.5, green: isNsGreen, yellow: isNsYellow, red: isAllRed || isEwGreen || isEwYellow },
        { id: 'NE', wx: 300 + 9.5, wy: 300 + 9.5, green: isEwGreen, yellow: isEwYellow, red: isAllRed || isNsGreen || isNsYellow },
        { id: 'SE', wx: 300 + 9.5, wy: 300 - 9.5, green: isNsGreen, yellow: isNsYellow, red: isAllRed || isEwGreen || isEwYellow },
        { id: 'SW', wx: 300 - 9.5, wy: 300 - 9.5, green: isEwGreen, yellow: isEwYellow, red: isAllRed || isNsGreen || isNsYellow },
      ];
      corners.forEach((c) => {
        const basePt = worldToScreen(c.wx, c.wy, 0);
        const topPt = worldToScreen(c.wx, c.wy, isIso ? 6.5 : 0);
        if (isIso) {
          ctx.strokeStyle = '#475569';
          ctx.lineWidth = 2.5;
          ctx.beginPath();
          ctx.moveTo(basePt.x, basePt.y);
          ctx.lineTo(topPt.x, topPt.y);
          ctx.stroke();
        }
        ctx.fillStyle = '#0f172a';
        ctx.strokeStyle = '#334155';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.roundRect(topPt.x - 5, topPt.y - 11, 10, 22, 3);
        ctx.fill();
        ctx.stroke();

        const rColor = c.red ? '#ef4444' : '#450a0a';
        const aColor = c.yellow ? '#f59e0b' : '#451a03';
        const gColor = c.green ? '#10b981' : '#022c22';

        const drawLens = (offY, color, glow) => {
          ctx.fillStyle = color;
          ctx.beginPath();
          ctx.arc(topPt.x, topPt.y + offY, 2.5, 0, Math.PI * 2);
          ctx.fill();
          if (glow) {
            ctx.save();
            ctx.shadowColor = color;
            ctx.shadowBlur = 10;
            ctx.fillStyle = color;
            ctx.beginPath();
            ctx.arc(topPt.x, topPt.y + offY, 2.8, 0, Math.PI * 2);
            ctx.fill();
            ctx.restore();
          }
        };
        drawLens(-5.5, rColor, c.red);
        drawLens(0, aColor, c.yellow);
        drawLens(5.5, gColor, c.green);
      });
    }

    // ==========================================
    // 2. MICROSCOPIC VEHICLE RENDERING
    // ==========================================
    const vehicles = activeFrame?.vehicles || [];

    vehicles.forEach((v) => {
      // Determine altitude z for Marathahalli flyover vehicles
      let vehZ = 0;
      if (isMarathahalli) {
        const isHeadingEastWest = Math.abs(v.a - 90) < 35 || Math.abs(v.a - 270) < 35;
        if (Math.abs(v.y - 350) <= 7.5 && v.x >= 170 && v.x <= 530 && isHeadingEastWest) {
          if (v.x < 275) {
            vehZ = ((v.x - 170) / (275 - 170)) * 6.5;
          } else if (v.x > 425) {
            vehZ = ((530 - v.x) / (530 - 425)) * 6.5;
          } else {
            vehZ = 7.0;
          }
        }
      }

      const screenPt = worldToScreen(v.x, v.y, vehZ);
      const angle = sumoAngleToScreen(v.a);
      const isAmbulance = Boolean(v.em);

      ctx.save();
      ctx.translate(screenPt.x, screenPt.y);
      ctx.rotate(angle);

      const vehLen = (isAmbulance ? 6.2 : 4.6) * baseScale * (isMarathahalli ? 1.3 : 1.0);
      const vehWid = (isAmbulance ? 2.4 : 1.9) * baseScale * (isMarathahalli ? 1.3 : 1.0);

      if (isAmbulance) {
        // Ambulance V2I Pulse
        const pulseR = (Date.now() / 30) % 35;
        ctx.save();
        ctx.strokeStyle = 'rgba(239, 68, 68, 0.35)';
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.arc(0, 0, pulseR * (baseScale * 0.4), 0, Math.PI * 2);
        ctx.stroke();
        ctx.restore();

        // Ambulance Shadow & Body
        ctx.fillStyle = 'rgba(0, 0, 0, 0.45)';
        ctx.beginPath();
        ctx.roundRect(-vehLen / 2 + 1, -vehWid / 2 + 1, vehLen, vehWid, 2);
        ctx.fill();

        ctx.fillStyle = '#f8fafc';
        ctx.strokeStyle = '#dc2626';
        ctx.lineWidth = 1.2;
        ctx.beginPath();
        ctx.roundRect(-vehLen / 2, -vehWid / 2, vehLen, vehWid, 2);
        ctx.fill();
        ctx.stroke();

        ctx.fillStyle = '#ef4444';
        ctx.fillRect(-vehLen * 0.25, -vehWid / 2, vehLen * 0.5, vehWid);

        const strobeTick = Math.floor(Date.now() / 120) % 2;
        const strobeColor = strobeTick === 0 ? '#ef4444' : '#06b6d4';
        ctx.save();
        ctx.shadowColor = strobeColor;
        ctx.shadowBlur = 14;
        ctx.fillStyle = strobeColor;
        ctx.beginPath();
        ctx.arc(0, 0, 2.5, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
      } else {
        // Passenger Vehicle
        ctx.fillStyle = 'rgba(0, 0, 0, 0.4)';
        ctx.beginPath();
        ctx.roundRect(-vehLen / 2 + 1, -vehWid / 2 + 1, vehLen, vehWid, 1.5);
        ctx.fill();

        const hash = (v.id || '').split('').reduce((acc, c) => acc + c.charCodeAt(0), 0);
        const paints = ['#475569', '#3b82f6', '#0284c7', '#94a3b8', '#0f172a', '#d97706', '#10b981'];
        const carPaint = paints[hash % paints.length];

        ctx.fillStyle = carPaint;
        ctx.beginPath();
        ctx.roundRect(-vehLen / 2, -vehWid / 2, vehLen, vehWid, 2);
        ctx.fill();

        // Windshields
        ctx.fillStyle = '#0f172a';
        ctx.fillRect(vehLen * 0.08, -vehWid * 0.35, vehLen * 0.18, vehWid * 0.7);
        ctx.fillRect(-vehLen * 0.28, -vehWid * 0.35, vehLen * 0.12, vehWid * 0.7);

        // Headlights
        ctx.fillStyle = 'rgba(254, 240, 138, 0.6)';
        ctx.fillRect(vehLen * 0.45, -vehWid * 0.35, 1.5, 1.5);
        ctx.fillRect(vehLen * 0.45, vehWid * 0.35 - 1.5, 1.5, 1.5);

        // Brake lights
        const isBraking = v.s < 0.5 || v.w > 0;
        ctx.fillStyle = isBraking ? '#ef4444' : '#7f1d1d';
        ctx.fillRect(-vehLen * 0.48, -vehWid * 0.35, 1.2, 1.5);
        ctx.fillRect(-vehLen * 0.48, vehWid * 0.35 - 1.5, 1.2, 1.5);
      }

      ctx.restore();
    });

    // ==========================================
    // 3. APPROACH & CORRIDOR TEXT BADGES (LEADER LINES)
    // ==========================================
    if (showLabels) {
      // Draw non-obstructive callout badge with clean leader line
      const drawCallout = (targetWx, targetWy, targetZ, dx, dy, title, subtitle, accentColor) => {
        const targetPt = worldToScreen(targetWx, targetWy, targetZ);
        const badgeX = targetPt.x + dx;
        const badgeY = targetPt.y + dy;

        ctx.save();

        // 1. Subtle Anchor Pin on feature
        ctx.fillStyle = accentColor;
        ctx.beginPath();
        ctx.arc(targetPt.x, targetPt.y, 2.5, 0, Math.PI * 2);
        ctx.fill();

        ctx.strokeStyle = accentColor;
        ctx.lineWidth = 1;
        ctx.globalAlpha = 0.45;
        ctx.beginPath();
        ctx.arc(targetPt.x, targetPt.y, 5, 0, Math.PI * 2);
        ctx.stroke();

        // 2. High-Tech Leader Line with elbow dogleg
        ctx.strokeStyle = accentColor;
        ctx.lineWidth = 1;
        ctx.setLineDash([2, 3]);
        ctx.globalAlpha = 0.65;
        ctx.beginPath();
        ctx.moveTo(targetPt.x, targetPt.y);

        const midX = dx >= 0 ? badgeX - 6 : badgeX + 6;
        const midY = targetPt.y + (dy * 0.45);
        ctx.lineTo(midX, midY);
        ctx.lineTo(midX, badgeY);
        ctx.lineTo(badgeX, badgeY);
        ctx.stroke();

        ctx.setLineDash([]);
        ctx.globalAlpha = 1.0;

        // 3. Compact Badge Box in empty margin space
        ctx.font = '600 10.5px ui-monospace, monospace';
        const titleW = ctx.measureText(title).width;
        ctx.font = '500 9px ui-monospace, monospace';
        const subW = subtitle ? ctx.measureText(subtitle).width : 0;
        const textW = Math.max(titleW, subW);

        const padX = 8;
        const boxW = Math.max(70, textW + padX * 2);
        const boxH = subtitle ? 28 : 20;

        const boxX = dx >= 0 ? badgeX : badgeX - boxW;
        const boxY = badgeY - boxH / 2;

        // Glassmorphic background
        ctx.fillStyle = 'rgba(11, 16, 27, 0.90)';
        ctx.strokeStyle = accentColor;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.roundRect(boxX, boxY, boxW, boxH, 4);
        ctx.fill();
        ctx.stroke();

        // Typography
        ctx.textAlign = 'left';
        ctx.textBaseline = 'top';

        ctx.fillStyle = '#ffffff';
        ctx.font = '600 10px ui-monospace, monospace';
        ctx.fillText(title, boxX + padX, boxY + (subtitle ? 4 : 5));

        if (subtitle) {
          ctx.fillStyle = accentColor;
          ctx.font = '500 9px ui-monospace, monospace';
          ctx.fillText(subtitle, boxX + padX, boxY + 15);
        }

        ctx.restore();
      };

      const q = activeFrame?.queues_m || { N: 0, S: 0, E: 0, W: 0 };
      if (isMarathahalli) {
        // Flyover elevated deck (Z=+7m) — positioned above-left out of road corridor
        drawCallout(
          350, 350, 7.0,
          isIso ? -165 : -150, isIso ? -85 : -70,
          'MARATHAHALLI FLYOVER',
          'Elevated 6-Lane · Free-Flow (Z=+7m)',
          '#38bdf8'
        );

        // Surface Traffic Light Signal (Z=0m) — positioned below-right in open space
        const phaseColor = activeFrame?.phase === 'ALL_RED' ? '#ef4444' : (activeFrame?.phase === 'YELLOW' ? '#f59e0b' : '#10b981');
        drawCallout(
          350, 345, 0.0,
          isIso ? 165 : 150, isIso ? 75 : 65,
          'SURFACE JUNCTION',
          `marathahalli_tls · [${activeFrame?.phase || 'GREEN'}]`,
          phaseColor
        );

        // ORR North (KR Puram) — offset to outside shoulder
        drawCallout(
          350, 520, 0.0,
          isIso ? -145 : -130, isIso ? -35 : -15,
          'ORR NORTH · KR Puram',
          `det_orr_n · Q: ${Number(q.N || 0).toFixed(1)}m`,
          '#38bdf8'
        );

        // ORR South (Kadubeesanahalli) — offset to outside shoulder
        drawCallout(
          350, 180, 0.0,
          isIso ? 145 : 130, isIso ? 35 : 15,
          'ORR SOUTH · Kadubeesanahalli',
          `det_orr_s · Q: ${Number(q.S || 0).toFixed(1)}m`,
          '#38bdf8'
        );

        // East (Whitefield / ITPL) — offset up-right in open space
        drawCallout(
          520, 350, 0.0,
          isIso ? 120 : 110, isIso ? -55 : -40,
          'EAST · Whitefield / ITPL',
          `det_wf · Q: ${Number(q.E || 0).toFixed(1)}m`,
          '#f59e0b'
        );

        // West (HAL Airport Rd) — offset down-left in open space
        drawCallout(
          180, 350, 0.0,
          isIso ? -120 : -110, isIso ? 55 : 40,
          'WEST · HAL Airport Rd',
          `det_hal · Q: ${Number(q.W || 0).toFixed(1)}m`,
          '#f59e0b'
        );
      } else {
        // Synthetic 4-way cross
        drawCallout(300, 430, 0, -110, -25, 'NORTH APPROACH', `det_N · Q: ${Number(q.N || 0).toFixed(1)}m`, '#38bdf8');
        drawCallout(300, 170, 0, 110, 25, 'SOUTH APPROACH', `det_S · Q: ${Number(q.S || 0).toFixed(1)}m`, '#38bdf8');
        drawCallout(430, 300, 0, 100, -35, 'EAST APPROACH', `det_E · Q: ${Number(q.E || 0).toFixed(1)}m`, '#f59e0b');
        drawCallout(170, 300, 0, -100, 35, 'WEST APPROACH', `det_W · Q: ${Number(q.W || 0).toFixed(1)}m`, '#f59e0b');
      }
    }

    // ==========================================
    // 4. ORIENTATION COMPASS ROSE (BOTTOM-LEFT)
    // ==========================================
    const compassX = 42;
    const compassY = h - 42;
    ctx.save();
    ctx.fillStyle = 'rgba(15, 23, 42, 0.75)';
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.15)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.arc(compassX, compassY, 24, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();

    const northHeading = isIso ? -Math.PI / 3 : -Math.PI / 2;
    const arrowLen = 15;
    const nX = compassX + Math.cos(northHeading) * arrowLen;
    const nY = compassY + Math.sin(northHeading) * arrowLen;
    const sX = compassX - Math.cos(northHeading) * (arrowLen * 0.7);
    const sY = compassY - Math.sin(northHeading) * (arrowLen * 0.7);

    // North pointer (Red)
    ctx.strokeStyle = '#ef4444';
    ctx.lineWidth = 2.5;
    ctx.beginPath();
    ctx.moveTo(compassX, compassY);
    ctx.lineTo(nX, nY);
    ctx.stroke();

    // South pointer (Slate)
    ctx.strokeStyle = '#64748b';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(compassX, compassY);
    ctx.lineTo(sX, sY);
    ctx.stroke();

    ctx.fillStyle = '#ef4444';
    ctx.font = 'bold 10px ui-monospace, monospace';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText('N', nX + Math.cos(northHeading) * 7, nY + Math.sin(northHeading) * 7);

    ctx.restore();
  }, [activeFrame, viewMode, showDetectors, showLabels, isMarathahalli, zoom, pan]);

  // Scrub bar helpers
  const totalFrames = replayData?.frames?.length || 1;
  const progressPercent = totalFrames > 1 ? (currentFrameIdx / (totalFrames - 1)) * 100 : 0;

  const formatSimTime = (s) => {
    const totalSec = Math.floor(s || 0);
    const m = Math.floor(totalSec / 60);
    const sec = totalSec % 60;
    return `${m}:${sec.toString().padStart(2, '0')}`;
  };

  return (
    <div className={`relative bg-[#0b101b] border border-white/10 rounded-xl overflow-hidden shadow-2xl flex flex-col ${className}`}>
      {/* --- TOP HUD BAR --- */}
      <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-3 bg-[#0e1524]/90 border-b border-white/10 backdrop-blur z-10 text-xs">
        {/* Left: Run info & Mode */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse shadow-[0_0_8px_#34d399]" />
            <span className="font-semibold text-slate-100 tracking-wide uppercase text-[11px]">
              {isLiveMode ? 'Live TraCI Simulation Twin' : 'Verified TraCI Microscopic Replay'}
            </span>
          </div>

          <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 bg-white/5 border border-white/10 rounded font-mono text-[11px] text-slate-300">
            <span className="text-slate-400">Run:</span>
            <span className="font-bold text-white">{runId}</span>
          </div>

          {availableRuns.length > 0 && onRunChange && !isLiveMode && (
            <select
              value={runId}
              onChange={(e) => onRunChange(e.target.value)}
              aria-label="Select simulation run"
              className="px-2 py-1 bg-slate-900 border border-white/15 rounded text-[11px] font-mono text-slate-200 focus:outline-none focus:border-blue-500"
            >
              {availableRuns.map((r) => (
                <option key={r.id || r} value={r.id || r}>
                  {r.label || r.id || r}
                </option>
              ))}
            </select>
          )}
        </div>

        {/* Center: Phase & Time Telemetry */}
        <div className="flex items-center gap-3">
          {/* Active Phase Pill */}
          <div
            className={`flex items-center gap-2 px-3 py-1 rounded-full font-mono text-[11px] font-bold border transition-colors ${
              activeFrame?.phase === 'ALL_RED'
                ? 'bg-red-950/70 border-red-500/50 text-red-300 shadow-[0_0_12px_rgba(239,68,68,0.3)]'
                : activeFrame?.phase === 'YELLOW'
                ? 'bg-amber-950/70 border-amber-500/50 text-amber-300 shadow-[0_0_12px_rgba(245,158,11,0.3)]'
                : 'bg-emerald-950/70 border-emerald-500/50 text-emerald-300 shadow-[0_0_12px_rgba(16,185,129,0.3)]'
            }`}
          >
            <span>{activeFrame?.phase || 'IDLE'}</span>
            <span className="text-[10px] opacity-75">[{activeFrame?.axis || '—'}]</span>
          </div>

          {/* Sim Clock */}
          <div className="flex items-center gap-1.5 px-2.5 py-1 bg-slate-900/90 border border-white/10 rounded font-mono text-xs">
            <span className="text-slate-400">t:</span>
            <span className="font-bold text-blue-400">
              {Number(activeFrame?.t || 0).toFixed(1)}s
            </span>
          </div>

          {/* Active Vehicles count */}
          <div className="hidden md:flex items-center gap-1 px-2 py-1 bg-white/5 rounded text-[11px] font-mono text-slate-400">
            <Gauge size={12} className="text-slate-400" />
            <span>{activeFrame?.vehicles?.length || 0} active vehs</span>
          </div>
        </div>

        {/* Right: Camera View & Zoom Controls */}
        <div className="flex items-center gap-2">
          {/* Zoom Controls */}
          <div className="flex items-center bg-slate-900 border border-white/10 rounded overflow-hidden p-0.5">
            <button
              onClick={handleZoomIn}
              title="Zoom In (Scroll Up or +)"
              className="p-1 hover:bg-white/10 text-slate-300 hover:text-white transition-colors"
            >
              <ZoomIn size={13} />
            </button>
            <button
              onClick={handleResetView}
              title="Reset Zoom & Pan (Double Click Canvas)"
              className="px-2 py-0.5 text-[11px] font-mono font-bold text-blue-400 hover:text-blue-300 transition-colors"
            >
              {Math.round(zoom * 100)}%
            </button>
            <button
              onClick={handleZoomOut}
              title="Zoom Out (Scroll Down or -)"
              className="p-1 hover:bg-white/10 text-slate-300 hover:text-white transition-colors"
            >
              <ZoomOut size={13} />
            </button>
          </div>

          <button
            onClick={handleResetView}
            title="Reset View / Fit to screen"
            className={`p-1.5 rounded border transition-colors ${
              zoom !== 1.0 || pan.x !== 0 || pan.y !== 0
                ? 'bg-blue-950/70 border-blue-500/50 text-blue-300'
                : 'bg-slate-900 border-white/10 text-slate-400 hover:text-slate-200'
            }`}
          >
            <RotateCcw size={13} />
          </button>

          {/* Isometric / Top-Down Switcher */}
          <div className="flex items-center bg-slate-900 border border-white/10 rounded p-0.5">
            <button
              onClick={() => setViewMode('isometric')}
              className={`px-2.5 py-1 text-[11px] font-medium rounded transition-colors ${
                viewMode === 'isometric'
                  ? 'bg-blue-600 text-white font-semibold'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              2.5D Isometric
            </button>
            <button
              onClick={() => setViewMode('topdown')}
              className={`px-2.5 py-1 text-[11px] font-medium rounded transition-colors ${
                viewMode === 'topdown'
                  ? 'bg-blue-600 text-white font-semibold'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Top-Down
            </button>
          </div>

          {/* Labels Toggle */}
          <button
            onClick={() => setShowLabels((v) => !v)}
            title={showLabels ? "Hide road and feature labels (clean view)" : "Show road and feature labels"}
            className={`px-2 py-1 flex items-center gap-1 rounded border text-[11px] font-medium transition-colors ${
              showLabels
                ? 'bg-blue-950/70 border-blue-500/50 text-blue-300 shadow-[0_0_8px_rgba(59,130,246,0.3)]'
                : 'bg-slate-900 border-white/10 text-slate-400 hover:text-slate-200'
            }`}
          >
            <Tag size={12} />
            <span className="hidden sm:inline">Labels {showLabels ? 'ON' : 'OFF'}</span>
          </button>

          {/* Sensor Zones Toggle */}
          <button
            onClick={() => setShowDetectors((v) => !v)}
            title="Toggle E2 detector sensor zones"
            className={`p-1.5 rounded border transition-colors ${
              showDetectors
                ? 'bg-blue-950/60 border-blue-500/40 text-blue-300'
                : 'bg-slate-900 border-white/10 text-slate-400'
            }`}
          >
            <Layers size={13} />
          </button>
        </div>
      </div>

      {/* --- EMERGENCY PRIORITY BANNER (EVSP) --- */}
      {activeFrame?.emergency_approaching && (
        <div className="px-4 py-2 bg-gradient-to-r from-red-950/90 via-red-900/80 to-red-950/90 border-b border-red-500/50 flex items-center justify-between text-xs text-red-100 animate-pulse z-10 shadow-lg">
          <div className="flex items-center gap-2.5 font-semibold">
            <Siren size={16} className="text-red-400 animate-bounce" />
            <span>EVSP ACTIVE: Emergency Vehicle Approaching (North Approach)</span>
            <span className="hidden sm:inline text-red-300 font-mono text-[11px]">
              • Priority green held until clearance
            </span>
          </div>
          {activeFrame.emergency_dist_m !== null && (
            <div className="flex items-center gap-1.5 font-mono font-bold text-red-200 bg-red-950 px-2.5 py-0.5 rounded border border-red-500/40">
              <span>{Number(activeFrame.emergency_dist_m).toFixed(1)}m</span>
              <span className="text-[10px] text-red-400 font-normal">to stop line</span>
            </div>
          )}
        </div>
      )}

      {/* --- CANVAS VIEWPORT --- */}
      <div ref={containerRef} className="relative w-full h-[500px] md:h-[560px] flex-1 overflow-hidden">
        <canvas
          ref={canvasRef}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          onDoubleClick={handleResetView}
          className={`w-full h-full block select-none ${
            isDragging ? 'cursor-grabbing' : 'cursor-grab'
          }`}
        />

        {/* Floating Quick Camera Toolbar (Top-Right of Viewport) */}
        <div className="absolute top-3 right-3 flex items-center gap-1.5 bg-[#0e1524]/90 border border-white/10 rounded-lg p-1 backdrop-blur shadow-2xl z-20">
          <button
            onClick={handleZoomIn}
            title="Zoom In (Scroll Up or +)"
            className="p-1.5 hover:bg-white/10 text-slate-300 hover:text-white rounded transition-colors"
          >
            <ZoomIn size={14} />
          </button>
          <button
            onClick={handleResetView}
            title="Double-click to reset zoom & pan"
            className="px-2 py-0.5 text-[11px] font-mono font-bold text-blue-400 hover:text-blue-300 transition-colors"
          >
            {Math.round(zoom * 100)}%
          </button>
          <button
            onClick={handleZoomOut}
            title="Zoom Out (Scroll Down or -)"
            className="p-1.5 hover:bg-white/10 text-slate-300 hover:text-white rounded transition-colors"
          >
            <ZoomOut size={14} />
          </button>
          <div className="w-px h-3.5 bg-white/15 mx-0.5" />
          <button
            onClick={handleResetView}
            title="Fit to Screen / Center View"
            className={`p-1.5 rounded transition-colors ${
              zoom !== 1.0 || pan.x !== 0 || pan.y !== 0
                ? 'bg-blue-600/30 text-blue-300'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <RotateCcw size={13} />
          </button>
          <button
            onClick={() => setShowLabels((v) => !v)}
            title={showLabels ? "Hide Labels (Pure Road View)" : "Show Labels"}
            className={`px-2 py-1 flex items-center gap-1 text-[11px] rounded transition-colors ${
              showLabels
                ? 'bg-blue-600/30 text-blue-300 font-semibold'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Tag size={12} />
            <span>Labels</span>
          </button>
        </div>

        {/* Loading Overlay */}
        {loadingReplay && (
          <div className="absolute inset-0 bg-slate-950/70 backdrop-blur-sm flex flex-col items-center justify-center gap-3 z-20">
            <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
            <span className="text-xs font-mono text-slate-300 tracking-wide">
              Loading TraCI Microscopic Replay...
            </span>
          </div>
        )}

        {/* Floating Queue Radar overlay (bottom right) */}
        {activeFrame?.queues_m && (
          <div className="absolute bottom-3 right-3 bg-slate-950/85 border border-white/10 rounded-lg p-2.5 backdrop-blur font-mono text-[11px] space-y-1 z-10 hidden sm:block">
            <div className="text-[10px] uppercase tracking-wider text-slate-400 font-semibold mb-1 flex items-center gap-1">
              <Activity size={11} className="text-blue-400" />
              <span>{isMarathahalli ? 'Stop-Line Queues (E2 25m)' : 'Queue Lengths (E2 150m)'}</span>
            </div>
            <div className="grid grid-cols-2 gap-x-3 gap-y-0.5 text-slate-300">
              <div>{isMarathahalli ? 'ORR-N:' : 'N:'} <span className="text-white font-bold">{Number(activeFrame.queues_m.N || 0).toFixed(1)}m</span></div>
              <div>{isMarathahalli ? 'ORR-S:' : 'S:'} <span className="text-white font-bold">{Number(activeFrame.queues_m.S || 0).toFixed(1)}m</span></div>
              <div>{isMarathahalli ? 'WF (E):' : 'E:'} <span className="text-white font-bold">{Number(activeFrame.queues_m.E || 0).toFixed(1)}m</span></div>
              <div>{isMarathahalli ? 'HAL (W):' : 'W:'} <span className="text-white font-bold">{Number(activeFrame.queues_m.W || 0).toFixed(1)}m</span></div>
            </div>
          </div>
        )}
      </div>

      {/* --- BOTTOM PLAYER CONTROLS (FOR REPLAY MODE) --- */}
      {!isLiveMode && replayData && replayData.frames && (
        <div className="px-4 py-3 bg-[#0a0f1a] border-t border-white/10 flex flex-col gap-2 z-10 text-xs">
          {/* Timeline Scrub Slider */}
          <div className="flex items-center gap-3 w-full">
            <span className="font-mono text-[11px] text-slate-400 w-12 text-right">
              {formatSimTime(activeFrame?.t)}
            </span>
            <div className="relative flex-1 flex items-center group">
              <input
                type="range"
                min="0"
                max={Math.max(0, replayData.frames.length - 1)}
                value={currentFrameIdx}
                onChange={(e) => {
                  setCurrentFrameIdx(Number(e.target.value));
                  setIsPlaying(false);
                }}
                className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-blue-500 focus:outline-none"
              />
            </div>
            <span className="font-mono text-[11px] text-slate-400 w-12">
              {formatSimTime(replayData.duration_s)}
            </span>
          </div>

          {/* Buttons Strip */}
          <div className="flex flex-wrap items-center justify-between gap-3 pt-1">
            <div className="flex items-center gap-2">
              {/* Play / Pause */}
              <button
                onClick={() => setIsPlaying((v) => !v)}
                className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded font-medium flex items-center gap-1.5 transition-colors shadow"
              >
                {isPlaying ? <Pause size={13} /> : <Play size={13} />}
                <span>{isPlaying ? 'Pause' : 'Play'}</span>
              </button>

              {/* Step Backward / Forward */}
              <button
                onClick={() => {
                  setIsPlaying(false);
                  setCurrentFrameIdx((p) => Math.max(0, p - 1));
                }}
                title="Step -1s"
                className="p-1.5 bg-slate-900 hover:bg-slate-800 border border-white/10 rounded text-slate-300"
              >
                <ChevronLeft size={14} />
              </button>
              <button
                onClick={() => {
                  setIsPlaying(false);
                  setCurrentFrameIdx((p) => Math.min(replayData.frames.length - 1, p + 1));
                }}
                title="Step +1s"
                className="p-1.5 bg-slate-900 hover:bg-slate-800 border border-white/10 rounded text-slate-300"
              >
                <ChevronRight size={14} />
              </button>

              {/* Reset to Start */}
              <button
                onClick={() => {
                  setCurrentFrameIdx(0);
                  setIsPlaying(true);
                }}
                title="Reset to t=0"
                className="p-1.5 bg-slate-900 hover:bg-slate-800 border border-white/10 rounded text-slate-300"
              >
                <RotateCcw size={14} />
              </button>
            </div>

            {/* Playback Speed Selectors */}
            <div className="flex items-center gap-1 bg-slate-950 border border-white/10 rounded p-0.5">
              {[0.5, 1, 2, 5, 10].map((spd) => (
                <button
                  key={spd}
                  onClick={() => setPlaybackSpeed(spd)}
                  className={`px-2 py-0.5 rounded text-[11px] font-mono transition-colors ${
                    playbackSpeed === spd
                      ? 'bg-blue-600 text-white font-bold'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {spd}x
                </button>
              ))}
            </div>

            {/* Integrity Notice */}
            <div className="hidden lg:flex items-center gap-1.5 text-[11px] text-slate-400">
              <Shield size={12} className="text-emerald-400" />
              <span>100% SUMO TraCI Microscopic Coordinates</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default IsometricIntersection;
