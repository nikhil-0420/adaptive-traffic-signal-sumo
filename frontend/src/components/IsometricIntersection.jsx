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
  Gauge
} from 'lucide-react';
import { api } from '../api/client';

export function IsometricIntersection({
  runId = 'imbalanced_ns_adaptive_s1',
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

  // Animation Loop Ref
  const animFrameRef = useRef(null);
  const lastTickTimeRef = useRef(Date.now());
  const frameAccumulatorRef = useRef(0);

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

    if (canvas.width !== Math.floor(w * dpr) || canvas.height !== Math.floor(h * dpr)) {
      canvas.width = Math.floor(w * dpr);
      canvas.height = Math.floor(h * dpr);
    }

    ctx.save();
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, w, h);

    // Background Gradient (Deep Cockpit Blue-Gray)
    const bgGrad = ctx.createRadialGradient(w / 2, h / 2, 20, w / 2, h / 2, Math.max(w, h));
    bgGrad.addColorStop(0, '#0f1624');
    bgGrad.addColorStop(1, '#080c14');
    ctx.fillStyle = bgGrad;
    ctx.fillRect(0, 0, w, h);

    const cx = w / 2;
    const cy = h / 2;

    // Scale calculation: SUMO world is 600m x 600m, center is (300, 300).
    // Viewport covers center +- 160m to display 150m detector queues.
    const isIso = viewMode === 'isometric';
    const viewSpanM = 280; // metres visible from center to arm tip
    const baseScale = Math.min(w, h) / (viewSpanM * 1.85);

    // Coordinate transforms
    const worldToScreen = (wx, wy, z = 0) => {
      const u = wx - 300.0;
      const v = wy - 300.0;
      if (!isIso) {
        // Orthographic Top-Down (SUMO: +y is North, canvas: +y is Down)
        return {
          x: cx + u * baseScale,
          y: cy - v * baseScale - z * baseScale,
        };
      }
      // Isometric 2.5D: 30 degree tilt
      const cos30 = Math.cos(Math.PI / 6);
      const sin30 = Math.sin(Math.PI / 6);
      const isoX = (u - v) * cos30;
      const isoY = (u + v) * sin30;
      return {
        x: cx + isoX * baseScale,
        y: cy - (isoY * baseScale * 0.72) - z * baseScale,
      };
    };

    // Vector angle transform to screen heading
    const sumoAngleToScreen = (deg) => {
      const rad = (deg * Math.PI) / 180;
      // In SUMO: 0=N, 90=E, 180=S, 270=W
      const vx = Math.sin(rad);
      const vy = Math.cos(rad);
      const p1 = worldToScreen(300, 300);
      const p2 = worldToScreen(300 + vx * 10, 300 + vy * 10);
      return Math.atan2(p2.y - p1.y, p2.x - p1.x);
    };

    // 1. Draw Ground Grid & Terrain Accents
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.03)';
    ctx.lineWidth = 1;
    const gridStep = 40;
    for (let gx = -240; gx <= 240; gx += gridStep) {
      const pA = worldToScreen(300 + gx, 300 - 240);
      const pB = worldToScreen(300 + gx, 300 + 240);
      ctx.beginPath();
      ctx.moveTo(pA.x, pA.y);
      ctx.lineTo(pB.x, pB.y);
      ctx.stroke();

      const pC = worldToScreen(300 - 240, 300 + gx);
      const pD = worldToScreen(300 + 240, 300 + gx);
      ctx.beginPath();
      ctx.moveTo(pC.x, pC.y);
      ctx.lineTo(pD.x, pD.y);
      ctx.stroke();
    }

    // 2. Draw Road Surfaces
    // Road width: 4 lanes * 3.2m = 12.8m + curbs = 15m. Half-width = 7.5m
    const rw = 7.5;
    const armL = 220; // 220m road length

    const drawRoadQuad = (x1, y1, x2, y2, x3, y3, x4, y4, fill) => {
      const p1 = worldToScreen(x1, y1);
      const p2 = worldToScreen(x2, y2);
      const p3 = worldToScreen(x3, y3);
      const p4 = worldToScreen(x4, y4);
      ctx.fillStyle = fill;
      ctx.beginPath();
      ctx.moveTo(p1.x, p1.y);
      ctx.lineTo(p2.x, p2.y);
      ctx.lineTo(p3.x, p3.y);
      ctx.lineTo(p4.x, p4.y);
      ctx.closePath();
      ctx.fill();
    };

    // Curbs / Sidewalk base (slightly wider)
    const curbW = rw + 2.2;
    drawRoadQuad(300 - curbW, 300 - armL, 300 + curbW, 300 - armL, 300 + curbW, 300 + armL, 300 - curbW, 300 + armL, '#131b29');
    drawRoadQuad(300 - armL, 300 - curbW, 300 + armL, 300 - curbW, 300 + armL, 300 + curbW, 300 - armL, 300 + curbW, '#131b29');

    // Asphalt Main Deck
    const asphaltColor = '#1a2333';
    drawRoadQuad(300 - rw, 300 - armL, 300 + rw, 300 - armL, 300 + rw, 300 + armL, 300 - rw, 300 + armL, asphaltColor);
    drawRoadQuad(300 - armL, 300 - rw, 300 + armL, 300 - rw, 300 + armL, 300 + rw, 300 - armL, 300 + rw, asphaltColor);

    // Conflict Box Center (Intersection Box)
    const pC1 = worldToScreen(300 - rw, 300 - rw);
    const pC2 = worldToScreen(300 + rw, 300 - rw);
    const pC3 = worldToScreen(300 + rw, 300 + rw);
    const pC4 = worldToScreen(300 - rw, 300 + rw);
    ctx.fillStyle = '#202b3f';
    ctx.beginPath();
    ctx.moveTo(pC1.x, pC1.y);
    ctx.lineTo(pC2.x, pC2.y);
    ctx.lineTo(pC3.x, pC3.y);
    ctx.lineTo(pC4.x, pC4.y);
    ctx.closePath();
    ctx.fill();

    // Center Cross-hatch Yellow Box
    ctx.strokeStyle = 'rgba(234, 179, 8, 0.22)';
    ctx.lineWidth = 1;
    ctx.stroke();

    // 3. Road Markings: Yellow Double Centerlines & White Dashed Lanes
    const drawLine = (x1, y1, x2, y2, color, width, dash = []) => {
      const pA = worldToScreen(x1, y1);
      const pB = worldToScreen(x2, y2);
      ctx.strokeStyle = color;
      ctx.lineWidth = width;
      ctx.setLineDash(dash);
      ctx.beginPath();
      ctx.moveTo(pA.x, pA.y);
      ctx.lineTo(pB.x, pB.y);
      ctx.stroke();
      ctx.setLineDash([]);
    };

    // Center double yellow lines
    // North Arm (y > 300 + rw)
    drawLine(300 - 0.15, 300 + rw, 300 - 0.15, 300 + armL, 'rgba(245, 158, 11, 0.75)', 1.5);
    drawLine(300 + 0.15, 300 + rw, 300 + 0.15, 300 + armL, 'rgba(245, 158, 11, 0.75)', 1.5);
    // South Arm (y < 300 - rw)
    drawLine(300 - 0.15, 300 - armL, 300 - 0.15, 300 - rw, 'rgba(245, 158, 11, 0.75)', 1.5);
    drawLine(300 + 0.15, 300 - armL, 300 + 0.15, 300 - rw, 'rgba(245, 158, 11, 0.75)', 1.5);
    // East Arm (x > 300 + rw)
    drawLine(300 + rw, 300 - 0.15, 300 + armL, 300 - 0.15, 'rgba(245, 158, 11, 0.75)', 1.5);
    drawLine(300 + rw, 300 + 0.15, 300 + armL, 300 + 0.15, 'rgba(245, 158, 11, 0.75)', 1.5);
    // West Arm (x < 300 - rw)
    drawLine(300 - armL, 300 - 0.15, 300 - rw, 300 - 0.15, 'rgba(245, 158, 11, 0.75)', 1.5);
    drawLine(300 - armL, 300 + 0.15, 300 - rw, 300 + 0.15, 'rgba(245, 158, 11, 0.75)', 1.5);

    // White dashed lane dividers (between lane 0 and lane 1, 3.2m from center)
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

    // 4. Zebra Crosswalk Stripes & Stop Bars
    const drawCrosswalk = (cx1, cy1, cx2, cy2, isHoriz) => {
      const stripes = 6;
      for (let s = 0; s < stripes; s++) {
        const t = (s + 0.5) / stripes;
        if (isHoriz) {
          const sx = cx1 + (cx2 - cx1) * t;
          drawLine(sx, cy1 - 1.5, sx, cy1 + 1.5, 'rgba(255, 255, 255, 0.75)', 2.5);
        } else {
          const sy = cy1 + (cy2 - cy1) * t;
          drawLine(cx1 - 1.5, sy, cx1 + 1.5, sy, 'rgba(255, 255, 255, 0.75)', 2.5);
        }
      }
    };

    // North Stop Line & Zebra (at y = 300 + rw + 2)
    drawLine(300 - rw, 300 + rw + 4, 300, 300 + rw + 4, 'rgba(255, 255, 255, 0.95)', 3);
    drawCrosswalk(300 - rw, 300 + rw + 1.8, 300 + rw, 300 + rw + 1.8, true);

    // South Stop Line & Zebra (at y = 300 - rw - 2)
    drawLine(300, 300 - rw - 4, 300 + rw, 300 - rw - 4, 'rgba(255, 255, 255, 0.95)', 3);
    drawCrosswalk(300 - rw, 300 - rw - 1.8, 300 + rw, 300 - rw - 1.8, true);

    // East Stop Line & Zebra (at x = 300 + rw + 2)
    drawLine(300 + rw + 4, 300, 300 + rw + 4, 300 + rw, 'rgba(255, 255, 255, 0.95)', 3);
    drawCrosswalk(300 + rw + 1.8, 300 - rw, 300 + rw + 1.8, 300 + rw, false);

    // West Stop Line & Zebra (at x = 300 - rw - 2)
    drawLine(300 - rw - 4, 300 - rw, 300 - rw - 4, 300, 'rgba(255, 255, 255, 0.95)', 3);
    drawCrosswalk(300 - rw - 1.8, 300 - rw, 300 - rw - 1.8, 300 + rw, false);

    // 5. Draw 150m E2 LaneArea Detector Zones & Real Queue Length Fill
    if (showDetectors && activeFrame) {
      const qN = activeFrame.queues_m?.N || 0;
      const qS = activeFrame.queues_m?.S || 0;
      const qE = activeFrame.queues_m?.E || 0;
      const qW = activeFrame.queues_m?.W || 0;

      const detLen = 150.0; // 150m standard detector length

      // North Inbound Detector: x in [300 - 6.4, 300], y in [300 + rw + 4, 300 + rw + 4 + detLen]
      const nStop = 300 + rw + 4;
      // Detector box outline
      drawRoadQuad(300 - 6.4, nStop, 300, nStop, 300, nStop + detLen, 300 - 6.4, nStop + detLen, 'rgba(56, 189, 248, 0.05)');
      // Queue accumulation fill (amber to red gradient)
      if (qN > 0) {
        const fillN = Math.min(detLen, qN);
        drawRoadQuad(300 - 6.4, nStop, 300, nStop, 300, nStop + fillN, 300 - 6.4, nStop + fillN, 'rgba(239, 68, 68, 0.28)');
      }

      // South Inbound Detector: x in [300, 300 + 6.4], y in [300 - rw - 4 - detLen, 300 - rw - 4]
      const sStop = 300 - rw - 4;
      drawRoadQuad(300, sStop - detLen, 300 + 6.4, sStop - detLen, 300 + 6.4, sStop, 300, sStop, 'rgba(56, 189, 248, 0.05)');
      if (qS > 0) {
        const fillS = Math.min(detLen, qS);
        drawRoadQuad(300, sStop - fillS, 300 + 6.4, sStop - fillS, 300 + 6.4, sStop, 300, sStop, 'rgba(239, 68, 68, 0.28)');
      }

      // East Inbound Detector: x in [300 + rw + 4, 300 + rw + 4 + detLen], y in [300, 300 + 6.4]
      const eStop = 300 + rw + 4;
      drawRoadQuad(eStop, 300, eStop + detLen, 300, eStop + detLen, 300 + 6.4, eStop, 300 + 6.4, 'rgba(56, 189, 248, 0.05)');
      if (qE > 0) {
        const fillE = Math.min(detLen, qE);
        drawRoadQuad(eStop, 300, eStop + fillE, 300, eStop + fillE, 300 + 6.4, eStop, 300 + 6.4, 'rgba(239, 68, 68, 0.28)');
      }

      // West Inbound Detector: x in [300 - rw - 4 - detLen, 300 - rw - 4], y in [300 - 6.4, 300]
      const wStop = 300 - rw - 4;
      drawRoadQuad(wStop - detLen, 300 - 6.4, wStop, 300 - 6.4, wStop, 300, wStop - detLen, 300, 'rgba(56, 189, 248, 0.05)');
      if (qW > 0) {
        const fillW = Math.min(detLen, qW);
        drawRoadQuad(wStop - fillW, 300 - 6.4, wStop, 300 - 6.4, wStop, 300, wStop - fillW, 300, 'rgba(239, 68, 68, 0.28)');
      }
    }

    // 6. Draw 3D Signal Light Heads on Corner Poles
    // TraCI tl_state has 16 chars: 4 signals (North, East, South, West), each 4 links (e.g. 'GGggrrrrGGggrrrr')
    const tl = activeFrame?.tl_state || 'GGggrrrrGGggrrrr';
    const isNsGreen = activeFrame?.phase === 'GREEN' && activeFrame?.axis === 'NS';
    const isNsYellow = activeFrame?.phase === 'YELLOW' && activeFrame?.axis === 'NS';
    const isEwGreen = activeFrame?.phase === 'GREEN' && activeFrame?.axis === 'EW';
    const isEwYellow = activeFrame?.phase === 'YELLOW' && activeFrame?.axis === 'EW';
    const isAllRed = activeFrame?.phase === 'ALL_RED';

    // Corner signal posts at (300 +- 9, 300 +- 9)
    const corners = [
      { id: 'NW', wx: 300 - 9.5, wy: 300 + 9.5, green: isNsGreen, yellow: isNsYellow, red: isAllRed || isEwGreen || isEwYellow },
      { id: 'NE', wx: 300 + 9.5, wy: 300 + 9.5, green: isEwGreen, yellow: isEwYellow, red: isAllRed || isNsGreen || isNsYellow },
      { id: 'SE', wx: 300 + 9.5, wy: 300 - 9.5, green: isNsGreen, yellow: isNsYellow, red: isAllRed || isEwGreen || isEwYellow },
      { id: 'SW', wx: 300 - 9.5, wy: 300 - 9.5, green: isEwGreen, yellow: isEwYellow, red: isAllRed || isNsGreen || isNsYellow },
    ];

    corners.forEach((c) => {
      const basePt = worldToScreen(c.wx, c.wy, 0);
      const topPt = worldToScreen(c.wx, c.wy, isIso ? 6.5 : 0);

      // Pole
      if (isIso) {
        ctx.strokeStyle = '#475569';
        ctx.lineWidth = 2.5;
        ctx.beginPath();
        ctx.moveTo(basePt.x, basePt.y);
        ctx.lineTo(topPt.x, topPt.y);
        ctx.stroke();
      }

      // Signal Head Housing
      const headW = isIso ? 10 : 8;
      const headH = isIso ? 22 : 18;
      ctx.fillStyle = '#0f172a';
      ctx.strokeStyle = '#334155';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.roundRect(topPt.x - headW / 2, topPt.y - headH / 2, headW, headH, 3);
      ctx.fill();
      ctx.stroke();

      // 3 Lenses: Red (top), Amber (mid), Green (bot)
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

    // 7. Active Signal Ground Light Wash (Green flow beam)
    if (isNsGreen || isEwGreen) {
      const glowAxis = isNsGreen ? 'NS' : 'EW';
      const pG1 = worldToScreen(glowAxis === 'NS' ? 300 - rw : 300 - rw, glowAxis === 'NS' ? 300 - rw : 300 - rw);
      const pG2 = worldToScreen(glowAxis === 'NS' ? 300 + rw : 300 + rw, glowAxis === 'NS' ? 300 + rw : 300 + rw);
      const gWash = ctx.createRadialGradient(cx, cy, 5, cx, cy, 45);
      gWash.addColorStop(0, 'rgba(16, 185, 129, 0.22)');
      gWash.addColorStop(1, 'rgba(16, 185, 129, 0)');
      ctx.fillStyle = gWash;
      ctx.fillRect(cx - 50, cy - 50, 100, 100);
    }

    // 8. Draw Microscopic Real Vehicles
    const vehicles = activeFrame?.vehicles || [];

    vehicles.forEach((v) => {
      const screenPt = worldToScreen(v.x, v.y, isIso ? 0.8 : 0);
      const angle = sumoAngleToScreen(v.a);
      const isAmbulance = Boolean(v.em);

      ctx.save();
      ctx.translate(screenPt.x, screenPt.y);
      ctx.rotate(angle);

      const vehLen = (isAmbulance ? 6.2 : 4.6) * baseScale;
      const vehWid = (isAmbulance ? 2.4 : 1.9) * baseScale;

      if (isAmbulance) {
        // --- EMERGENCY AMBULANCE ---
        // V2I Radio Beacon Wave (pulsing circle)
        const pulseR = (Date.now() / 30) % 35;
        ctx.save();
        ctx.strokeStyle = 'rgba(239, 68, 68, 0.35)';
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.arc(0, 0, pulseR * (baseScale * 0.4), 0, Math.PI * 2);
        ctx.stroke();
        ctx.restore();

        // Ambulance Shadow
        ctx.fillStyle = 'rgba(0, 0, 0, 0.45)';
        ctx.beginPath();
        ctx.roundRect(-vehLen / 2 + 1, -vehWid / 2 + 1, vehLen, vehWid, 2);
        ctx.fill();

        // Ambulance Body (Arctic White with Red Livery)
        ctx.fillStyle = '#f8fafc';
        ctx.strokeStyle = '#dc2626';
        ctx.lineWidth = 1.2;
        ctx.beginPath();
        ctx.roundRect(-vehLen / 2, -vehWid / 2, vehLen, vehWid, 2);
        ctx.fill();
        ctx.stroke();

        // Red Chevron / Side Stripe
        ctx.fillStyle = '#ef4444';
        ctx.fillRect(-vehLen * 0.25, -vehWid / 2, vehLen * 0.5, vehWid);

        // Windshield Glass
        ctx.fillStyle = '#0ea5e9';
        ctx.fillRect(vehLen * 0.2, -vehWid * 0.35, vehLen * 0.18, vehWid * 0.7);

        // Medical Cross on Roof
        ctx.fillStyle = '#ef4444';
        const crossW = vehLen * 0.16;
        const crossH = vehWid * 0.16;
        ctx.fillRect(-crossW / 2, -crossH * 1.6, crossW, crossH * 3.2);
        ctx.fillRect(-crossW * 1.6, -crossH / 2, crossW * 3.2, crossH);

        // Dual Flashing Strobe (alternating Red / Cyan)
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

        // High-beam Headlights
        ctx.fillStyle = 'rgba(254, 240, 138, 0.75)';
        ctx.fillRect(vehLen * 0.46, -vehWid * 0.35, 2, 2);
        ctx.fillRect(vehLen * 0.46, vehWid * 0.35 - 2, 2, 2);
      } else {
        // --- STANDARD PASSENGER CAR ---
        // Vehicle Shadow
        ctx.fillStyle = 'rgba(0, 0, 0, 0.4)';
        ctx.beginPath();
        ctx.roundRect(-vehLen / 2 + 1, -vehWid / 2 + 1, vehLen, vehWid, 1.5);
        ctx.fill();

        // Deterministic paint color from vehicle ID
        const hash = (v.id || '').split('').reduce((acc, c) => acc + c.charCodeAt(0), 0);
        const paints = ['#475569', '#3b82f6', '#0284c7', '#94a3b8', '#0f172a', '#d97706'];
        const carPaint = paints[hash % paints.length];

        ctx.fillStyle = carPaint;
        ctx.beginPath();
        ctx.roundRect(-vehLen / 2, -vehWid / 2, vehLen, vehWid, 2);
        ctx.fill();

        // Windshield Glass (Front & Rear)
        ctx.fillStyle = '#0f172a';
        ctx.fillRect(vehLen * 0.08, -vehWid * 0.35, vehLen * 0.18, vehWid * 0.7);
        ctx.fillRect(-vehLen * 0.28, -vehWid * 0.35, vehLen * 0.12, vehWid * 0.7);

        // Front Headlights
        ctx.fillStyle = 'rgba(254, 240, 138, 0.6)';
        ctx.fillRect(vehLen * 0.45, -vehWid * 0.35, 1.5, 1.5);
        ctx.fillRect(vehLen * 0.45, vehWid * 0.35 - 1.5, 1.5, 1.5);

        // Rear Tail Red Lights (bright red when stopping / waiting)
        const isBraking = v.s < 0.5 || v.w > 0;
        ctx.fillStyle = isBraking ? '#ef4444' : '#7f1d1d';
        ctx.fillRect(-vehLen * 0.48, -vehWid * 0.35, 1.2, 1.5);
        ctx.fillRect(-vehLen * 0.48, vehWid * 0.35 - 1.5, 1.2, 1.5);
      }

      ctx.restore();
    });

    // 9. Approach Arm Directional Text Badges
    if (showLabels) {
      const drawArmTag = (label, qVal, wx, wy, align) => {
        const pt = worldToScreen(wx, wy);
        ctx.font = '600 11px ui-monospace, monospace';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';

        const tagText = `${label} (${Number(qVal || 0).toFixed(1)}m)`;
        const tagW = ctx.measureText(tagText).width + 14;

        ctx.fillStyle = 'rgba(15, 23, 42, 0.85)';
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.15)';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.roundRect(pt.x - tagW / 2, pt.y - 10, tagW, 20, 4);
        ctx.fill();
        ctx.stroke();

        ctx.fillStyle = '#94a3b8';
        ctx.fillText(tagText, pt.x, pt.y);
      };

      const q = activeFrame?.queues_m || { N: 0, S: 0, E: 0, W: 0 };
      drawArmTag('NORTH det_N', q.N, 300, 300 + 130);
      drawArmTag('SOUTH det_S', q.S, 300, 300 - 130);
      drawArmTag('EAST det_E', q.E, 300 + 130, 300);
      drawArmTag('WEST det_W', q.W, 300 - 130, 300);
    }

    ctx.restore();
  }, [activeFrame, viewMode, showDetectors, showLabels]);

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

        {/* Right: Camera View Controls */}
        <div className="flex items-center gap-2">
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
      <div ref={containerRef} className="relative w-full h-[440px] md:h-[500px] flex-1 overflow-hidden">
        <canvas ref={canvasRef} className="w-full h-full block cursor-grab active:cursor-grabbing" />

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
              <span>Queue Lengths (E2 150m)</span>
            </div>
            <div className="grid grid-cols-2 gap-x-3 gap-y-0.5 text-slate-300">
              <div>N: <span className="text-white font-bold">{Number(activeFrame.queues_m.N || 0).toFixed(1)}m</span></div>
              <div>S: <span className="text-white font-bold">{Number(activeFrame.queues_m.S || 0).toFixed(1)}m</span></div>
              <div>E: <span className="text-white font-bold">{Number(activeFrame.queues_m.E || 0).toFixed(1)}m</span></div>
              <div>W: <span className="text-white font-bold">{Number(activeFrame.queues_m.W || 0).toFixed(1)}m</span></div>
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
