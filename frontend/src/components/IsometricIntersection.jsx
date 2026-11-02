import React, { useRef, useEffect, useState, useCallback, useMemo, Suspense } from 'react';
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

import { isWebGLAvailable } from '../utils/network3dGeometry';

export { isWebGLAvailable };

// Lazy-load Phase 4 3D Scene chunk to keep main bundle small
const Network3DScene = React.lazy(() => import('./Network3DScene'));

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
  vehicleScale = null,
  defaultSeeThroughFlyover = true,
  defaultShowTrails = true,
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
  const [viewMode, setViewMode] = useState(initialViewMode); // 'isometric' | 'topdown' | '3d'
  const [webglNotice, setWebglNotice] = useState(null);

  const handleSetViewMode = useCallback((mode) => {
    if (mode === '3d') {
      if (!isWebGLAvailable()) {
        setWebglNotice('WebGL is unavailable in this environment. Falling back to 2.5D view.');
        setViewMode('isometric');
        return;
      }
    }
    setWebglNotice(null);
    setViewMode(mode);
  }, []);

  const [showDetectors, setShowDetectors] = useState(true);
  const [showLabels, setShowLabels] = useState(true);

  // Phase 2 Vehicle Scale Exaggeration: 1.0 (True scale), 2.0 (Default Exaggerate 2x), 3.0 (Max Exaggerate 3x)
  const [vehicleScaleMultiplier, setVehicleScaleMultiplier] = useState(
    typeof vehicleScale === 'number' ? vehicleScale : 2.0
  );

  // Phase 2 See-Through Flyover Deck Toggle (Default: true near junction)
  const [seeThroughFlyover, setSeeThroughFlyover] = useState(defaultSeeThroughFlyover);

  // Phase 2 Vehicle Movement Trails & Glow Toggle (Default: true)
  const [showTrails, setShowTrails] = useState(defaultShowTrails);

  // Phase 2 Map Legend Overlay Toggle (Default: true)
  const [showLegend, setShowLegend] = useState(true);

  // Phase 2 Live Telemetry Buffering (one-tick buffer, never extrapolate past latest tick)
  const liveHistoryRef = useRef({ prev: null, current: null, lastReceivedAt: Date.now(), intervalMs: 1500 });
  const [liveTelemetryAgeMs, setLiveTelemetryAgeMs] = useState(0);

  // Vehicle trail histories for fading movement trails: Map<vehicleId, Array<{x, y, t}>>
  const vehicleTrailsRef = useRef(new Map());

  // Update live telemetry buffer when new live payload arrives
  useEffect(() => {
    if (liveTelemetry && isLiveMode) {
      const now = Date.now();
      const prev = liveHistoryRef.current.current;
      const dt = prev ? (now - liveHistoryRef.current.lastReceivedAt) : 1500;
      liveHistoryRef.current = {
        prev: prev || liveTelemetry,
        current: liveTelemetry,
        lastReceivedAt: now,
        intervalMs: Math.max(400, Math.min(dt, 4000)),
      };
      setLiveTelemetryAgeMs(0);
    }
  }, [liveTelemetry, isLiveMode]);

  // Keep live telemetry age ticker updated
  useEffect(() => {
    if (!isLiveMode) return;
    const interval = setInterval(() => {
      setLiveTelemetryAgeMs(Math.max(0, Date.now() - liveHistoryRef.current.lastReceivedAt));
    }, 150);
    return () => clearInterval(interval);
  }, [isLiveMode]);

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
        t: liveTelemetry.sim_time || liveTelemetry.sim_time_s || 0,
        phase: liveTelemetry.current_phase || liveTelemetry.phase || 'GREEN',
        axis: liveTelemetry.active_axis || liveTelemetry.axis || 'NS',
        tl_state: liveTelemetry.tl_state || 'GGGgrrrrGGGgrrrr',
        queues_m: {
          N: liveTelemetry.approach_queues?.N?.total_queue_m ?? liveTelemetry.queues_m?.N ?? 0,
          S: liveTelemetry.approach_queues?.S?.total_queue_m ?? liveTelemetry.queues_m?.S ?? 0,
          E: liveTelemetry.approach_queues?.E?.total_queue_m ?? liveTelemetry.queues_m?.E ?? 0,
          W: liveTelemetry.approach_queues?.W?.total_queue_m ?? liveTelemetry.queues_m?.W ?? 0,
        },
        vehicles: liveTelemetry.vehicles || [],
        emergency_priority: Boolean(liveTelemetry.emergency_priority),
        emergency_approaching: Boolean(liveTelemetry.emergency_approaching),
      };
    }
    if (replayData && replayData.frames && replayData.frames.length > 0) {
      return replayData.frames[currentFrameIdx] || replayData.frames[0];
    }
    return null;
  }, [isLiveMode, liveTelemetry, replayData, currentFrameIdx]);

  const nextFrame = useMemo(() => {
    if (isLiveMode) {
      return liveHistoryRef.current.current || activeFrame;
    }
    if (!replayData || !replayData.frames) return null;
    return replayData.frames[currentFrameIdx + 1] || activeFrame;
  }, [isLiveMode, liveTelemetry, replayData, currentFrameIdx, activeFrame]);

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
      setIsFollowMode(true);
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
    if (viewMode === '3d') return;
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

      // -------------------------------------------------------------
      // 5. VEHICLE INTERPOLATION & PREPARATION PIPELINE
      // -------------------------------------------------------------
      // Telemetry interpolation (one-tick buffer, strictly bounded to [0.0, 1.0])
      let subFrameProgress = 0.0;
      let prevVehiclesMap = new Map();
      let nextVehiclesMap = new Map();

      if (isLiveMode) {
        const { prev, current, lastReceivedAt, intervalMs } = liveHistoryRef.current;
        if (prev && current) {
          const elapsed = Date.now() - lastReceivedAt;
          subFrameProgress = Math.min(1.0, Math.max(0.0, elapsed / intervalMs));
          if (prev.vehicles) {
            prev.vehicles.forEach((v) => prevVehiclesMap.set(v.id, v));
          }
          if (current.vehicles) {
            current.vehicles.forEach((v) => nextVehiclesMap.set(v.id, v));
          }
        }
      } else {
        subFrameProgress = Math.min(1.0, Math.max(0.0, frameAccumulatorRef.current));
        if (nextFrame && nextFrame.vehicles) {
          nextFrame.vehicles.forEach((v) => nextVehiclesMap.set(v.id, v));
        }
      }

      const currentVehicles = activeFrame?.vehicles || [];

      // Camera tracking if Follow Mode is active
      if (isFollowMode && selectedVehicleId) {
        const followed = currentVehicles.find((v) => v.id === selectedVehicleId);
        if (followed) {
          const pt = worldToScreen(followed.x, followed.y, 0, 'surface');
          const targetPanX = panRef.current.x + (w / 2 - pt.x) * 0.1;
          const targetPanY = panRef.current.y + (h / 2 - pt.y) * 0.1;
          panRef.current = { x: targetPanX, y: targetPanY };
        }
      }

      // Vehicle scale multiplier & minimum on-screen sizing clamp (min 8px length, 4px width)
      const minVehiclePx = 8.0;
      const scaleMult = vehicleScaleMultiplier || 2.0;

      const preparedVehicles = [];
      let closestHovered = null;
      let minHoverDist = 22;

      currentVehicles.forEach((veh) => {
        const v1 = isLiveMode ? (prevVehiclesMap.get(veh.id) || veh) : veh;
        const v2 = nextVehiclesMap.get(veh.id) || v1;

        // Smooth position and shortest-angle heading interpolation
        const interpX = v1.x + (v2.x - v1.x) * subFrameProgress;
        const interpY = v1.y + (v2.y - v1.y) * subFrameProgress;
        let da = ((v2.a - v1.a + 540) % 360) - 180;
        const interpA = (v1.a + da * subFrameProgress + 360) % 360;
        const interpS = v1.s + (v2.s - v1.s) * subFrameProgress;

        // Tier classification: check explicit elevation z, tier field, or robust geometric bounds
        let vehTier = 'surface';
        let vehZ = 0.0;
        if (veh.z !== undefined && veh.z !== null) {
          const zNum = Number(veh.z);
          vehZ = zNum;
          if (zNum >= 5.0) vehTier = 'flyover';
          else if (zNum < -1.0) vehTier = 'underpass';
          else vehTier = 'surface';
        } else if (veh.tier) {
          vehTier = veh.tier;
          vehZ = vehTier === 'flyover' ? 7.0 : (vehTier === 'underpass' ? -4.0 : 0.0);
        } else {
          const isEastWest = Math.abs(interpA - 90) < 35 || Math.abs(interpA - 270) < 35;
          const isNorthSouth = Math.abs(interpA - 0) < 35 || Math.abs(interpA - 180) < 35;
          if (Math.abs(interpY - 350) <= 7.5 && isEastWest && interpX >= 170 && interpX <= 530) {
            vehTier = 'flyover';
            vehZ = 7.0;
          } else if (Math.abs(interpX - 350) <= 7.5 && isNorthSouth && interpY >= 170 && interpY <= 530 && interpS > 8.0) {
            vehTier = 'underpass';
            vehZ = -4.0;
          }
        }

        const opacity = getTierOpacity(vehTier);
        if (opacity <= 0.01) return;

        const screenPt = worldToScreen(interpX, interpY, vehZ, vehTier);
        const headingAngle = sumoAngleToScreen(interpA);
        const vType = getVehicleType(veh);
        const spec = VEHICLE_SPECS[vType] || VEHICLE_SPECS.car;

        // Sizing with exaggeration control & minimum on-screen visibility floor
        const baseLen = spec.len * baseScale * scaleMult;
        const baseWid = spec.wid * baseScale * scaleMult;
        const vehLen = Math.max(minVehiclePx, baseLen);
        const vehWid = Math.max(minVehiclePx * (spec.wid / spec.len), baseWid);

        // Queued detection: speed < 0.8 m/s or explicit queued flag / delay
        const isQueued = interpS < 0.8 || Boolean(veh.queued) || Boolean(veh.w > 1);

        // Movement trail recording
        if (showTrails) {
          let tr = vehicleTrailsRef.current.get(veh.id);
          if (!tr) {
            tr = [];
            vehicleTrailsRef.current.set(veh.id, tr);
          }
          const lastPt = tr[tr.length - 1];
          if (!lastPt || Math.hypot(screenPt.x - lastPt.x, screenPt.y - lastPt.y) > 2) {
            tr.push({ x: screenPt.x, y: screenPt.y, t: Date.now() });
            if (tr.length > 5) tr.shift();
          }
        }

        // Hover detection
        const mPos = mousePosRef.current;
        const mouseDist = Math.hypot(mPos.x - screenPt.x, mPos.y - screenPt.y);
        if (mouseDist < minHoverDist) {
          minHoverDist = mouseDist;
          closestHovered = {
            id: veh.id,
            type: vType,
            typeName: spec.name,
            speed_mps: interpS,
            speed_kmh: interpS * 3.6,
            wait_s: veh.w || 0,
            screenX: screenPt.x,
            screenY: screenPt.y,
            tier: vehTier,
            isQueued,
            lane_id: veh.lane_id || (vehTier === 'flyover' ? 'flyover_e2w' : (vehTier === 'underpass' ? 'orr_underpass' : 'surface_tls')),
          };
        }

        preparedVehicles.push({
          v1,
          v2,
          interpX,
          interpY,
          interpA,
          interpS,
          vehTier,
          vehZ,
          opacity,
          screenPt,
          headingAngle,
          vType,
          spec,
          vehLen,
          vehWid,
          isQueued,
        });
      });

      // Hover update for state
      hoveredVehicleRef.current = closestHovered;
      setHoveredVehicle((prev) => {
        if (!prev && !closestHovered) return null;
        if (prev && closestHovered && prev.id === closestHovered.id) {
          if (
            Math.abs(prev.screenX - closestHovered.screenX) < 1 &&
            Math.abs(prev.screenY - closestHovered.screenY) < 1 &&
            prev.speed_kmh === closestHovered.speed_kmh &&
            prev.isQueued === closestHovered.isQueued
          ) {
            return prev;
          }
        }
        return closestHovered;
      });

      // Partition vehicles by tier for physical depth layering
      const underpassVehicles = [];
      const surfaceVehicles = [];
      const flyoverVehicles = [];
      preparedVehicles.forEach((item) => {
        if (item.vehTier === 'underpass') underpassVehicles.push(item);
        else if (item.vehTier === 'flyover') flyoverVehicles.push(item);
        else surfaceVehicles.push(item);
      });

      // Unified Single Vehicle Renderer
      const drawSingleVehicle = (item) => {
        const { v1, v2, interpS, vType, spec, vehLen, vehWid, opacity, screenPt, headingAngle, isQueued } = item;

        // Fading movement trails
        if (showTrails && interpS > 1.0) {
          const tr = vehicleTrailsRef.current.get(v1.id);
          if (tr && tr.length >= 2) {
            ctx.save();
            for (let i = 0; i < tr.length - 1; i++) {
              const pA = tr[i];
              const pB = tr[i + 1];
              const alpha = ((i + 1) / tr.length) * 0.35 * opacity;
              ctx.strokeStyle = isDark ? `rgba(56, 189, 248, ${alpha})` : `rgba(2, 132, 199, ${alpha})`;
              ctx.lineWidth = Math.max(1.5, vehWid * 0.4);
              ctx.lineCap = 'round';
              ctx.beginPath();
              ctx.moveTo(pA.x, pA.y);
              ctx.lineTo(pB.x, pB.y);
              ctx.stroke();
            }
            ctx.restore();
          }
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

        // High-contrast color hierarchy:
        // Moving: Sky Blue family (#38BDF8 / #00E5FF)
        // Queued / Stopped: Distinct warm amber (#F59E0B / #D97706)
        // Ambulance: Pure White (#FFFFFF) with pulsing halo
        let bodyColor;
        if (vType === 'ambulance') {
          bodyColor = '#FFFFFF';
        } else if (isQueued) {
          bodyColor = isDark ? '#F59E0B' : '#D97706';
        } else {
          bodyColor = isDark ? '#38BDF8' : '#0284C7';
          if (vType === 'bus') bodyColor = isDark ? '#00E5FF' : '#0891B2';
          else if (vType === 'truck') bodyColor = isDark ? '#7DD3FC' : '#0369A1';
          else if (vType === 'auto' || vType === 'motorcycle') bodyColor = isDark ? '#2DD4BF' : '#0D9488';
        }

        // Ambulance Pulsing Halo
        if (vType === 'ambulance') {
          const pulsePhase = (Date.now() % 1000) / 1000;
          const haloRadius = Math.max(vehLen, vehWid) * (0.8 + 0.3 * Math.sin(pulsePhase * Math.PI * 2));
          const haloAlpha = 0.55 * (1 - Math.sin(pulsePhase * Math.PI * 2) * 0.3);
          ctx.save();
          ctx.strokeStyle = `rgba(239, 68, 68, ${haloAlpha})`;
          ctx.lineWidth = 2.0;
          ctx.beginPath();
          ctx.arc(0, 0, haloRadius, 0, Math.PI * 2);
          ctx.stroke();
          ctx.fillStyle = `rgba(239, 68, 68, ${haloAlpha * 0.25})`;
          ctx.fill();
          ctx.restore();
        }

        // Vehicle Body Fill
        ctx.fillStyle = bodyColor;
        ctx.beginPath();
        drawSafeRoundRect(ctx, -vehLen / 2, -vehWid / 2, vehLen, vehWid, spec.radius);
        ctx.fill();

        // Thin light outline (dark outline in light theme) so vehicles never blend into dark asphalt
        ctx.strokeStyle = isDark ? '#FFFFFF' : '#0F172A';
        ctx.lineWidth = 1.0;
        ctx.stroke();

        // Heading arrow on vehicle roof
        ctx.fillStyle = isDark ? 'rgba(255, 255, 255, 0.9)' : 'rgba(15, 23, 42, 0.9)';
        ctx.beginPath();
        const arrowFront = vehLen * 0.28;
        const arrowBack = vehLen * 0.08;
        const arrowHalfW = Math.max(1.2, vehWid * 0.25);
        ctx.moveTo(arrowFront, 0);
        ctx.lineTo(arrowBack, -arrowHalfW);
        ctx.lineTo(arrowBack, arrowHalfW);
        ctx.closePath();
        ctx.fill();

        // Windscreen & Roof Detail
        if (vType === 'ambulance') {
          ctx.fillStyle = '#EF4444';
          const crossSize = Math.min(vehLen * 0.3, vehWid * 0.7);
          ctx.fillRect(-crossSize / 2, -crossSize / 6, crossSize, crossSize / 3);
          ctx.fillRect(-crossSize / 6, -crossSize / 2, crossSize / 3, crossSize);
          const strobe = Math.floor(Date.now() / 120) % 2 === 0;
          ctx.fillStyle = strobe ? '#EF4444' : '#00E5FF';
          ctx.shadowColor = strobe ? '#EF4444' : '#00E5FF';
          ctx.shadowBlur = 10;
          ctx.beginPath();
          ctx.arc(0, 0, 2.5, 0, Math.PI * 2);
          ctx.fill();
          ctx.shadowBlur = 0;
        } else {
          ctx.fillStyle = isDark ? 'rgba(15, 23, 42, 0.75)' : 'rgba(255, 255, 255, 0.6)';
          ctx.fillRect(vehLen * 0.06, -vehWid * 0.32, vehLen * 0.16, vehWid * 0.64);
          ctx.fillRect(-vehLen * 0.28, -vehWid * 0.32, vehLen * 0.12, vehWid * 0.64);
        }

        // Brake Lights (Illuminated when queued or decelerating)
        const isBraking = isQueued || interpS < 0.8 || (v2.s < v1.s - 0.2);
        ctx.fillStyle = isBraking ? '#FF2E2E' : 'rgba(214, 69, 61, 0.35)';
        if (isBraking) {
          ctx.shadowColor = '#FF2E2E';
          ctx.shadowBlur = 6;
        }
        ctx.beginPath();
        ctx.arc(-vehLen / 2 + 0.5, -vehWid * 0.32, 1.2, 0, Math.PI * 2);
        ctx.arc(-vehLen / 2 + 0.5, vehWid * 0.32, 1.2, 0, Math.PI * 2);
        ctx.fill();
        ctx.shadowBlur = 0;

        // Headlight glow & forward light cones (when moving)
        if (interpS > 1.0) {
          ctx.fillStyle = isDark ? 'rgba(56, 189, 248, 0.12)' : 'rgba(255, 235, 120, 0.18)';
          ctx.beginPath();
          ctx.moveTo(vehLen / 2, -vehWid * 0.32);
          ctx.lineTo(vehLen / 2 + 18, -vehWid * 0.95);
          ctx.lineTo(vehLen / 2 + 18, vehWid * 0.95);
          ctx.lineTo(vehLen / 2, vehWid * 0.32);
          ctx.closePath();
          ctx.fill();

          ctx.fillStyle = '#FFF8E7';
          ctx.beginPath();
          ctx.arc(vehLen / 2 - 0.5, -vehWid * 0.32, 1.2, 0, Math.PI * 2);
          ctx.arc(vehLen / 2 - 0.5, vehWid * 0.32, 1.2, 0, Math.PI * 2);
          ctx.fill();
        }

        // Selection reticle / tracking circle
        if (selectedVehicleId === v1.id) {
          ctx.strokeStyle = '#F59E0B';
          ctx.lineWidth = 2.0;
          ctx.beginPath();
          ctx.arc(0, 0, Math.max(vehLen, vehWid) * 0.75, 0, Math.PI * 2);
          ctx.stroke();

          const r = Math.max(vehLen, vehWid) * 0.9;
          ctx.setLineDash([4, 4]);
          ctx.beginPath();
          ctx.arc(0, 0, r, 0, Math.PI * 2);
          ctx.stroke();
          ctx.setLineDash([]);
        }

        ctx.restore();
      };

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

      // Draw Underpass Vehicles (rendered in underpass trench)
      underpassVehicles.forEach(drawSingleVehicle);

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

        // E2 Detectors Translucent Zones & Status-Aware Color Coding
        if (showDetectors) {
          const queues = activeFrame?.queues_m || { N: 0, S: 0, E: 0, W: 0 };
          marathahalliGeom.detectors.forEach((det) => {
            if (det.shape && det.shape.length >= 2) {
              const qVal = queues[det.approach] || 0;
              const isOffline = det.sensor_status === 'OFFLINE' || det.data_valid === false;
              const isSaturated = qVal >= 24.0 || det.is_saturated;
              const isZero = qVal === 0.0;

              let strokeColor, fillColor;
              if (isOffline) {
                strokeColor = '#64748B'; // Hatched slate grey
                fillColor = 'rgba(100, 116, 139, 0.25)';
              } else if (isSaturated) {
                strokeColor = '#EF4444'; // Saturated alert red
                fillColor = 'rgba(239, 68, 68, 0.45)';
              } else if (isZero) {
                strokeColor = '#10B981'; // Confirmed zero emerald
                fillColor = 'rgba(16, 185, 129, 0.25)';
              } else {
                strokeColor = '#FFB020'; // Measuring amber
                fillColor = 'rgba(255, 176, 32, 0.35)';
              }

              const p1 = worldToScreen(det.shape[0][0], det.shape[0][1], 0.0, 'surface');
              const p2 = worldToScreen(det.shape[1][0], det.shape[1][1], 0.0, 'surface');

              ctx.save();
              ctx.strokeStyle = fillColor;
              ctx.lineWidth = 4.0 * baseScale;
              ctx.lineCap = 'butt';
              ctx.beginPath();
              ctx.moveTo(p1.x, p1.y);
              ctx.lineTo(p2.x, p2.y);
              ctx.stroke();

              ctx.strokeStyle = strokeColor;
              if (isOffline) {
                ctx.setLineDash([4 * zoom, 4 * zoom]);
              }
              ctx.lineWidth = 2.0 * baseScale;
              const fillRatio = Math.min(1.0, Math.max(0.06, qVal / 24.9));
              const qFillX = p1.x + (p2.x - p1.x) * fillRatio;
              const qFillY = p1.y + (p2.y - p1.y) * fillRatio;
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

      // Draw Surface Vehicles (rendered directly on surface roadways and below flyover deck)
      surfaceVehicles.forEach(drawSingleVehicle);

      // 5.3 TIER 1: ELEVATED FLYOVER OVERPASS
      if (getTierOpacity('flyover') > 0.01) {
        ctx.save();
        const flyoverOpacity = getTierOpacity('flyover');
        // When seeThroughFlyover is enabled, ghost the deck ribbons (alpha 0.35x) so vehicles below are clearly visible
        const deckAlpha = seeThroughFlyover ? (0.35 * flyoverOpacity) : flyoverOpacity;
        ctx.globalAlpha = deckAlpha;

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

      // Draw Flyover Vehicles (rendered on top of elevated flyover deck)
      flyoverVehicles.forEach(drawSingleVehicle);

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
    vehicleScaleMultiplier,
    seeThroughFlyover,
    showTrails,
  ]);

  const totalVehiclesCount = activeFrame?.vehicles?.length || 0;
  const queuedVehiclesCount = (activeFrame?.vehicles || []).filter(
    (v) => (v.s !== undefined ? v.s < 0.1 : (v.speed !== undefined ? v.speed < 0.1 : false)) || (v.w > 0)
  ).length;

  return (
    <div
      ref={containerRef}
      className={`relative w-full overflow-hidden select-none bg-[#0D1417] text-[#F3EDE0] ${className}`}
      style={{ height: height || 480 }}
    >
      {/* 1. Canvas Viewport (2.5D Iso / Top-Down) */}
      <canvas
        ref={canvasRef}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onDoubleClick={handleDoubleClick}
        onClick={handleCanvasClick}
        style={{ display: viewMode === '3d' ? 'none' : 'block' }}
        className="w-full h-full cursor-grab active:cursor-grabbing"
      />

      {/* 1b. 3D WebGL Viewport (Lazy-Loaded chunk with Suspense fallback) */}
      {viewMode === '3d' && (
        <div className="absolute inset-0 z-0">
          <Suspense
            fallback={
              <div className="w-full h-full flex flex-col items-center justify-center bg-[#0C1316] text-[#AEB8BA] font-mono">
                <div className="w-8 h-8 border-2 border-[#FFB020] border-t-transparent rounded-full animate-spin mb-3" />
                <span className="text-sm">Loading 3D Road Scene...</span>
              </div>
            }
          >
            <Network3DScene
              isDark={isDark}
              seeThroughFlyover={seeThroughFlyover}
              isExploded={isExploded}
              onExplodeToggle={toggleExplode}
              onSeeThroughToggle={() => setSeeThroughFlyover((prev) => !prev)}
              showControls={showControls}
              className="w-full h-full"
              activeFrame={activeFrame}
              prevFrame={isLiveMode ? liveHistoryRef.current?.prev : (replayData?.frames?.[currentFrameIdx - 1] || null)}
              interpolationAlpha={frameAccumulatorRef.current}
              vehicleScale={vehicleScaleMultiplier}
              onVehicleScaleChange={setVehicleScaleMultiplier}
              trafficLightState={activeFrame?.tl_state || activeFrame?.traffic_light_state || liveTelemetry?.traffic_light_state || 'rrrrGGGgrrrrGGGg'}
              activePhase={activeFrame?.phase || liveTelemetry?.phase || 'GREEN'}
              approachQueues={liveTelemetry?.approach_queues || null}
              queues_m={activeFrame?.queues_m || liveTelemetry?.queues_m || {}}
              adaptiveDecision={liveTelemetry?.adaptive_decision || null}
              simTime={activeFrame?.t || 0}
              isLiveMode={isLiveMode}
              runId={runId}
              modeLabel={modeLabel || (isLiveMode ? 'Live simulation' : (replayData ? 'Replay' : 'Snapshot'))}
            />
          </Suspense>
        </div>
      )}

      {/* WebGL Fallback Notification Banner */}
      {webglNotice && (
        <div className="absolute top-14 left-1/2 -translate-x-1/2 bg-amber-500/95 text-black px-4 py-1.5 rounded-full text-xs font-mono font-semibold shadow-lg backdrop-blur-md z-30 flex items-center gap-2">
          <span>{webglNotice}</span>
          <button
            type="button"
            onClick={() => setWebglNotice(null)}
            className="font-bold hover:opacity-75 px-1"
          >
            ✕
          </button>
        </div>
      )}

      {/* 2. Top-Left: Mode Label & Status Badge */}
      <div className="absolute top-3 left-3 flex flex-wrap items-center gap-2 pointer-events-none z-20">
        <div className="px-3 py-1 rounded-full bg-[#0C1316]/90 border border-white/10 text-xs font-mono font-semibold text-[#F3EDE0] flex items-center gap-2 shadow-lg backdrop-blur-md">
          <span className="w-2 h-2 rounded-full bg-[#2FA866] animate-pulse" />
          <span>{modeLabel || 'PHASORA DIGITAL TWIN'}</span>
        </div>

        <div className="px-2.5 py-1 rounded-full bg-[#0C1316]/80 border border-white/10 text-[11px] font-mono text-[#AEB8BA] hidden sm:flex items-center gap-1.5 shadow-md">
          <span className="font-semibold text-white">
            {totalVehiclesCount} vehs in network ({queuedVehiclesCount} queued)
          </span>
          <span>•</span>
          <span>{viewMode.toUpperCase()}</span>
          {isLiveMode && liveTelemetryAgeMs !== null && (
            <>
              <span>•</span>
              <span className="text-[#38BDF8]">
                Age: {(liveTelemetryAgeMs / 1000).toFixed(1)}s
              </span>
            </>
          )}
        </div>
      </div>

      {/* 3. Top-Right: Camera Presets & Visibility Controls */}
      {showControls && (
        <div className="absolute top-3 right-3 flex flex-wrap items-center gap-2 z-20 justify-end max-w-[calc(100%-250px)]">
          {/* Exaggerate Vehicles Control (1x True, 2x Default, 3x Max) */}
          <div className="flex items-center bg-[#0C1316]/90 border border-white/15 rounded-full p-0.5 shadow-md backdrop-blur-md">
            <span className="text-[10px] font-mono text-[#AEB8BA] px-2 hidden md:inline">Scale:</span>
            {[
              { label: '1x True', val: 1.0 },
              { label: '2x (Def)', val: 2.0 },
              { label: '3x Max', val: 3.0 },
            ].map((sc) => (
              <button
                key={sc.val}
                type="button"
                onClick={() => setVehicleScaleMultiplier(sc.val)}
                className={`px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold transition-colors ${
                  vehicleScaleMultiplier === sc.val
                    ? 'bg-[#38BDF8] text-[#0C1316] font-bold shadow-sm'
                    : 'text-[#AEB8BA] hover:text-white'
                }`}
                title={`Scale vehicles by ${sc.label}`}
              >
                {sc.label}
              </button>
            ))}
          </div>

          {/* See-Through Flyover Toggle */}
          <button
            type="button"
            onClick={() => setSeeThroughFlyover((prev) => !prev)}
            className={`px-2.5 py-1 rounded-full text-xs font-mono font-semibold flex items-center gap-1 transition-all shadow-md backdrop-blur-md ${
              seeThroughFlyover
                ? 'bg-[#38BDF8]/20 text-[#38BDF8] border border-[#38BDF8]/50'
                : 'bg-[#0C1316]/90 text-[#AEB8BA] hover:bg-[#1A2327] border border-white/15'
            }`}
            title="Ghost elevated flyover deck so surface traffic beneath is visible"
          >
            <Eye size={12} />
            <span className="hidden sm:inline">See-Through</span>
          </button>

          {/* Trails Toggle */}
          <button
            type="button"
            onClick={() => setShowTrails((prev) => !prev)}
            className={`px-2.5 py-1 rounded-full text-xs font-mono font-semibold flex items-center gap-1 transition-all shadow-md backdrop-blur-md ${
              showTrails
                ? 'bg-[#38BDF8]/20 text-[#38BDF8] border border-[#38BDF8]/50'
                : 'bg-[#0C1316]/90 text-[#AEB8BA] hover:bg-[#1A2327] border border-white/15'
            }`}
            title="Toggle vehicle motion trails & headlight illumination"
          >
            <Activity size={12} />
            <span className="hidden sm:inline">Trails</span>
          </button>

          {/* Explode 3-Tier Toggle Button */}
          <button
            type="button"
            onClick={toggleExplode}
            className={`px-3 py-1 rounded-full text-xs font-mono font-bold flex items-center gap-1.5 transition-all shadow-md backdrop-blur-md ${
              isExploded
                ? 'bg-[#FFB020] text-[#0C1316] ring-2 ring-[#FFB020]/40'
                : 'bg-[#0C1316]/90 text-[#F3EDE0] hover:bg-[#1A2327] border border-white/15'
            }`}
          >
            <Layers size={13} />
            <span>{isExploded ? 'Collapse' : '3-Tier'}</span>
          </button>

          {/* View Mode Toggle: 2.5D Iso, Top-Down, 3D */}
          <div className="flex items-center bg-[#0C1316]/90 border border-white/15 rounded-full p-0.5 shadow-md">
            <button
              type="button"
              onClick={() => handleSetViewMode('isometric')}
              className={`px-2.5 py-1 rounded-full text-xs font-mono font-semibold transition-colors ${
                viewMode === 'isometric' ? 'bg-[#1A2327] text-[#FFB020]' : 'text-[#AEB8BA] hover:text-white'
              }`}
            >
              2.5D
            </button>
            <button
              type="button"
              onClick={() => handleSetViewMode('topdown')}
              className={`px-2.5 py-1 rounded-full text-xs font-mono font-semibold transition-colors ${
                viewMode === 'topdown' ? 'bg-[#1A2327] text-[#FFB020]' : 'text-[#AEB8BA] hover:text-white'
              }`}
            >
              Top-Down
            </button>
            <button
              type="button"
              onClick={() => handleSetViewMode('3d')}
              className={`px-2.5 py-1 rounded-full text-xs font-mono font-semibold transition-colors ${
                viewMode === '3d' ? 'bg-[#1A2327] text-[#FFB020]' : 'text-[#AEB8BA] hover:text-white'
              }`}
            >
              3D
            </button>
          </div>

          {/* Legend Toggle */}
          <button
            type="button"
            onClick={() => setShowLegend((prev) => !prev)}
            className={`px-2.5 py-1 rounded-full text-xs font-mono font-semibold flex items-center gap-1 transition-all shadow-md backdrop-blur-md ${
              showLegend
                ? 'bg-[#FFB020]/20 text-[#FFB020] border border-[#FFB020]/50'
                : 'bg-[#0C1316]/90 text-[#AEB8BA] hover:bg-[#1A2327] border border-white/15'
            }`}
            title="Toggle Map Visual Legend"
          >
            <span>Legend</span>
          </button>
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

      {/* Map Legend Overlay */}
      {showLegend && (
        <div className="absolute bottom-12 left-3 z-20 bg-[#0C1316]/95 border border-white/15 rounded-xl p-2.5 shadow-xl backdrop-blur-md text-[11px] font-mono space-y-2 pointer-events-auto max-w-[210px]">
          <div className="flex items-center justify-between border-b border-white/10 pb-1">
            <span className="font-bold text-[#F3EDE0]">MAP LEGEND</span>
            <button
              type="button"
              onClick={() => setShowLegend(false)}
              className="text-[#AEB8BA] hover:text-white"
            >
              <X size={12} />
            </button>
          </div>
          <div className="space-y-1 text-[10px]">
            <div className="text-[#AEB8BA] uppercase font-bold text-[9px]">Vehicles (High Contrast)</div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-2 rounded-sm bg-[#38BDF8] border border-white/40" />
              <span>Moving Vehicle</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-2 rounded-sm bg-[#F59E0B] border border-white/40" />
              <span>Queued / Stopped</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-2 rounded-sm bg-[#FFFFFF] border border-red-500 shadow-[0_0_6px_rgba(239,68,68,0.8)]" />
              <span>Ambulance (Pulsing)</span>
            </div>
          </div>
          <div className="pt-1 border-t border-white/10 space-y-1 text-[10px]">
            <div className="text-[#AEB8BA] uppercase font-bold text-[9px]">E2 Detectors (Sensors)</div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-1.5 rounded-sm bg-[#10B981]" />
              <span>CONFIRMED_ZERO (Clear)</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-1.5 rounded-sm bg-[#FFB020]" />
              <span>MEASURING (Active Queue)</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-1.5 rounded-sm bg-[#EF4444]" />
              <span>SATURATED (Full Span)</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-1.5 rounded-sm bg-slate-500 border border-dashed border-slate-300" />
              <span>OFFLINE (Fallback)</span>
            </div>
          </div>
        </div>
      )}

      {/* 6. Vehicle Detail Hover / Click Card */}
      {(hoveredVehicle || (selectedVehicleId && activeFrame)) && (
        <div
          className="absolute z-30 pointer-events-auto bg-[#0C1316]/95 border border-[#38BDF8]/50 rounded-xl p-3 shadow-2xl backdrop-blur-md text-xs font-mono space-y-2 min-w-[220px]"
          style={{
            left: Math.min(
              (containerRef.current?.clientWidth || 400) - 240,
              Math.max(10, (hoveredVehicle?.screenX || 100) + 14)
            ),
            top: Math.min(
              (containerRef.current?.clientHeight || 400) - 180,
              Math.max(10, (hoveredVehicle?.screenY || 100) - 20)
            ),
          }}
        >
          <div className="flex items-center justify-between border-b border-white/10 pb-1.5">
            <span className="font-bold text-[#38BDF8]">
              {hoveredVehicle?.id || selectedVehicleId}
            </span>
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-white/10 text-[#F3EDE0] uppercase font-bold">
              {hoveredVehicle?.typeName || 'Vehicle'}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-2 text-[11px]">
            <div>
              <span className="text-[#AEB8BA] block text-[9px] uppercase">Speed</span>
              <span className="font-bold text-white">
                {(hoveredVehicle?.speed_kmh || 0).toFixed(1)} km/h
              </span>
              <span className="text-[10px] text-[#AEB8BA] block">
                ({(hoveredVehicle?.speed_mps || 0).toFixed(1)} m/s)
              </span>
            </div>
            <div>
              <span className="text-[#AEB8BA] block text-[9px] uppercase">Waiting Time</span>
              <span className={`font-bold ${(hoveredVehicle?.wait_s || 0) > 0 ? 'text-[#F59E0B]' : 'text-white'}`}>
                {(hoveredVehicle?.wait_s || 0).toFixed(1)} s
              </span>
              <span className="text-[10px] block text-[#AEB8BA]">
                {hoveredVehicle?.isQueued ? 'QUEUED' : 'MOVING'}
              </span>
            </div>
          </div>

          <div className="pt-1.5 border-t border-white/10 flex items-center justify-between text-[10px]">
            <span className="text-[#AEB8BA]">
              Tier: <strong className="text-white uppercase">{hoveredVehicle?.tier || 'Surface'}</strong>
            </span>
            {hoveredVehicle?.lane_id && (
              <span className="text-[#AEB8BA] truncate max-w-[110px]" title={hoveredVehicle.lane_id}>
                Lane: <strong className="text-white">{hoveredVehicle.lane_id}</strong>
              </span>
            )}
          </div>

          <div className="pt-1 border-t border-white/10 flex items-center justify-between">
            <button
              type="button"
              onClick={() => setIsFollowMode((prev) => !prev)}
              className={`px-2.5 py-1 rounded text-[10px] font-bold flex items-center gap-1 transition-colors ${
                isFollowMode ? 'bg-[#38BDF8] text-[#0C1316]' : 'bg-white/10 text-white hover:bg-white/20'
              }`}
            >
              <LocateFixed size={11} />
              <span>{isFollowMode ? 'Following' : 'Follow Camera'}</span>
            </button>
            <button
              type="button"
              onClick={() => {
                setSelectedVehicleId(null);
                setIsFollowMode(false);
              }}
              className="text-[#AEB8BA] hover:text-white text-[10px]"
            >
              Deselect
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default IsometricIntersection;
