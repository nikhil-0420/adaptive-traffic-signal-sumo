import React, { useRef, useEffect, useState, useCallback, useMemo } from 'react';
import {
  Play,
  Pause,
  RotateCcw,
  FastForward,
  Layers,
  ZoomIn,
  ZoomOut,
  Maximize2,
  Compass,
  ArrowUpRight,
  Eye,
  Sliders,
  ChevronRight,
  Shield,
  Activity,
  LocateFixed,
  X
} from 'lucide-react';
import { api } from '../api/client';
import { useApp } from '../context/AppContext';
import marathahalliGeom from '../data/marathahalli_geometry.json';

// Deterministic vehicle type classification when not explicitly set
const VEHICLE_TYPES = ['car', 'motorcycle', 'auto', 'bus', 'truck'];

function getVehicleType(v) {
  if (v.em || v.is_emergency || v.type === 'emergency' || v.type === 'ambulance') {
    return 'ambulance';
  }
  if (v.type && VEHICLE_TYPES.includes(v.type)) {
    return v.type;
  }
  const hash = (v.id || '').split('').reduce((acc, c) => acc + c.charCodeAt(0), 0);
  const mod = hash % 100;
  if (mod < 55) return 'car';
  if (mod < 75) return 'motorcycle';
  if (mod < 87) return 'auto';
  if (mod < 95) return 'bus';
  return 'truck';
}

const VEHICLE_SPECS = {
  car: { len: 4.8, wid: 1.9, radius: 1.8, name: 'Passenger Car' },
  motorcycle: { len: 2.2, wid: 0.8, radius: 0.6, name: 'Motorcycle' },
  auto: { len: 2.8, wid: 1.4, radius: 1.0, name: 'Auto-Rickshaw' },
  bus: { len: 11.5, wid: 2.6, radius: 2.0, name: 'BMTC Transit Bus' },
  truck: { len: 9.5, wid: 2.5, radius: 1.8, name: 'Commercial Truck' },
  ambulance: { len: 6.5, wid: 2.3, radius: 2.0, name: 'Emergency Ambulance' },
};

// Viewport Zoom Limits (25% to 350%)
const MIN_ZOOM = 0.25;
const MAX_ZOOM = 3.5;

function drawSafeRoundRect(ctx, x, y, width, height, radius) {
  if (width <= 0 || height <= 0) return;
  const r = Math.max(0, Math.min(radius || 0, width / 2, height / 2));
  if (ctx.roundRect) {
    ctx.roundRect(x, y, width, height, r);
  } else {
    ctx.rect(x, y, width, height);
  }
}

export function IsometricIntersection({
  runId = 'marathahalli_imbalanced_orr_hybrid_queue_adaptive_s121',
  network = 'marathahalli',
  liveTelemetry = null,
  isLiveMode = false,
  onRunChange = null,
  availableRuns = [],
  className = '',
  modeLabel = null,
  currentTime = null,
  onSeek = null,
  onFrameUpdate = null,
  height = null,
  isExploded: propIsExploded,
  onExplodeToggle = null,
  soloTier: propSoloTier,
  onSoloTierChange = null,
  initialViewMode = 'isometric',
  showControls = true,
}) {
  const { isDark } = useApp() || {};
  const canvasRef = useRef(null);
  const containerRef = useRef(null);

  // Replay State
  const [replayData, setReplayData] = useState(null);
  const [loadingReplay, setLoadingReplay] = useState(false);
  const [isPlaying, setIsPlaying] = useState(!isLiveMode);
  const [currentFrameIdx, setCurrentFrameIdx] = useState(0);
  const [playbackSpeed, setPlaybackSpeed] = useState(1); // 0.5, 1, 2, 5, 10
  const [viewMode, setViewMode] = useState(initialViewMode); // 'isometric' | 'topdown' | 'approach'
  const [showDetectors, setShowDetectors] = useState(true);
  const [showLabels, setShowLabels] = useState(true);

  // Explode 3-Tier State
  const [internalExploded, setInternalExploded] = useState(false);
  const isExploded = propIsExploded !== undefined ? propIsExploded : internalExploded;
  const [internalSoloTier, setInternalSoloTier] = useState(null);
  const soloTier = propSoloTier !== undefined ? propSoloTier : internalSoloTier;

  // Smooth Explode Progress (0.0 to 1.0)
  const explodeProgressRef = useRef(isExploded ? 1.0 : 0.0);

  // Viewport Zoom & Pan State (Clamped 0.25 to 3.50 max zoom / 350%)
  const [zoom, setZoom] = useState(1.0);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const dragStartRef = useRef({ x: 0, y: 0 });
  const panStartRef = useRef({ x: 0, y: 0 });
  const panVelocityRef = useRef({ x: 0, y: 0 });
  const hasDraggedRef = useRef(false);

  // Synchronized refs for 60fps render loop and event handlers without closure lag
  const zoomRef = useRef(1.0);
  const panRef = useRef({ x: 0, y: 0 });
  const mousePosRef = useRef({ x: 0, y: 0 });
  const hoveredVehicleRef = useRef(null);

  useEffect(() => {
    zoomRef.current = zoom;
  }, [zoom]);

  useEffect(() => {
    panRef.current = pan;
  }, [pan]);

  // Camera Fly-to Animation
  const cameraAnimRef = useRef(null);

  // Selected vehicle for detail card & follow mode
  const [selectedVehicleId, setSelectedVehicleId] = useState(null);
  const [isFollowMode, setIsFollowMode] = useState(false);
  const [hoveredVehicle, setHoveredVehicle] = useState(null);

  // Animation Loop State
  const animFrameRef = useRef(null);
  const lastTickTimeRef = useRef(Date.now());
  const frameAccumulatorRef = useRef(0);
  const isVisibleRef = useRef(true);

  // 1. Replay Data Loading
  useEffect(() => {
    if (isLiveMode || !runId) return;
    let isSubscribed = true;
    setLoadingReplay(true);

    api
      .getReplay(runId)
      .then((data) => {
        if (!isSubscribed) return;
        if (data && data.frames && data.frames.length > 0) {
          setReplayData(data);
          setCurrentFrameIdx(0);
          frameAccumulatorRef.current = 0;
        }
      })
      .catch((err) => {
        console.warn('Replay fetch fallback:', err);
      })
      .finally(() => {
        if (isSubscribed) setLoadingReplay(false);
      });

    return () => {
      isSubscribed = false;
    };
  }, [runId, isLiveMode]);

  // Synchronize seek time
  useEffect(() => {
    if (currentTime !== null && replayData && replayData.frames.length > 0 && !isPlaying) {
      const idx = replayData.frames.findIndex((f) => f.t >= currentTime);
      if (idx !== -1 && idx !== currentFrameIdx) {
        setCurrentFrameIdx(idx);
        frameAccumulatorRef.current = 0;
      }
    }
  }, [currentTime, replayData, isPlaying]);

  // Active Frames for 60fps Interpolation
  const activeFrame = useMemo(() => {
    if (isLiveMode && liveTelemetry) {
      return {
        t: liveTelemetry.sim_time || 0,
        phase: liveTelemetry.current_phase || 'GREEN',
        axis: liveTelemetry.active_axis || 'NS',
        tl_state: liveTelemetry.tl_state || 'GGGgrrrrGGGgrrrr',
        queues_m: {
          N: liveTelemetry.approach_queues?.N?.total_queue_m || 0,
          S: liveTelemetry.approach_queues?.S?.total_queue_m || 0,
          E: liveTelemetry.approach_queues?.E?.total_queue_m || 0,
          W: liveTelemetry.approach_queues?.W?.total_queue_m || 0,
        },
        vehicles: liveTelemetry.vehicles || [],
        emergency_priority: Boolean(liveTelemetry.emergency_priority),
        emergency_approaching: Boolean(liveTelemetry.emergency_approaching),
      };
    }
    if (replayData && replayData.frames.length > 0) {
      return replayData.frames[currentFrameIdx] || replayData.frames[0];
    }
    return null;
  }, [isLiveMode, liveTelemetry, replayData, currentFrameIdx]);

  const nextFrame = useMemo(() => {
    if (isLiveMode || !replayData || !replayData.frames) return null;
    return replayData.frames[currentFrameIdx + 1] || activeFrame;
  }, [isLiveMode, replayData, currentFrameIdx, activeFrame]);

  // Notify parent of active frame
  useEffect(() => {
    if (activeFrame && onFrameUpdate) {
      onFrameUpdate(activeFrame);
    }
  }, [currentFrameIdx, activeFrame]);

  // Playback loop (60 fps decoupling)
  useEffect(() => {
    if (isLiveMode || !isPlaying || !replayData || !replayData.frames.length) return;

    let mounted = true;
    const tick = () => {
      const now = Date.now();
      const dt = (now - lastTickTimeRef.current) / 1000;
      lastTickTimeRef.current = now;

      if (isVisibleRef.current) {
        const frameStep = replayData.step_s || 1.0;
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

  // Pause rendering when tab is hidden or offscreen
  useEffect(() => {
    const handleVisibility = () => {
      isVisibleRef.current = !document.hidden;
    };
    document.addEventListener('visibilitychange', handleVisibility);

    const el = containerRef.current;
    if (!el) return;
    const observer = new IntersectionObserver(([entry]) => {
      isVisibleRef.current = entry.isIntersecting;
    });
    observer.observe(el);

    return () => {
      document.removeEventListener('visibilitychange', handleVisibility);
      observer.disconnect();
    };
  }, []);

  // Zoom & Pan Actions (Clamped to 350% maximum)
  const handleZoomIn = useCallback(() => {
    const curZoom = zoomRef.current;
    const curPan = panRef.current;
    const nextZoom = Math.min(MAX_ZOOM, Number((curZoom * 1.25).toFixed(2)));
    if (nextZoom === curZoom) return;
    const ratio = nextZoom / curZoom;
    const nextPan = {
      x: Math.round(curPan.x * ratio),
      y: Math.round(curPan.y * ratio),
    };
    zoomRef.current = nextZoom;
    panRef.current = nextPan;
    setZoom(nextZoom);
    setPan(nextPan);
  }, []);

  const handleZoomOut = useCallback(() => {
    const curZoom = zoomRef.current;
    const curPan = panRef.current;
    const nextZoom = Math.max(MIN_ZOOM, Number((curZoom / 1.25).toFixed(2)));
    if (nextZoom === curZoom) return;
    const ratio = nextZoom / curZoom;
    const nextPan = {
      x: Math.round(curPan.x * ratio),
      y: Math.round(curPan.y * ratio),
    };
    zoomRef.current = nextZoom;
    panRef.current = nextPan;
    setZoom(nextZoom);
    setPan(nextPan);
  }, []);

  const handleResetView = useCallback(() => {
    zoomRef.current = 1.0;
    panRef.current = { x: 0, y: 0 };
    setZoom(1.0);
    setPan({ x: 0, y: 0 });
    setSelectedVehicleId(null);
    setIsFollowMode(false);
  }, []);

  // Fly to approach animation (600ms)
  const flyToApproach = useCallback((approach) => {
    const targetPans = {
      N: { x: 0, y: 140, zoom: 2.2 },
      S: { x: 0, y: -140, zoom: 2.2 },
      W: { x: 140, y: 0, zoom: 2.2 },
      E: { x: -140, y: 0, zoom: 2.2 },
      C: { x: 0, y: 0, zoom: 1.0 },
    };
    const target = targetPans[approach] || targetPans.C;
    const startPan = { ...panRef.current };
    const startZoom = zoomRef.current;
    const startTime = performance.now();
    const duration = 600;

    if (cameraAnimRef.current) cancelAnimationFrame(cameraAnimRef.current);

    const animateCamera = (now) => {
      const elapsed = now - startTime;
      const progress = Math.min(1.0, elapsed / duration);
      // Ease out cubic
      const eased = 1 - Math.pow(1 - progress, 3);

      const curP = {
        x: Math.round(startPan.x + (target.x - startPan.x) * eased),
        y: Math.round(startPan.y + (target.y - startPan.y) * eased),
      };
      const curZ = Math.min(MAX_ZOOM, Number((startZoom + (target.zoom - startZoom) * eased).toFixed(2)));

      panRef.current = curP;
      zoomRef.current = curZ;
      setPan(curP);
      setZoom(curZ);

      if (progress < 1.0) {
        cameraAnimRef.current = requestAnimationFrame(animateCamera);
      }
    };
    cameraAnimRef.current = requestAnimationFrame(animateCamera);
  }, []);

  // Pointer wheel zoom toward pointer (Accurate viewport-relative transform)
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const handleWheelNative = (e) => {
      e.preventDefault();
      const rect = canvas.getBoundingClientRect();
      const w = rect.width;
      const h = rect.height;
      if (w <= 0 || h <= 0) return;

      const mouseX = e.clientX - rect.left;
      const mouseY = e.clientY - rect.top;

      const factor = e.deltaY < 0 ? 1.15 : 0.87;
      const curZoom = zoomRef.current;
      const curPan = panRef.current;
      const nextZoom = Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, Number((curZoom * factor).toFixed(2))));
      if (nextZoom === curZoom) return;

      const ratio = nextZoom / curZoom;
      const cx = w / 2;
      const cy = h / 2;
      const nextPan = {
        x: Math.round(mouseX - cx - (mouseX - cx - curPan.x) * ratio),
        y: Math.round(mouseY - cy - (mouseY - cy - curPan.y) * ratio),
      };

      zoomRef.current = nextZoom;
      panRef.current = nextPan;
      setZoom(nextZoom);
      setPan(nextPan);
    };

    canvas.addEventListener('wheel', handleWheelNative, { passive: false });
    return () => canvas.removeEventListener('wheel', handleWheelNative);
  }, []);

  // Keyboard navigation (+, -, 0, Arrow Keys)
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (document.activeElement?.tagName === 'INPUT') return;
      if (e.key === '+' || e.key === '=') {
        handleZoomIn();
      } else if (e.key === '-' || e.key === '_') {
        handleZoomOut();
      } else if (e.key === '0' || e.key.toLowerCase() === 'f') {
        handleResetView();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleZoomIn, handleZoomOut, handleResetView]);

  // Double-click zoom in toward mouse pointer
  const handleDoubleClick = (e) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const w = rect.width;
    const h = rect.height;
    if (w <= 0 || h <= 0) return;

    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;
    const curZoom = zoomRef.current;
    const curPan = panRef.current;
    const nextZoom = Math.min(MAX_ZOOM, Number((curZoom * 1.5).toFixed(2)));
    if (nextZoom === curZoom) return;

    const ratio = nextZoom / curZoom;
    const cx = w / 2;
    const cy = h / 2;
    const nextPan = {
      x: Math.round(mouseX - cx - (mouseX - cx - curPan.x) * ratio),
      y: Math.round(mouseY - cy - (mouseY - cy - curPan.y) * ratio),
    };

    zoomRef.current = nextZoom;
    panRef.current = nextPan;
    setZoom(nextZoom);
    setPan(nextPan);
  };

  // Drag and Pan
  const handleMouseDown = (e) => {
    if (e.button !== 0) return;
    setIsDragging(true);
    hasDraggedRef.current = false;
    dragStartRef.current = { x: e.clientX, y: e.clientY };
    panStartRef.current = { ...panRef.current };
    panVelocityRef.current = { x: 0, y: 0 };
  };

  const handleMouseMove = (e) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const newMouseX = e.clientX - rect.left;
    const newMouseY = e.clientY - rect.top;
    mousePosRef.current = { x: newMouseX, y: newMouseY };

    if (!isDragging) return;
    const dx = e.clientX - dragStartRef.current.x;
    const dy = e.clientY - dragStartRef.current.y;
    if (Math.hypot(dx, dy) > 4) {
      hasDraggedRef.current = true;
    }
    panVelocityRef.current = { x: dx, y: dy };
    const newPan = {
      x: panStartRef.current.x + dx,
      y: panStartRef.current.y + dy,
    };
    panRef.current = newPan;
    setPan(newPan);
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const handleCanvasClick = () => {
    if (hasDraggedRef.current) return;
    const hovered = hoveredVehicleRef.current;
    if (hovered) {
      setSelectedVehicleId(hovered.id);
    } else {
      setSelectedVehicleId(null);
      setIsFollowMode(false);
    }
  };

  // Explode Toggle Handler
  const toggleExplode = useCallback(() => {
    if (onExplodeToggle) {
      onExplodeToggle();
    } else {
      setInternalExploded((prev) => !prev);
    }
  }, [onExplodeToggle]);

  const selectSoloTier = useCallback((tier) => {
    const newTier = soloTier === tier ? null : tier;
    if (onSoloTierChange) {
      onSoloTierChange(newTier);
    } else {
      setInternalSoloTier(newTier);
    }
  }, [soloTier, onSoloTierChange]);

  // MAIN CANVAS RENDER LOOP (60 FPS)
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId;

    const render = () => {
      // 1. Container Size and Device Pixel Ratio
      const rect = canvas.getBoundingClientRect();
      const w = rect.width;
      const h = rect.height;
      if (w <= 0 || h <= 0) {
        animationFrameId = requestAnimationFrame(render);
        return;
      }

      const dpr = Math.min(2, window.devicePixelRatio || 1);
      const targetW = Math.floor(w * dpr);
      const targetH = Math.floor(h * dpr);
      if (canvas.width !== targetW || canvas.height !== targetH) {
        canvas.width = targetW;
        canvas.height = targetH;
      }

      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

      // 2. Animate Explode Progress with Spring Physics (~700ms)
      const targetExplode = isExploded ? 1.0 : 0.0;
      const diff = targetExplode - explodeProgressRef.current;
      if (Math.abs(diff) > 0.002) {
        explodeProgressRef.current += diff * 0.12;
      } else {
        explodeProgressRef.current = targetExplode;
      }
      const ep = explodeProgressRef.current;

      // 3. Scene Palette: Control-Room Screen in BOTH themes (#0D1417 ground, #29343A asphalt)
      const groundColor = '#0D1417';
      const asphaltColor = '#29343A';
      const markingWhite = 'rgba(243, 237, 224, 0.75)';
      const medianYellow = '#FFB020';
      const stopLineColor = '#FFFFFF';
      const signalGreen = '#2FA866';
      const signalYellow = '#F2C230';
      const signalRed = '#D6453D';

      // Clear Canvas to Control-Room Screen Ground
      ctx.fillStyle = groundColor;
      ctx.fillRect(0, 0, w, h);

      // Subtle engineering coordinate grid
      const currentZoom = zoomRef.current;
      const currentPan = panRef.current;

      ctx.strokeStyle = 'rgba(255, 255, 255, 0.03)';
      ctx.lineWidth = 1;
      const gridStep = 40 * currentZoom;
      if (gridStep > 15) {
        const startX = (w / 2 + currentPan.x) % gridStep;
        const startY = (h / 2 + currentPan.y) % gridStep;
        ctx.beginPath();
        for (let x = startX; x < w; x += gridStep) {
          ctx.moveTo(x, 0);
          ctx.lineTo(x, h);
        }
        for (let y = startY; y < h; y += gridStep) {
          ctx.moveTo(0, y);
          ctx.lineTo(w, y);
        }
        ctx.stroke();
      }

      // Center Origin
      let cx = w / 2 + currentPan.x;
      let cy = h / 2 + currentPan.y;

      const isIso = viewMode === 'isometric';
      const origX = 350.0;
      const origY = 350.0;
      const viewSpanM = 480;
      const baseScale = (Math.min(w, h) / (viewSpanM * (isIso ? 1.45 : 1.6))) * currentZoom;

      // Coordinate Projection Functions
      const worldToScreen = (wx, wy, z = 0, tier = 'surface') => {
        const u = wx - origX;
        const v = wy - origY;

        // Tier Explode Vertical Offsets
        let tierOffsetY = 0;
        if (tier === 'flyover') {
          tierOffsetY = -72 * ep;
        } else if (tier === 'underpass') {
          tierOffsetY = 65 * ep;
        }

        if (!isIso) {
          // Top-down Orthographic
          return {
            x: cx + u * baseScale,
            y: cy - v * baseScale - z * baseScale * 0.35 + tierOffsetY,
          };
        }

        // 2.5D Isometric (30 deg tilt)
        const cos30 = Math.cos(Math.PI / 6);
        const sin30 = Math.sin(Math.PI / 6);
        const isoX = (u - v) * cos30;
        const isoY = (u + v) * sin30;
        return {
          x: cx + isoX * baseScale,
          y: cy - isoY * baseScale * 0.72 - z * baseScale * 1.85 + tierOffsetY,
        };
      };

      const sumoAngleToScreen = (deg) => {
        const rad = (deg * Math.PI) / 180;
        const vx = Math.sin(rad);
        const vy = Math.cos(rad);
        const p1 = worldToScreen(origX, origY, 0);
        const p2 = worldToScreen(origX + vx * 10, origY + vy * 10, 0);
        return Math.atan2(p2.y - p1.y, p2.x - p1.x);
      };

      // Tier Opacity Helper (for Solo Tier mode)
      const getTierOpacity = (tier) => {
        if (!soloTier) return 1.0;
        return soloTier === tier ? 1.0 : 0.15;
      };

      // 4. DRAW CONNECTING EXPLODED VERTICAL GUIDES
      if (ep > 0.05 && isIso) {
        ctx.save();
        ctx.setLineDash([4, 4]);
        ctx.lineWidth = 1.5;
        const guideNodes = [
          { x: 170, y: 350 }, // HAL split
          { x: 530, y: 350 }, // Whitefield split
          { x: 350, y: 170 }, // ORR South split
          { x: 350, y: 530 }, // ORR North split
          { x: 350, y: 350 }, // Junction center
        ];
        guideNodes.forEach((node) => {
          const pUnder = worldToScreen(node.x, node.y, -4.0, 'underpass');
          const pSurf = worldToScreen(node.x, node.y, 0.0, 'surface');
          const pFly = worldToScreen(node.x, node.y, 7.0, 'flyover');

          ctx.strokeStyle = 'rgba(255, 176, 32, 0.35)';
          ctx.beginPath();
          ctx.moveTo(pUnder.x, pUnder.y);
          ctx.lineTo(pSurf.x, pSurf.y);
          ctx.lineTo(pFly.x, pFly.y);
          ctx.stroke();

          // Small anchor rings
          ctx.fillStyle = '#FFB020';
          ctx.beginPath();
          ctx.arc(pFly.x, pFly.y, 2.5, 0, Math.PI * 2);
          ctx.arc(pSurf.x, pSurf.y, 2, 0, Math.PI * 2);
          ctx.arc(pUnder.x, pUnder.y, 2, 0, Math.PI * 2);
          ctx.fill();
        });
        ctx.restore();
      }

      // 5. DRAW ROADWAYS BY TIER (Underpass -> Surface -> Flyover)
      const drawRoadRibbon = (shape, widthM, tier, zVal, isMedian = false) => {
        if (!shape || shape.length < 2) return;
        const opacity = getTierOpacity(tier);
        if (opacity <= 0.01) return;

        ctx.save();
        ctx.globalAlpha = opacity;

        const pts = shape.map((p) => worldToScreen(p[0], p[1], zVal, tier));
        const halfW = (widthM / 2.0) * baseScale;

        // Asphalt Ribbon
        ctx.strokeStyle = asphaltColor;
        ctx.lineWidth = widthM * baseScale;
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
        ctx.beginPath();
        pts.forEach((pt, i) => {
          if (i === 0) ctx.moveTo(pt.x, pt.y);
          else ctx.lineTo(pt.x, pt.y);
        });
        ctx.stroke();

        // Edge kerb lines
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
        ctx.lineWidth = 1;
        ctx.stroke();

        ctx.restore();
      };

      // 5.1 TIER 3: UNDERPASS TRENCH (ORR Mainline)
      if (getTierOpacity('underpass') > 0.01) {
        ctx.save();
        ctx.globalAlpha = getTierOpacity('underpass');

        // Underpass trench walls
        const underLanes = marathahalliGeom.lanes.filter((l) => l.tier === 'underpass');
        underLanes.forEach((l) => {
          drawRoadRibbon(l.shape, l.width, 'underpass', -4.0);
        });

        // Underpass center dashed divider
        underLanes.forEach((l) => {
          if (l.shape && l.shape.length >= 2) {
            const pts = l.shape.map((p) => worldToScreen(p[0], p[1], -4.0, 'underpass'));
            ctx.save();
            ctx.strokeStyle = markingWhite;
            ctx.setLineDash([4 * zoom, 4 * zoom]);
            ctx.lineWidth = 1.2;
            ctx.beginPath();
            pts.forEach((pt, i) => {
              if (i === 0) ctx.moveTo(pt.x, pt.y);
              else ctx.lineTo(pt.x, pt.y);
            });
            ctx.stroke();
            ctx.restore();
          }
        });
        ctx.restore();
      }

      // 5.2 TIER 2: SURFACE ROADWAYS & CONFLICT AREA
      if (getTierOpacity('surface') > 0.01) {
        ctx.save();
        ctx.globalAlpha = getTierOpacity('surface');

        // Draw surface junctions
        marathahalliGeom.junctions.forEach((junc) => {
          if (junc.tier === 'surface' && junc.shape && junc.shape.length >= 3) {
            const pts = junc.shape.map((p) => worldToScreen(p[0], p[1], 0.0, 'surface'));
            ctx.fillStyle = asphaltColor;
            ctx.beginPath();
            pts.forEach((pt, i) => {
              if (i === 0) ctx.moveTo(pt.x, pt.y);
              else ctx.lineTo(pt.x, pt.y);
            });
            ctx.closePath();
            ctx.fill();

            // Conflict box hatched marking at marathahalli_tls
            if (junc.id === 'marathahalli_tls') {
              ctx.strokeStyle = 'rgba(255, 176, 32, 0.4)';
              ctx.lineWidth = 1.5;
              ctx.stroke();
            }
          }
        });

        // Draw all surface lanes
        const surfaceLanes = marathahalliGeom.lanes.filter((l) => l.tier === 'surface');
        surfaceLanes.forEach((l) => {
          drawRoadRibbon(l.shape, l.width, 'surface', 0.0);
        });

        // Lane markings (solid yellow medians and dashed dividers)
        surfaceLanes.forEach((l) => {
          if (l.shape && l.shape.length >= 2) {
            const pts = l.shape.map((p) => worldToScreen(p[0], p[1], 0.0, 'surface'));
            ctx.save();
            if (l.index === 0 && !l.is_internal) {
              // Outer median line
              ctx.strokeStyle = medianYellow;
              ctx.lineWidth = 1.5;
              ctx.beginPath();
              pts.forEach((pt, i) => {
                if (i === 0) ctx.moveTo(pt.x, pt.y);
                else ctx.lineTo(pt.x, pt.y);
              });
              ctx.stroke();
            } else if (!l.is_internal) {
              // Dashed lane divider
              ctx.strokeStyle = markingWhite;
              ctx.setLineDash([4 * zoom, 4 * zoom]);
              ctx.lineWidth = 1.0;
              ctx.beginPath();
              pts.forEach((pt, i) => {
                if (i === 0) ctx.moveTo(pt.x, pt.y);
                else ctx.lineTo(pt.x, pt.y);
              });
              ctx.stroke();
            }
            ctx.restore();
          }
        });

        // E2 Detectors Translucent Zones & Stopped Vehicle Stack Agreement
        if (showDetectors) {
          const queues = activeFrame?.queues_m || { N: 0, S: 0, E: 0, W: 0 };
          marathahalliGeom.detectors.forEach((det) => {
            if (det.shape && det.shape.length >= 2) {
              const qVal = queues[det.approach] || 0;
              const fillRatio = Math.min(1.0, Math.max(0.05, qVal / 25.0));
              const p1 = worldToScreen(det.shape[0][0], det.shape[0][1], 0.0, 'surface');
              const p2 = worldToScreen(det.shape[1][0], det.shape[1][1], 0.0, 'surface');

              ctx.save();
              // Translucent strip
              ctx.strokeStyle = qVal > 5 ? 'rgba(239, 68, 68, 0.55)' : 'rgba(255, 176, 32, 0.35)';
              ctx.lineWidth = 3.2 * baseScale;
              ctx.lineCap = 'butt';
              ctx.beginPath();
              ctx.moveTo(p1.x, p1.y);
              ctx.lineTo(p2.x, p2.y);
              ctx.stroke();

              // Active Queue Fill
              const qFillX = p1.x + (p2.x - p1.x) * fillRatio;
              const qFillY = p1.y + (p2.y - p1.y) * fillRatio;
              ctx.strokeStyle = qVal > 15 ? signalRed : '#FFB020';
              ctx.lineWidth = 3.0 * baseScale;
              ctx.beginPath();
              ctx.moveTo(p1.x, p1.y);
              ctx.lineTo(qFillX, qFillY);
              ctx.stroke();

              ctx.restore();
            }
          });
        }

        // Real TLS Stop Lines & Signal Heads
        const tlState = activeFrame?.tl_state || 'GGGgrrrrGGGgrrrr';
        marathahalliGeom.stop_lines.forEach((sl) => {
          const linkChar = tlState[sl.link_index] || 'r';
          let stopColor = signalRed;
          if (linkChar === 'G' || linkChar === 'g') stopColor = signalGreen;
          else if (linkChar === 'y' || linkChar === 'Y') stopColor = signalYellow;

          const p1 = worldToScreen(sl.p1[0], sl.p1[1], 0.0, 'surface');
          const p2 = worldToScreen(sl.p2[0], sl.p2[1], 0.0, 'surface');

          // Colored stop-line stripe on road
          ctx.save();
          ctx.strokeStyle = stopColor;
          ctx.lineWidth = Math.max(2.5, 1.8 * zoom);
          ctx.beginPath();
          ctx.moveTo(p1.x, p1.y);
          ctx.lineTo(p2.x, p2.y);
          ctx.stroke();

          // Physical 3D Signal Head on Curb
          const headPt = worldToScreen(sl.center[0], sl.center[1], 3.2, 'surface');
          ctx.fillStyle = '#0C1316';
          ctx.strokeStyle = '#2B373C';
          ctx.lineWidth = 1;
          ctx.beginPath();
          drawSafeRoundRect(ctx, headPt.x - 4, headPt.y - 12, 8, 22, 3);
          ctx.fill();
          ctx.stroke();

          // Three signal lamps (Red, Yellow, Green)
          // Red
          ctx.fillStyle = stopColor === signalRed ? signalRed : 'rgba(214, 69, 61, 0.25)';
          ctx.beginPath();
          ctx.arc(headPt.x, headPt.y - 7, 2, 0, Math.PI * 2);
          ctx.fill();
          // Yellow
          ctx.fillStyle = stopColor === signalYellow ? signalYellow : 'rgba(242, 194, 48, 0.25)';
          ctx.beginPath();
          ctx.arc(headPt.x, headPt.y - 1, 2, 0, Math.PI * 2);
          ctx.fill();
          // Green
          ctx.fillStyle = stopColor === signalGreen ? signalGreen : 'rgba(47, 168, 102, 0.25)';
          ctx.beginPath();
          ctx.arc(headPt.x, headPt.y + 5, 2, 0, Math.PI * 2);
          ctx.fill();

          ctx.restore();
        });

        ctx.restore();
      }

      // 5.3 TIER 1: ELEVATED FLYOVER OVERPASS
      if (getTierOpacity('flyover') > 0.01) {
        ctx.save();
        ctx.globalAlpha = getTierOpacity('flyover');

        const flyoverLanes = marathahalliGeom.lanes.filter((l) => l.tier === 'flyover');

        // Flyover ground shadow
        flyoverLanes.forEach((l) => {
          if (l.shape && l.shape.length >= 2) {
            const shadowPts = l.shape.map((p) => worldToScreen(p[0], p[1], 0.0, 'surface'));
            ctx.save();
            ctx.strokeStyle = 'rgba(0, 0, 0, 0.45)';
            ctx.lineWidth = (l.width + 1.5) * baseScale;
            ctx.lineCap = 'round';
            ctx.beginPath();
            shadowPts.forEach((pt, i) => {
              if (i === 0) ctx.moveTo(pt.x, pt.y);
              else ctx.lineTo(pt.x, pt.y);
            });
            ctx.stroke();
            ctx.restore();
          }
        });

        // Concrete support piers
        const pierLocations = [
          [220, 350],
          [285, 350],
          [415, 350],
          [480, 350],
        ];
        pierLocations.forEach(([px, py]) => {
          const pBase = worldToScreen(px, py, 0.0, 'surface');
          const pTop = worldToScreen(px, py, 6.5, 'flyover');
          ctx.save();
          ctx.strokeStyle = '#3C454B';
          ctx.lineWidth = 4 * baseScale;
          ctx.beginPath();
          ctx.moveTo(pBase.x, pBase.y);
          ctx.lineTo(pTop.x, pTop.y);
          ctx.stroke();
          ctx.restore();
        });

        // Elevated deck ribbons
        flyoverLanes.forEach((l) => {
          drawRoadRibbon(l.shape, l.width, 'flyover', 7.0);
        });

        // Flyover concrete parapets & center divider
        flyoverLanes.forEach((l) => {
          if (l.shape && l.shape.length >= 2) {
            const pts = l.shape.map((p) => worldToScreen(p[0], p[1], 7.0, 'flyover'));
            ctx.save();
            if (l.index === 0) {
              ctx.strokeStyle = medianYellow;
              ctx.lineWidth = 1.5;
            } else {
              ctx.strokeStyle = markingWhite;
              ctx.setLineDash([4 * zoom, 4 * zoom]);
              ctx.lineWidth = 1.0;
            }
            ctx.beginPath();
            pts.forEach((pt, i) => {
              if (i === 0) ctx.moveTo(pt.x, pt.y);
              else ctx.lineTo(pt.x, pt.y);
            });
            ctx.stroke();
            ctx.restore();
          }
        });

        ctx.restore();
      }

      // 6. RENDER VEHICLES WITH REAL SUMO VTYPES & VISIBILITY SCALING
      const currentVehicles = activeFrame?.vehicles || [];
      const nextVehiclesMap = new Map();
      if (nextFrame && nextFrame.vehicles) {
        nextFrame.vehicles.forEach((v) => nextVehiclesMap.set(v.id, v));
      }

      // Interpolation progress between frame t and t+1
      const subFrameProgress = Math.min(1.0, Math.max(0.0, frameAccumulatorRef.current));

      // Compute camera tracking if Follow Mode is on (smooth panRef update without re-render thrashing)
      if (isFollowMode && selectedVehicleId) {
        const followed = currentVehicles.find((v) => v.id === selectedVehicleId);
        if (followed) {
          const pt = worldToScreen(followed.x, followed.y, 0, 'surface');
          const targetPanX = panRef.current.x + (w / 2 - pt.x) * 0.1;
          const targetPanY = panRef.current.y + (h / 2 - pt.y) * 0.1;
          panRef.current = { x: targetPanX, y: targetPanY };
        }
      }

      // Visibility factor: car length >= 12.5px at 100% zoom, easing to 1.0x at 350%
      const minLengthPxAt100 = 13.0;
      const nominalCarPx = 4.8 * baseScale * Math.min(currentZoom, 1.0);
      const rawVisFactor = Math.max(1.0, minLengthPxAt100 / nominalCarPx);
      const easeT = Math.min(1.0, Math.max(0.0, (currentZoom - 1.0) / 2.5));
      const visFactor = rawVisFactor * (1.0 - easeT) + 1.0 * easeT;

      let closestHovered = null;
      let minHoverDist = 18;

      currentVehicles.forEach((v1) => {
        const v2 = nextVehiclesMap.get(v1.id) || v1;

        // Smooth position and shortest-angle heading interpolation
        const interpX = v1.x + (v2.x - v1.x) * subFrameProgress;
        const interpY = v1.y + (v2.y - v1.y) * subFrameProgress;
        let da = ((v2.a - v1.a + 540) % 360) - 180;
        const interpA = (v1.a + da * subFrameProgress + 360) % 360;
        const interpS = v1.s + (v2.s - v1.s) * subFrameProgress;

        // Determine vehicle tier & altitude
        let vehTier = 'surface';
        let vehZ = 0.0;
        const isEastWest = Math.abs(interpA - 90) < 35 || Math.abs(interpA - 270) < 35;
        const isNorthSouth = Math.abs(interpA - 0) < 35 || Math.abs(interpA - 180) < 35;

        if (Math.abs(interpY - 350) <= 7.5 && isEastWest && interpX >= 170 && interpX <= 530) {
          vehTier = 'flyover';
          vehZ = 7.0;
        } else if (Math.abs(interpX - 350) <= 7.5 && isNorthSouth && interpY >= 170 && interpY <= 530 && interpS > 8.0) {
          vehTier = 'underpass';
          vehZ = -4.0;
        }

        const opacity = getTierOpacity(vehTier);
        if (opacity <= 0.01) return;

        const screenPt = worldToScreen(interpX, interpY, vehZ, vehTier);
        const headingAngle = sumoAngleToScreen(interpA);
        const vType = getVehicleType(v1);
        const spec = VEHICLE_SPECS[vType] || VEHICLE_SPECS.car;

        const vehLen = spec.len * baseScale * visFactor;
        const vehWid = spec.wid * baseScale * visFactor;

        // Check hover detection using mousePosRef
        const mPos = mousePosRef.current;
        const mouseDist = Math.hypot(mPos.x - screenPt.x, mPos.y - screenPt.y);
        if (mouseDist < minHoverDist) {
          minHoverDist = mouseDist;
          closestHovered = {
            id: v1.id,
            type: vType,
            typeName: spec.name,
            speed_mps: interpS,
            speed_kmh: interpS * 3.6,
            wait_s: v1.w || 0,
            screenX: screenPt.x,
            screenY: screenPt.y,
            tier: vehTier,
          };
        }

        ctx.save();
        ctx.globalAlpha = opacity;
        ctx.translate(screenPt.x, screenPt.y);
        ctx.rotate(headingAngle);

        // Ground shadow
        ctx.fillStyle = 'rgba(0, 0, 0, 0.45)';
        ctx.beginPath();
        drawSafeRoundRect(ctx, -vehLen / 2 + 1, -vehWid / 2 + 1, vehLen, vehWid, spec.radius);
        ctx.fill();

        // Distinct saturated palette based on vehicle type
        let bodyColor = '#FFB020'; // Phasora amber default
        if (vType === 'ambulance') {
          bodyColor = '#FFFFFF';
        } else if (vType === 'bus') {
          bodyColor = '#0F6B7A'; // Petrol BMTC
        } else if (vType === 'truck') {
          bodyColor = '#E06A3B'; // Terracotta
        } else if (vType === 'auto') {
          bodyColor = '#2FA866'; // Green auto body
        } else if (vType === 'motorcycle') {
          bodyColor = '#4FB3C2'; // Bright teal
        } else {
          // Passenger cars deterministic variety
          const hash = (v1.id || '').split('').reduce((acc, c) => acc + c.charCodeAt(0), 0);
          const carPaints = ['#FFB020', '#4FB3C2', '#E2E8F0', '#3B82F6', '#D97706', '#94A3B8'];
          bodyColor = carPaints[hash % carPaints.length];
        }

        // Vehicle Body
        ctx.fillStyle = bodyColor;
        ctx.strokeStyle = '#0C1316';
        ctx.lineWidth = 1;
        ctx.beginPath();
        drawSafeRoundRect(ctx, -vehLen / 2, -vehWid / 2, vehLen, vehWid, spec.radius);
        ctx.fill();
        ctx.stroke();

        // Windscreen & Roof Detail
        if (vType === 'ambulance') {
          // Red cross livery
          ctx.fillStyle = '#D6453D';
          ctx.fillRect(-vehLen * 0.25, -vehWid / 2, vehLen * 0.5, vehWid);
          // Alternating Red/Blue Strobe Siren
          const strobe = Math.floor(Date.now() / 120) % 2 === 0;
          ctx.fillStyle = strobe ? '#D6453D' : '#00D2FF';
          ctx.shadowColor = strobe ? '#D6453D' : '#00D2FF';
          ctx.shadowBlur = 12;
          ctx.beginPath();
          ctx.arc(0, 0, 2.5 * visFactor, 0, Math.PI * 2);
          ctx.fill();
          ctx.shadowBlur = 0;
        } else if (vType === 'bus') {
          // Front and rear panoramic glass
          ctx.fillStyle = '#0C1316';
          ctx.fillRect(vehLen * 0.25, -vehWid * 0.35, vehLen * 0.15, vehWid * 0.7);
          ctx.fillRect(-vehLen * 0.38, -vehWid * 0.35, vehLen * 0.1, vehWid * 0.7);
        } else if (vType === 'auto') {
          // Yellow front roof canopy
          ctx.fillStyle = '#FFB020';
          ctx.fillRect(-vehLen * 0.3, -vehWid * 0.4, vehLen * 0.6, vehWid * 0.8);
        } else {
          // Car windscreen and rear glass
          ctx.fillStyle = '#0C1316';
          ctx.fillRect(vehLen * 0.08, -vehWid * 0.35, vehLen * 0.18, vehWid * 0.7);
          ctx.fillRect(-vehLen * 0.28, -vehWid * 0.35, vehLen * 0.12, vehWid * 0.7);
        }

        // Brake Lights (Illuminated when stopped or decelerating)
        const isBraking = interpS < 0.8 || (v2.s < v1.s - 0.2);
        ctx.fillStyle = isBraking ? '#FF2E2E' : 'rgba(214, 69, 61, 0.4)';
        if (isBraking) {
          ctx.shadowColor = '#FF2E2E';
          ctx.shadowBlur = 6;
        }
        ctx.beginPath();
        ctx.arc(-vehLen / 2 + 0.5, -vehWid * 0.35, 1.2, 0, Math.PI * 2);
        ctx.arc(-vehLen / 2 + 0.5, vehWid * 0.35, 1.2, 0, Math.PI * 2);
        ctx.fill();
        ctx.shadowBlur = 0;

        // Headlights (Lit in dark theme)
        if (isDark) {
          ctx.fillStyle = '#FFF8E7';
          ctx.beginPath();
          ctx.arc(vehLen / 2 - 0.5, -vehWid * 0.35, 1.2, 0, Math.PI * 2);
          ctx.arc(vehLen / 2 - 0.5, vehWid * 0.35, 1.2, 0, Math.PI * 2);
          ctx.fill();

          // Forward light cones
          ctx.fillStyle = 'rgba(255, 248, 231, 0.06)';
          ctx.beginPath();
          ctx.moveTo(vehLen / 2, -vehWid * 0.35);
          ctx.lineTo(vehLen / 2 + 14 * visFactor, -vehWid * 0.9);
          ctx.lineTo(vehLen / 2 + 14 * visFactor, vehWid * 0.9);
          ctx.lineTo(vehLen / 2, vehWid * 0.35);
          ctx.closePath();
          ctx.fill();
        }

        // Selection ring
        if (selectedVehicleId === v1.id) {
          ctx.strokeStyle = '#FFB020';
          ctx.lineWidth = 1.5;
          ctx.beginPath();
          ctx.arc(0, 0, vehLen * 0.7, 0, Math.PI * 2);
          ctx.stroke();
        }

        ctx.restore();
      });

      hoveredVehicleRef.current = closestHovered;
      // Only trigger React state update if hover target changed (prevents 60fps re-render loop)
      setHoveredVehicle((prev) => {
        if (!prev && !closestHovered) return null;
        if (prev && closestHovered && prev.id === closestHovered.id) {
          if (
            Math.abs(prev.screenX - closestHovered.screenX) < 1 &&
            Math.abs(prev.screenY - closestHovered.screenY) < 1 &&
            prev.speed_kmh === closestHovered.speed_kmh
          ) {
            return prev;
          }
        }
        return closestHovered;
      });

      // 7. TIER 3D FLOATING LABELS (When Exploded)
      if (ep > 0.4 && isIso) {
        ctx.save();
        const tierBadges = [
          { text: 'TIER 1 · FLYOVER (+7.0 m)', pos: [190, 370, 7.0], tier: 'flyover', color: '#FFB020' },
          { text: 'TIER 2 · SURFACE AT-GRADE (0.0 m)', pos: [190, 310, 0.0], tier: 'surface', color: '#2FA866' },
          { text: 'TIER 3 · UNDERPASS TRENCH (-4.0 m)', pos: [330, 190, -4.0], tier: 'underpass', color: '#4FB3C2' },
        ];
        tierBadges.forEach((b) => {
          const pt = worldToScreen(b.pos[0], b.pos[1], b.pos[2], b.tier);
          const isSolo = soloTier === b.tier;

          ctx.fillStyle = 'rgba(12, 19, 22, 0.9)';
          ctx.strokeStyle = isSolo ? b.color : 'rgba(255, 255, 255, 0.15)';
          ctx.lineWidth = isSolo ? 2 : 1;
          ctx.beginPath();
          drawSafeRoundRect(ctx, pt.x - 70, pt.y - 12, 140, 24, 6);
          ctx.fill();
          ctx.stroke();

          ctx.fillStyle = isSolo ? b.color : '#F3EDE0';
          ctx.font = 'bold 9px JetBrains Mono, monospace';
          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';
          ctx.fillText(b.text, pt.x, pt.y);
        });
        ctx.restore();
      }

      // 8. COLLISION-AWARE VIEWPORT LABELS (Never cut off at canvas margins)
      if (showLabels) {
        ctx.save();
        const approachLabels = [
          { label: 'ORR NORTH · KR Puram', world: [350, 680], code: 'N' },
          { label: 'ORR SOUTH · Kadubeesanahalli', world: [350, 20], code: 'S' },
          { label: 'VARTHUR ROAD · Whitefield East', world: [680, 350], code: 'E' },
          { label: 'HAL AIRPORT ROAD · West', world: [20, 350], code: 'W' },
        ];

        ctx.font = '600 10px Plus Jakarta Sans, -apple-system, BlinkMacSystemFont, sans-serif';
        approachLabels.forEach((item) => {
          const pt = worldToScreen(item.world[0], item.world[1], 0, 'surface');
          const textMetrics = ctx.measureText(item.label);
          const textW = Math.ceil(textMetrics.width) + 18;
          const halfW = textW / 2;
          const halfH = 10;
          const margin = 12;

          // Clamp inside viewport so label badge never exceeds canvas bounds
          const clampedX = Math.max(margin + halfW, Math.min(w - margin - halfW, pt.x));
          const clampedY = Math.max(margin + halfH, Math.min(h - margin - halfH, pt.y));

          ctx.fillStyle = 'rgba(12, 19, 22, 0.88)';
          ctx.strokeStyle = 'rgba(255, 255, 255, 0.12)';
          ctx.lineWidth = 1;
          ctx.beginPath();
          drawSafeRoundRect(ctx, clampedX - halfW, clampedY - halfH, textW, 20, 4);
          ctx.fill();
          ctx.stroke();

          ctx.fillStyle = '#F3EDE0';
          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';
          ctx.fillText(item.label, clampedX, clampedY);
        });

        ctx.restore();
      }

      // 9. COMPASS ROSE (Safely placed in bottom-left corner with zero label overlap)
      ctx.save();
      const compassX = 38;
      const compassY = h - 38;
      ctx.fillStyle = 'rgba(12, 19, 22, 0.85)';
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.15)';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.arc(compassX, compassY, 20, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();

      const northAngle = isIso ? -Math.PI / 4 : -Math.PI / 2;
      ctx.save();
      ctx.translate(compassX, compassY);
      ctx.rotate(northAngle);

      // North needle (Amber)
      ctx.fillStyle = '#FFB020';
      ctx.beginPath();
      ctx.moveTo(0, -14);
      ctx.lineTo(4, 0);
      ctx.lineTo(-4, 0);
      ctx.closePath();
      ctx.fill();

      // South needle (Grey)
      ctx.fillStyle = '#4A5458';
      ctx.beginPath();
      ctx.moveTo(0, 14);
      ctx.lineTo(4, 0);
      ctx.lineTo(-4, 0);
      ctx.closePath();
      ctx.fill();

      ctx.restore();

      ctx.fillStyle = '#FFB020';
      ctx.font = 'bold 9px JetBrains Mono, monospace';
      ctx.textAlign = 'center';
      ctx.fillText('N', compassX, compassY - 24);
      ctx.restore();

      animationFrameId = requestAnimationFrame(render);
    };

    animationFrameId = requestAnimationFrame(render);
    return () => cancelAnimationFrame(animationFrameId);
  }, [
    activeFrame,
    nextFrame,
    isExploded,
    soloTier,
    zoom,
    pan,
    viewMode,
    isDark,
    showDetectors,
    showLabels,
    selectedVehicleId,
    isFollowMode,
  ]);

  return (
    <div
      ref={containerRef}
      className={`relative w-full overflow-hidden select-none bg-[#0D1417] text-[#F3EDE0] ${className}`}
      style={{ height: height || 480 }}
    >
      {/* 1. Canvas Viewport */}
      <canvas
        ref={canvasRef}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onDoubleClick={handleDoubleClick}
        onClick={handleCanvasClick}
        className="w-full h-full block cursor-grab active:cursor-grabbing"
      />

      {/* 2. Top-Left: Mode Label & Status Badge */}
      <div className="absolute top-3 left-3 flex flex-wrap items-center gap-2 pointer-events-none z-20">
        <div className="px-3 py-1 rounded-full bg-[#0C1316]/90 border border-white/10 text-xs font-mono font-semibold text-[#F3EDE0] flex items-center gap-2 shadow-lg backdrop-blur-md">
          <span className="w-2 h-2 rounded-full bg-[#2FA866] animate-pulse" />
          <span>{modeLabel || 'PHASORA DIGITAL TWIN'}</span>
        </div>

        <div className="px-2.5 py-1 rounded-full bg-[#0C1316]/80 border border-white/10 text-[11px] font-mono text-[#AEB8BA] hidden sm:flex items-center gap-1.5 shadow-md">
          <span>{activeFrame?.vehicles?.length || 0} active vehs</span>
          <span>•</span>
          <span>{viewMode.toUpperCase()}</span>
        </div>
      </div>

      {/* 3. Top-Right: Camera Presets & Explode Action */}
      {showControls && (
        <div className="absolute top-3 right-3 flex items-center gap-2 z-20">
          {/* Explode 3-Tier Toggle Button */}
          <button
            type="button"
            onClick={toggleExplode}
            className={`px-3 py-1.5 rounded-full text-xs font-mono font-bold flex items-center gap-1.5 transition-all shadow-md backdrop-blur-md ${
              isExploded
                ? 'bg-[#FFB020] text-[#0C1316] ring-2 ring-[#FFB020]/40'
                : 'bg-[#0C1316]/90 text-[#F3EDE0] hover:bg-[#1A2327] border border-white/15'
            }`}
          >
            <Layers size={13} />
            <span>{isExploded ? 'Collapse View' : 'Explode 3-Tier View'}</span>
          </button>

          {/* View Mode Dropdown */}
          <div className="flex items-center bg-[#0C1316]/90 border border-white/15 rounded-full p-0.5 shadow-md">
            <button
              type="button"
              onClick={() => setViewMode('isometric')}
              className={`px-2.5 py-1 rounded-full text-xs font-mono font-semibold transition-colors ${
                viewMode === 'isometric' ? 'bg-[#1A2327] text-[#FFB020]' : 'text-[#AEB8BA] hover:text-white'
              }`}
            >
              2.5D Iso
            </button>
            <button
              type="button"
              onClick={() => setViewMode('topdown')}
              className={`px-2.5 py-1 rounded-full text-xs font-mono font-semibold transition-colors ${
                viewMode === 'topdown' ? 'bg-[#1A2327] text-[#FFB020]' : 'text-[#AEB8BA] hover:text-white'
              }`}
            >
              Top-Down
            </button>
          </div>
        </div>
      )}

      {/* 4. Bottom-Right: Zoom Steps & Navigation Toolbar */}
      {showControls && (
        <div className="absolute bottom-3 right-3 flex items-center gap-1.5 bg-[#0C1316]/90 border border-white/15 rounded-full p-1 shadow-lg backdrop-blur-md z-20">
          <button
            type="button"
            onClick={handleZoomOut}
            disabled={zoom <= MIN_ZOOM}
            title={`Zoom Out (- min ${Math.round(MIN_ZOOM * 100)}%)`}
            className="w-7 h-7 rounded-full flex items-center justify-center text-[#AEB8BA] hover:text-white hover:bg-white/10 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
          >
            <ZoomOut size={14} />
          </button>

          <span className="text-[11px] font-mono font-bold text-[#FFB020] px-1 min-w-[42px] text-center">
            {Math.round(zoom * 100)}%
          </span>

          <button
            type="button"
            onClick={handleZoomIn}
            disabled={zoom >= MAX_ZOOM}
            title={`Zoom In (+ max ${Math.round(MAX_ZOOM * 100)}%)`}
            className="w-7 h-7 rounded-full flex items-center justify-center text-[#AEB8BA] hover:text-white hover:bg-white/10 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
          >
            <ZoomIn size={14} />
          </button>

          <div className="w-[1px] h-4 bg-white/15 mx-0.5" />

          <button
            type="button"
            onClick={handleResetView}
            title="Fit to View (F)"
            className="w-7 h-7 rounded-full flex items-center justify-center text-[#AEB8BA] hover:text-white hover:bg-white/10 transition-colors"
          >
            <Maximize2 size={13} />
          </button>
        </div>
      )}

      {/* 5. Bottom-Left Quick Approach Fly Buttons */}
      {showControls && (
        <div className="absolute bottom-3 left-16 hidden md:flex items-center gap-1 bg-[#0C1316]/90 border border-white/15 rounded-full p-1 shadow-md z-20 text-[10px] font-mono">
          <span className="text-[#AEB8BA] px-2">Fly to:</span>
          {['N', 'S', 'W', 'E'].map((app) => (
            <button
              key={app}
              type="button"
              onClick={() => flyToApproach(app)}
              className="px-2 py-0.5 rounded-full bg-white/5 hover:bg-[#FFB020] hover:text-[#0C1316] text-[#F3EDE0] font-bold transition-colors"
            >
              {app}
            </button>
          ))}
        </div>
      )}

      {/* 6. Vehicle Detail Hover / Click Card */}
      {(hoveredVehicle || (selectedVehicleId && activeFrame)) && (
        <div
          className="absolute z-30 pointer-events-auto bg-[#0C1316]/95 border border-[#FFB020]/40 rounded-xl p-3 shadow-2xl backdrop-blur-md text-xs font-mono space-y-2 min-w-[200px]"
          style={{
            left: Math.min(
              (containerRef.current?.clientWidth || 400) - 220,
              Math.max(10, (hoveredVehicle?.screenX || 100) + 12)
            ),
            top: Math.min(
              (containerRef.current?.clientHeight || 400) - 150,
              Math.max(10, (hoveredVehicle?.screenY || 100) - 20)
            ),
          }}
        >
          <div className="flex items-center justify-between border-b border-white/10 pb-1.5">
            <span className="font-bold text-[#FFB020]">
              {hoveredVehicle?.id || selectedVehicleId}
            </span>
            <span className="text-[10px] text-[#AEB8BA] uppercase">
              {hoveredVehicle?.typeName || 'Vehicle'}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-2 text-[11px]">
            <div>
              <span className="text-[#AEB8BA] block text-[9px] uppercase">Speed</span>
              <span className="font-bold text-white">
                {(hoveredVehicle?.speed_kmh || 0).toFixed(1)} km/h
              </span>
            </div>
            <div>
              <span className="text-[#AEB8BA] block text-[9px] uppercase">Wait Time</span>
              <span className="font-bold text-white">
                {(hoveredVehicle?.wait_s || 0).toFixed(1)} s
              </span>
            </div>
          </div>

          <div className="pt-1 border-t border-white/10 flex items-center justify-between">
            <button
              type="button"
              onClick={() => setIsFollowMode((prev) => !prev)}
              className={`px-2 py-0.5 rounded text-[10px] font-bold flex items-center gap-1 transition-colors ${
                isFollowMode ? 'bg-[#FFB020] text-[#0C1316]' : 'bg-white/10 text-white hover:bg-white/20'
              }`}
            >
              <LocateFixed size={10} />
              <span>{isFollowMode ? 'Following' : 'Follow'}</span>
            </button>
            <span className="text-[10px] text-[#4FB3C2] uppercase">
              {hoveredVehicle?.tier || 'Surface'}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

export default IsometricIntersection;
