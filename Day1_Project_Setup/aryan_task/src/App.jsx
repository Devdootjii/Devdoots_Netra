import NetraFooter from './NetraFooter';
import NetraHeaderLogo from './NetraHeaderLogo';


import React, { useEffect, useRef, useState } from "react";

function App() {
  // =========================================================
  // API
  // =========================================================

  const BACKEND_BASE = "http://127.0.0.1:8000";
  const AI_ENGINE_BASE = "http://127.0.0.1:8001";

  const API_URL = `${BACKEND_BASE}/api/ai-stream`;
  // FIX: this version was missing the camera-config sync endpoint entirely -
  // without this, connectCamera1() never tells the backend/engine what the
  // phone's URL is, so the engine keeps processing whatever it was on before
  // (or nothing) no matter what you type into the Camera #1 field.
  const CAMERA_CONFIG_URL = `${BACKEND_BASE}/api/update-camera-urls`;
  // FIX: this version had no reference to the engine's processed stream at
  // all - that's why "AI Processed Feed" never showed real output.
  const AI_LIVE_FEED_URL = `${AI_ENGINE_BASE}/live-feed`;
  // FIX: raw preview must also go through the engine, not straight to the
  // phone - DroidCam only allows ONE connected client at a time, so if the
  // browser and the engine both try to open the phone's URL directly, one of
  // them gets DroidCam's "busy" page instead of video.
  const AI_RAW_FEED_URL = `${AI_ENGINE_BASE}/raw-feed`;

  // =========================================================
  // GLOBAL STATE
  // =========================================================

  const [liveData, setLiveData] = useState(null);
  const [isApiConnected, setIsApiConnected] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isAlertActive, setIsAlertActive] = useState(false);

  const [currentTime, setCurrentTime] = useState(
    new Date().toLocaleTimeString()
  );

  const [activePage, setActivePage] = useState("dashboard");
  const [booted, setBooted] = useState(false);

  useEffect(() => {
    const root = document.documentElement;
    let frame = 0;
    const handlePointerMove = (event) => {
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(() => {
        const x = event.clientX / window.innerWidth;
        const y = event.clientY / window.innerHeight;
        root.style.setProperty("--netra-mx", `${(x - 0.5) * 2}`);
        root.style.setProperty("--netra-my", `${(y - 0.5) * 2}`);
        root.style.setProperty("--netra-cursor-x", `${x * 100}%`);
        root.style.setProperty("--netra-cursor-y", `${y * 100}%`);
      });
    };
    window.addEventListener("pointermove", handlePointerMove, { passive: true });
    return () => {
      cancelAnimationFrame(frame);
      window.removeEventListener("pointermove", handlePointerMove);
    };
  }, []);

  // =========================================================
  // DROIDCAM / CAMERA STATE
  // =========================================================

  const DROIDCAM_URL = "http://192.168.1.2:4747";
  const DROIDCAM_VIDEO_URL = "http://192.168.1.2:4747/video";

  const [camera1Url, setCamera1Url] = useState(DROIDCAM_VIDEO_URL);
  const [camera2Url, setCamera2Url] = useState("");

  const [camera1Online, setCamera1Online] = useState(false);
  const [camera2Online, setCamera2Online] = useState(false);

  const [camera1Connecting, setCamera1Connecting] = useState(false);
  const [camera2Connecting, setCamera2Connecting] = useState(false);

  const [camera1Refresh, setCamera1Refresh] = useState(0);
  const [camera2Refresh, setCamera2Refresh] = useState(0);

  const [cameraSyncStatus, setCameraSyncStatus] = useState({
    type: "INFO",
    message: "DroidCam ready. Click Connect Camera #1.",
  });

  const camera1TimeoutRef = useRef(null);
  const camera2TimeoutRef = useRef(null);

  // =========================================================
  // CAMERA HELPERS
  // =========================================================

  const clearCamera1Timeout = () => {
    if (camera1TimeoutRef.current) {
      clearTimeout(camera1TimeoutRef.current);
      camera1TimeoutRef.current = null;
    }
  };

  const clearCamera2Timeout = () => {
    if (camera2TimeoutRef.current) {
      clearTimeout(camera2TimeoutRef.current);
      camera2TimeoutRef.current = null;
    }
  };

  // =========================================================
  // CAMERA URL NORMALIZER
  // =========================================================

  const normalizeCameraUrl = (url) => {
    let cleanUrl = url.trim();

    if (!cleanUrl) return "";

    try {
      const parsed = new URL(cleanUrl);

      if (
        parsed.hostname === "192.168.1.2" &&
        parsed.port === "4747" &&
        (parsed.pathname === "/" || parsed.pathname === "")
      ) {
        parsed.pathname = "/video";
        cleanUrl = parsed.toString();
      }
    } catch {
      // Keep original URL
    }

    return cleanUrl;
  };

  // =========================================================
  // CAMERA 1 CONNECT
  // =========================================================

  const connectCamera1 = () => {
    const url = normalizeCameraUrl(camera1Url);

    if (!url) {
      setCameraSyncStatus({
        type: "ERROR",
        message: "Please enter Camera #1 URL.",
      });

      return;
    }

    clearCamera1Timeout();

    setCamera1Url(url);
    setCamera1Online(false);
    setCamera1Connecting(true);

    setCameraSyncStatus({
      type: "INFO",
      message: "Connecting to DroidCam Camera #1...",
    });

    // FIX (root cause of "processing nahi ho rahi"): this fetch call didn't
    // exist in this version at all. Without it, camera_config.json on the
    // backend never learns your phone's URL, so netra_unified_engine.py has
    // no way to know what to process - it just keeps failing/idling
    // regardless of what you type into this field.
    fetch(CAMERA_CONFIG_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        camera_1_url: url,
        camera_2_url: "",
      }),
    }).catch(() => {
      // Backend abhi unreachable ho sakta hai - status neeche wale onLoad/onError
      // se hi decide ho jayega, isliye yahan silently ignore karna theek hai.
    });

    setCamera1Refresh((prev) => prev + 1);

    camera1TimeoutRef.current = setTimeout(() => {
      setCamera1Connecting(false);
      setCamera1Online(false);

      setCameraSyncStatus({
        type: "ERROR",
        message:
          "DroidCam connection failed. Check phone IP, Wi-Fi and DroidCam app.",
      });
    }, 15000);
  };

  // =========================================================
  // CAMERA 2 CONNECT
  // =========================================================

  const connectCamera2 = () => {
    const url = normalizeCameraUrl(camera2Url);

    if (!url) {
      setCameraSyncStatus({
        type: "ERROR",
        message: "Please enter Camera #2 URL.",
      });

      return;
    }

    clearCamera2Timeout();

    setCamera2Url(url);
    setCamera2Online(false);
    setCamera2Connecting(true);

    setCameraSyncStatus({
      type: "INFO",
      message: "Connecting Camera #2...",
    });

    setCamera2Refresh((prev) => prev + 1);

    camera2TimeoutRef.current = setTimeout(() => {
      setCamera2Connecting(false);
      setCamera2Online(false);

      setCameraSyncStatus({
        type: "ERROR",
        message: "Camera #2 connection failed. Check URL and Wi-Fi.",
      });
    }, 15000);
  };

  // =========================================================
  // CAMERA LOAD
  // =========================================================

  const handleCamera1Load = () => {
    clearCamera1Timeout();

    setCamera1Online(true);
    setCamera1Connecting(false);

    setCameraSyncStatus({
      type: "SUCCESS",
      message: "DroidCam Camera #1 is LIVE.",
    });
  };

  const handleCamera2Load = () => {
    clearCamera2Timeout();

    setCamera2Online(true);
    setCamera2Connecting(false);

    setCameraSyncStatus({
      type: "SUCCESS",
      message: "Camera #2 is LIVE.",
    });
  };

  // =========================================================
  // CAMERA ERROR
  // =========================================================

  const handleCamera1Error = () => {
    clearCamera1Timeout();

    setCamera1Online(false);
    setCamera1Connecting(false);

    setCameraSyncStatus({
      type: "ERROR",
      message:
        "DroidCam stream failed. Make sure http://192.168.1.2:4747 is reachable.",
    });
  };

  const handleCamera2Error = () => {
    clearCamera2Timeout();

    setCamera2Online(false);
    setCamera2Connecting(false);

    setCameraSyncStatus({
      type: "ERROR",
      message: "Camera #2 stream failed.",
    });
  };

  // =========================================================
  // URL CHANGE
  // =========================================================

  const handleCamera1UrlChange = (value) => {
    clearCamera1Timeout();

    setCamera1Url(value);
    setCamera1Online(false);
    setCamera1Connecting(false);
    setCamera1Refresh(0);
  };

  const handleCamera2UrlChange = (value) => {
    clearCamera2Timeout();

    setCamera2Url(value);
    setCamera2Online(false);
    setCamera2Connecting(false);
    setCamera2Refresh(0);
  };

  // =========================================================
  // CAMERA CLEANUP
  // =========================================================

  useEffect(() => {
    return () => {
      clearCamera1Timeout();
      clearCamera2Timeout();
    };
  }, []);

  // =========================================================
  // PROCESSING
  // =========================================================

  const processingTimeoutRef = useRef(null);

  const showProcessing = (duration = 1500) => {
    setIsProcessing(true);

    if (processingTimeoutRef.current) {
      clearTimeout(processingTimeoutRef.current);
    }

    processingTimeoutRef.current = setTimeout(() => {
      setIsProcessing(false);
    }, duration);
  };

  useEffect(() => {
    return () => {
      if (processingTimeoutRef.current) {
        clearTimeout(processingTimeoutRef.current);
      }
    };
  }, []);

  // =========================================================
  // CLOCK
  // =========================================================

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date().toLocaleTimeString());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  // =========================================================
  // BACKEND API POLLING
  // =========================================================

  useEffect(() => {
    let cancelled = false;

    const pollAPI = async () => {
      try {
        const response = await fetch(API_URL);

        if (!response.ok) {
          throw new Error("API response error");
        }

        const data = await response.json();

        if (cancelled) return;

        setLiveData(data);
        setIsApiConnected(true);

        const alertDetected =
          data?.sos_active === true ||
          data?.threat_level === "CRITICAL";

        setIsAlertActive(alertDetected);

        if (alertDetected) {
          showProcessing(1800);
        }
      } catch {
        if (!cancelled) {
          setIsApiConnected(false);
        }
      }
    };

    pollAPI();

    const interval = setInterval(pollAPI, 2000);

    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  // =========================================================
  // ALERT SOUND
  // =========================================================

  const playAlertSound = () => {
    const AudioContext =
      window.AudioContext || window.webkitAudioContext;

    if (!AudioContext) return;

    const audioCtx = new AudioContext();

    const oscillator = audioCtx.createOscillator();
    const gain = audioCtx.createGain();

    oscillator.type = "sawtooth";

    oscillator.frequency.setValueAtTime(
      880,
      audioCtx.currentTime
    );

    oscillator.frequency.exponentialRampToValueAtTime(
      440,
      audioCtx.currentTime + 0.5
    );

    gain.gain.setValueAtTime(
      0.3,
      audioCtx.currentTime
    );

    gain.gain.exponentialRampToValueAtTime(
      0.01,
      audioCtx.currentTime + 0.5
    );

    oscillator.connect(gain);
    gain.connect(audioCtx.destination);

    oscillator.start();
    oscillator.stop(audioCtx.currentTime + 0.5);

    oscillator.onended = () => {
      audioCtx.close();
    };
  };

  useEffect(() => {
    if (!isAlertActive) return;

    const interval = setInterval(playAlertSound, 600);

    return () => clearInterval(interval);
  }, [isAlertActive]);

  // =========================================================
  // ALERT LOGS
  // =========================================================

  const [alertFilter, setAlertFilter] = useState("ALL");

  const [alertLogs, setAlertLogs] = useState([
    {
      id: 1,
      type: "CRITICAL",
      message: "SOS Signal Hand Gesture Detected in Camera #1",
      time: "10:14:02 AM",
    },
    {
      id: 2,
      type: "WARNING",
      message: "Threat Level Elevated: Unattended area movement",
      time: "10:10:15 AM",
    },
    {
      id: 3,
      type: "INFO",
      message: "Backend API connection established",
      time: "10:00:00 AM",
    },
  ]);

  // =========================================================
  // SETTINGS
  // =========================================================

  const [confidence, setConfidence] = useState(75);
  const [telegramEnabled, setTelegramEnabled] = useState(true);
  const [saveToast, setSaveToast] = useState(false);

  // =========================================================
  // TELEGRAM
  // =========================================================

  const [botToken, setBotToken] = useState("");
  const [chatId, setChatId] = useState("");
  const [testStatus, setTestStatus] = useState(null);

  // =========================================================
  // SIMULATE ALERT
  // =========================================================

  const handleSimulateAlert = () => {
    showProcessing(1800);

    const newLog = {
      id: Date.now(),

      type:
        Math.random() > 0.5
          ? "CRITICAL"
          : "WARNING",

      message:
        `Simulated Threat Detected on Zone #${
          Math.floor(Math.random() * 5) + 1
        }`,

      time: new Date().toLocaleTimeString(),
    };

    setAlertLogs((prev) => [newLog, ...prev]);
  };

  // =========================================================
  // SAVE SETTINGS
  // =========================================================

  const handleSaveSettings = () => {
    setSaveToast(true);

    setTimeout(() => {
      setSaveToast(false);
    }, 2500);
  };

  // =========================================================
  // TELEGRAM TEST
  // =========================================================

  const handleSendTestMessage = () => {
    setTestStatus("SENDING");

    showProcessing(1200);

    setTimeout(() => {
      setTestStatus("SUCCESS");

      setTimeout(() => {
        setTestStatus(null);
      }, 3000);
    }, 1200);
  };

  // =========================================================
  // FILTERED LOGS
  // =========================================================

  const filteredLogs = alertLogs.filter((log) => {
    if (alertFilter === "ALL") return true;

    return log.type === alertFilter;
  });

  // =========================================================
  // CSS
  // =========================================================

  const styles = `
    .netra-logo {
      display: inline-flex;
      align-items: baseline;
      transform: perspective(180px) rotateY(-8deg) rotateZ(-1deg);
      letter-spacing: 0.12em;
      text-shadow: 0 2px 12px rgba(6,182,212,.18);
    }

    .welcome-letter {
      display: inline-block;
      position: relative;
      transition:
        transform .28s cubic-bezier(.2,.8,.2,1),
        filter .25s ease;
    }

    .welcome-gradient {
      background: linear-gradient(
        90deg,
        #22d3ee 0%,
        #7dd3fc 35%,
        #818cf8 65%,
        #22d3ee 100%
      );
      background-size: 200% auto;
      background-clip: text;
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      animation: welcomeWave 4s linear infinite;
    }

    .welcome-white {
      color: #ffffff;
      -webkit-text-fill-color: #ffffff;
    }

    @keyframes welcomeWave {
      0% {
        background-position: 0% center;
      }

      100% {
        background-position: 200% center;
      }
    }

    .welcome-letter:hover {
      transform: translateY(-14px) rotate(-3deg) scale(1.08);
      filter: drop-shadow(0 8px 18px rgba(34,211,238,.25));
    }

    .welcome-letter:hover + .welcome-letter {
      transform: translateY(-8px) rotate(2deg) scale(1.04);
    }

    /* =====================================================
       FEATURE CARDS
       ===================================================== */

    .feature-card {
      position: relative;
      isolation: isolate;
      transition:
        transform .35s cubic-bezier(.2,.8,.2,1),
        border-color .35s ease,
        background .35s ease,
        box-shadow .35s ease;
    }

    .feature-card::before {
      content: "";
      position: absolute;
      z-index: -1;
      left: 5%;
      right: 5%;
      bottom: -28px;
      height: 65%;
      border-radius: 50%;
      background: rgba(34,211,238,.30);
      filter: blur(38px);
      opacity: 0;
      transform: scale(.65);
      transition:
        opacity .35s ease,
        transform .35s ease,
        filter .35s ease;
      pointer-events: none;
    }

    .feature-card:nth-child(2)::before {
      background: rgba(129,140,248,.30);
    }

    .feature-card:nth-child(3)::before {
      background: rgba(16,185,129,.28);
    }

    .feature-card:hover {
      transform: translateY(-12px) scale(1.015);
      box-shadow:
        0 22px 50px rgba(0,0,0,.35);
    }

    .feature-card:hover::before {
      opacity: 1;
      transform: scale(1.15);
      filter: blur(34px);
    }

    .feature-card:nth-child(1):hover {
      border-color: rgba(34,211,238,.55);
      box-shadow:
        0 22px 50px rgba(0,0,0,.35),
        0 0 35px rgba(34,211,238,.13);
    }

    .feature-card:nth-child(2):hover {
      border-color: rgba(129,140,248,.55);
      box-shadow:
        0 22px 50px rgba(0,0,0,.35),
        0 0 35px rgba(129,140,248,.13);
    }

    .feature-card:nth-child(3):hover {
      border-color: rgba(16,185,129,.55);
      box-shadow:
        0 22px 50px rgba(0,0,0,.35),
        0 0 35px rgba(16,185,129,.13);
    }

    /* =====================================================
       FEATURE NAME BOXES
       ===================================================== */

    .feature-name-box {
      display: flex;
      align-items: center;
      justify-content: center;
      width: fit-content;
      min-width: 130px;
      margin: 0 auto 16px;
      padding: 8px 18px;
      border-radius: 8px;
      transition:
        transform .3s ease,
        box-shadow .3s ease,
        background .3s ease,
        border-color .3s ease;
    }

    .camera-name-box {
      background: rgba(8,47,73,.75);
      border: 1px solid rgba(34,211,238,.55);
      box-shadow:
        0 0 15px rgba(34,211,238,.08),
        inset 0 0 15px rgba(34,211,238,.04);
    }

    .gesture-name-box {
      background: rgba(49,46,129,.55);
      border: 1px solid rgba(129,140,248,.55);
      box-shadow:
        0 0 15px rgba(129,140,248,.08),
        inset 0 0 15px rgba(129,140,248,.04);
    }

    .alert-name-box {
      background: rgba(6,78,59,.55);
      border: 1px solid rgba(16,185,129,.55);
      box-shadow:
        0 0 15px rgba(16,185,129,.08),
        inset 0 0 15px rgba(16,185,129,.04);
    }

    .feature-card:hover .feature-name-box {
      transform: translateY(-3px);
    }

    .feature-card:nth-child(1):hover .camera-name-box {
      background: rgba(8,47,73,.95);
      box-shadow:
        0 0 22px rgba(34,211,238,.25),
        inset 0 0 18px rgba(34,211,238,.08);
    }

    .feature-card:nth-child(2):hover .gesture-name-box {
      background: rgba(49,46,129,.80);
      box-shadow:
        0 0 22px rgba(129,140,248,.25),
        inset 0 0 18px rgba(129,140,248,.08);
    }

    .feature-card:nth-child(3):hover .alert-name-box {
      background: rgba(6,78,59,.80);
      box-shadow:
        0 0 22px rgba(16,185,129,.25),
        inset 0 0 18px rgba(16,185,129,.08);
    }

    .back-dashboard-btn {
      transition:
        transform .25s ease,
        border-color .25s ease,
        background .25s ease;
    }

    .back-dashboard-btn:hover {
      transform: translateY(-2px);
    }

    /* =====================================================
       NETRA // CINEMATIC UI MOTION PACK
       Pure CSS: no extra dependency, API/camera logic untouched.
       ===================================================== */

    :root {
      --netra-cyan: #22d3ee;
      --netra-blue: #38bdf8;
      --netra-indigo: #818cf8;
      --netra-emerald: #10b981;
      --netra-red: #ef4444;
    }

    * {
      scrollbar-width: thin;
      scrollbar-color: rgba(34,211,238,.45) rgba(2,6,23,.65);
    }

    ::selection {
      background: rgba(34,211,238,.28);
      color: #fff;
    }

    .netra-shell {
      position: relative;
      isolation: isolate;
      overflow-x: hidden;
      background:
        radial-gradient(circle at 12% 8%, rgba(34,211,238,.075), transparent 28%),
        radial-gradient(circle at 88% 18%, rgba(129,140,248,.07), transparent 30%),
        radial-gradient(circle at 50% 100%, rgba(16,185,129,.045), transparent 34%),
        #020617;
    }

    .netra-shell::before {
      content: "";
      position: fixed;
      inset: 0;
      z-index: -3;
      pointer-events: none;
      opacity: .28;
      background-image:
        linear-gradient(rgba(34,211,238,.045) 1px, transparent 1px),
        linear-gradient(90deg, rgba(34,211,238,.045) 1px, transparent 1px);
      background-size: 48px 48px;
      mask-image: linear-gradient(to bottom, black, transparent 92%);
      animation: gridDrift 18s linear infinite;
    }

    .netra-shell::after {
      content: "";
      position: fixed;
      inset: 0;
      z-index: 80;
      pointer-events: none;
      opacity: .055;
      background: repeating-linear-gradient(
        to bottom,
        rgba(255,255,255,.08) 0px,
        rgba(255,255,255,.08) 1px,
        transparent 1px,
        transparent 4px
      );
      mix-blend-mode: overlay;
    }

    @keyframes gridDrift {
      from { background-position: 0 0, 0 0; }
      to { background-position: 48px 48px, 48px 48px; }
    }

    .netra-ambient {
      position: fixed;
      width: 420px;
      height: 420px;
      border-radius: 999px;
      pointer-events: none;
      z-index: -2;
      filter: blur(80px);
      opacity: .14;
      background: #06b6d4;
      top: -160px;
      left: 15%;
      animation: ambientFloat 10s ease-in-out infinite alternate;
    }

    .netra-ambient.two {
      width: 360px;
      height: 360px;
      background: #6366f1;
      left: auto;
      right: -100px;
      top: 38%;
      animation-delay: -4s;
    }

    .netra-ambient.three {
      width: 280px;
      height: 280px;
      background: #10b981;
      left: 12%;
      top: auto;
      bottom: -120px;
      animation-delay: -7s;
    }

    @keyframes ambientFloat {
      0% { transform: translate3d(-20px, 0, 0) scale(.92); }
      100% { transform: translate3d(35px, 48px, 0) scale(1.08); }
    }

    .netra-boot {
      animation: netraBoot .72s cubic-bezier(.16,1,.3,1) both;
    }

    @keyframes netraBoot {
      0% { opacity: 0; transform: translateY(18px) scale(.985); filter: blur(8px); }
      100% { opacity: 1; transform: none; filter: blur(0); }
    }

    .netra-main-content {
      animation: contentReveal .65s cubic-bezier(.16,1,.3,1) both;
    }

    @keyframes contentReveal {
      from { opacity: 0; transform: translateY(10px); }
      to { opacity: 1; transform: none; }
    }

    header {
      position: relative;
      overflow: hidden;
      box-shadow: 0 12px 45px rgba(0,0,0,.18);
    }

    header::after {
      content: "";
      position: absolute;
      left: -20%;
      top: 0;
      width: 40%;
      height: 1px;
      background: linear-gradient(90deg, transparent, rgba(34,211,238,.9), transparent);
      box-shadow: 0 0 18px rgba(34,211,238,.65);
      animation: headerBeam 5s ease-in-out infinite;
    }

    @keyframes headerBeam {
      0%, 15% { left: -25%; opacity: 0; }
      25% { opacity: 1; }
      70% { left: 105%; opacity: 1; }
      80%, 100% { left: 105%; opacity: 0; }
    }

    nav button {
      position: relative;
      overflow: hidden;
      transition: transform .22s ease, color .22s ease, background .22s ease, box-shadow .22s ease !important;
    }

    nav button::before {
      content: "";
      position: absolute;
      inset: 0;
      background: linear-gradient(100deg, transparent, rgba(255,255,255,.08), transparent);
      transform: translateX(-120%);
      transition: transform .5s ease;
    }

    nav button:hover::before { transform: translateX(120%); }
    nav button:hover { transform: translateY(-1px); }

    nav button[class*="bg-slate-800"] {
      box-shadow: inset 0 0 18px rgba(34,211,238,.055), 0 0 18px rgba(34,211,238,.045);
    }

    .feature-card {
      overflow: hidden;
      transform-style: preserve-3d;
      will-change: transform;
    }

    .feature-card::after {
      content: "";
      position: absolute;
      inset: -80% -35%;
      background: linear-gradient(
        115deg,
        transparent 35%,
        rgba(255,255,255,.09) 47%,
        rgba(34,211,238,.12) 50%,
        transparent 58%
      );
      transform: translateX(-55%) rotate(8deg);
      opacity: 0;
      transition: opacity .2s ease, transform .75s cubic-bezier(.16,1,.3,1);
      pointer-events: none;
    }

    .feature-card:hover::after {
      opacity: 1;
      transform: translateX(55%) rotate(8deg);
    }

    .feature-card > * {
      position: relative;
      z-index: 1;
    }

    .feature-card:hover {
      transform: translateY(-12px) scale(1.018);
    }

    .feature-name-box {
      position: relative;
      overflow: hidden;
    }

    .feature-name-box::after {
      content: "";
      position: absolute;
      top: -60%;
      left: -120%;
      width: 70%;
      height: 220%;
      transform: rotate(18deg);
      background: linear-gradient(90deg, transparent, rgba(255,255,255,.16), transparent);
      animation: badgeSweep 4.5s ease-in-out infinite;
      pointer-events: none;
    }

    @keyframes badgeSweep {
      0%, 65% { left: -120%; }
      82% { left: 150%; }
      100% { left: 150%; }
    }

    .netra-hero {
      position: relative;
    }

    .netra-hero::before {
      content: "";
      position: absolute;
      width: 620px;
      height: 220px;
      left: 50%;
      top: 25%;
      transform: translate(-50%, -50%);
      border-radius: 50%;
      background: radial-gradient(ellipse, rgba(34,211,238,.11), transparent 68%);
      filter: blur(18px);
      pointer-events: none;
      animation: heroPulse 4s ease-in-out infinite;
    }

    @keyframes heroPulse {
      0%, 100% { opacity: .55; transform: translate(-50%, -50%) scale(.92); }
      50% { opacity: 1; transform: translate(-50%, -50%) scale(1.08); }
    }

    .welcome-letter {
      will-change: transform, filter;
    }

    .welcome-letter:nth-child(2n) { animation: letterFloat 3.8s ease-in-out infinite; }
    .welcome-letter:nth-child(3n) { animation: letterFloat 4.3s ease-in-out -.8s infinite; }

    @keyframes letterFloat {
      0%, 100% { transform: translateY(0); }
      50% { transform: translateY(-3px); }
    }

    .netra-metric {
      position: relative;
      overflow: hidden;
      box-shadow:
        inset 0 1px 0 rgba(255,255,255,.04),
        0 18px 45px rgba(0,0,0,.22);
    }

    .netra-metric::before {
      content: "";
      position: absolute;
      inset: 0;
      background: linear-gradient(120deg, transparent 20%, rgba(34,211,238,.08), transparent 80%);
      animation: metricSweep 3.5s linear infinite;
      pointer-events: none;
    }

    @keyframes metricSweep {
      from { transform: translateX(-100%); }
      to { transform: translateX(100%); }
    }

    .netra-sos {
      position: relative;
      isolation: isolate;
      overflow: hidden;
      box-shadow: 0 12px 35px rgba(34,211,238,.13);
      transition: transform .22s ease, box-shadow .22s ease, filter .22s ease !important;
    }

    .netra-sos::before {
      content: "";
      position: absolute;
      inset: -2px;
      z-index: -1;
      border-radius: inherit;
      padding: 1px;
      background: linear-gradient(90deg, #22d3ee, #818cf8, #10b981, #22d3ee);
      background-size: 300% 100%;
      animation: borderFlow 4s linear infinite;
      -webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
      -webkit-mask-composite: xor;
      mask-composite: exclude;
    }

    .netra-sos:hover {
      transform: translateY(-3px) scale(1.025);
      box-shadow: 0 18px 45px rgba(34,211,238,.22);
      filter: brightness(1.08);
    }

    @keyframes borderFlow {
      to { background-position: 300% 0; }
    }

    .netra-alert {
      animation: threatEntrance .5s cubic-bezier(.16,1,.3,1) both, threatGlow 1.25s ease-in-out infinite;
      position: relative;
      overflow: hidden;
    }

    .netra-alert::before {
      content: "";
      position: absolute;
      top: 0;
      bottom: 0;
      left: -25%;
      width: 20%;
      background: linear-gradient(90deg, transparent, rgba(255,255,255,.12), transparent);
      transform: skewX(-18deg);
      animation: alertSweep 1.7s linear infinite;
    }

    @keyframes threatEntrance {
      from { opacity: 0; transform: translateY(-12px) scale(.98); }
      to { opacity: 1; transform: none; }
    }

    @keyframes threatGlow {
      0%, 100% { box-shadow: 0 0 0 rgba(239,68,68,0); }
      50% { box-shadow: 0 0 32px rgba(239,68,68,.16); }
    }

    @keyframes alertSweep {
      from { left: -25%; }
      to { left: 125%; }
    }

    .netra-processing {
      background-image: linear-gradient(90deg, transparent, rgba(245,158,11,.12), transparent);
      background-size: 200% 100%;
      animation: processingFlow 1.5s linear infinite;
    }

    @keyframes processingFlow {
      from { background-position: -100% 0; }
      to { background-position: 100% 0; }
    }

    .netra-panel {
      position: relative;
      overflow: hidden;
      box-shadow:
        inset 0 1px 0 rgba(255,255,255,.025),
        0 20px 60px rgba(0,0,0,.16);
      transition: transform .35s ease, border-color .35s ease, box-shadow .35s ease;
    }

    .netra-panel::before {
      content: "";
      position: absolute;
      top: 0;
      left: 8%;
      right: 8%;
      height: 1px;
      background: linear-gradient(90deg, transparent, rgba(34,211,238,.5), transparent);
      opacity: .55;
    }

    .netra-panel:hover {
      transform: translateY(-3px);
      border-color: rgba(34,211,238,.18);
      box-shadow: 0 24px 70px rgba(0,0,0,.22);
    }

    .netra-camera-frame {
      box-shadow:
        inset 0 0 0 1px rgba(34,211,238,.08),
        inset 0 0 50px rgba(0,0,0,.5),
        0 20px 55px rgba(0,0,0,.3);
    }

    .netra-camera-frame::before {
      content: "";
      position: absolute;
      left: 0;
      right: 0;
      height: 2px;
      top: -3px;
      z-index: 10;
      background: linear-gradient(90deg, transparent, rgba(34,211,238,.85), transparent);
      box-shadow: 0 0 16px rgba(34,211,238,.8);
      animation: cameraScan 3s linear infinite;
      pointer-events: none;
    }

    .netra-camera-frame::after {
      content: "● REC   NETRA VISION";
      position: absolute;
      right: 12px;
      top: 10px;
      z-index: 10;
      padding: 4px 8px;
      border: 1px solid rgba(34,211,238,.18);
      border-radius: 6px;
      background: rgba(2,6,23,.72);
      color: rgba(103,232,249,.8);
      font: 9px/1 monospace;
      letter-spacing: .08em;
      backdrop-filter: blur(8px);
      pointer-events: none;
    }

    @keyframes cameraScan {
      0% { top: -3px; opacity: 0; }
      8% { opacity: 1; }
      92% { opacity: 1; }
      100% { top: calc(100% + 3px); opacity: 0; }
    }

    .netra-live-dot {
      box-shadow: 0 0 0 0 rgba(239,68,68,.55);
      animation: liveRing 1.8s infinite;
    }

    @keyframes liveRing {
      0% { box-shadow: 0 0 0 0 rgba(239,68,68,.55); }
      70% { box-shadow: 0 0 0 9px rgba(239,68,68,0); }
      100% { box-shadow: 0 0 0 0 rgba(239,68,68,0); }
    }

    .netra-input {
      transition: border-color .25s ease, box-shadow .25s ease, transform .2s ease !important;
    }

    .netra-input:focus {
      transform: translateY(-1px);
      box-shadow: 0 0 0 3px rgba(34,211,238,.07), 0 10px 30px rgba(0,0,0,.18);
    }

    .netra-log-row {
      animation: logIn .45s cubic-bezier(.16,1,.3,1) both;
      transition: transform .22s ease, filter .22s ease;
    }

    .netra-log-row:hover {
      transform: translateX(5px);
      filter: brightness(1.08);
    }

    @keyframes logIn {
      from { opacity: 0; transform: translateX(-12px); }
      to { opacity: 1; transform: none; }
    }

    .netra-back {
      transition: transform .25s ease, box-shadow .25s ease, border-color .25s ease !important;
    }

    .netra-back:hover {
      transform: translateX(-3px) translateY(-2px) !important;
      box-shadow: 0 12px 30px rgba(34,211,238,.09);
    }

    .netra-status {
      animation: statusIn .45s cubic-bezier(.16,1,.3,1) both;
    }

    @keyframes statusIn {
      from { opacity: 0; transform: scale(.94); }
      to { opacity: 1; transform: scale(1); }
    }

    .netra-status-dot {
      position: relative;
    }

    .netra-status-dot::after {
      content: "";
      position: absolute;
      inset: -5px;
      border-radius: 50%;
      border: 1px solid currentColor;
      opacity: .3;
      animation: statusPing 1.8s infinite;
    }

    @keyframes statusPing {
      0% { transform: scale(.65); opacity: .45; }
      80%, 100% { transform: scale(1.45); opacity: 0; }
    }

    .netra-footer {
      position: relative;
    }

    .netra-footer::before {
      content: "";
      position: absolute;
      top: 0;
      left: 15%;
      right: 15%;
      height: 1px;
      background: linear-gradient(90deg, transparent, rgba(34,211,238,.25), transparent);
    }

    .netra-reduced-motion *,
    .netra-reduced-motion *::before,
    .netra-reduced-motion *::after {
      animation-duration: .001ms !important;
      animation-iteration-count: 1 !important;
      scroll-behavior: auto !important;
      transition-duration: .001ms !important;
    }

    @media (prefers-reduced-motion: reduce) {
      .netra-shell *,
      .netra-shell *::before,
      .netra-shell *::after {
        animation-duration: .001ms !important;
        animation-iteration-count: 1 !important;
        scroll-behavior: auto !important;
      }
    }

    @media (max-width: 640px) {
      .netra-ambient { opacity: .08; }
      .netra-shell::before { background-size: 34px 34px; }
      .netra-hero::before { width: 360px; }
    }
    /* =====================================================
       NETRA // UI UX PRO MAX — MOTION OVERDRIVE
       High-intensity cinematic layer.
       ===================================================== */

    :root {
      --netra-mx: 0;
      --netra-my: 0;
      --netra-cursor-x: 50%;
      --netra-cursor-y: 50%;
    }

    .netra-shell {
      --parallax-x: calc(var(--netra-mx) * 10px);
      --parallax-y: calc(var(--netra-my) * 8px);
    }

    .netra-cursor-aura {
      position: fixed;
      z-index: -1;
      left: var(--netra-cursor-x);
      top: var(--netra-cursor-y);
      width: 280px;
      height: 280px;
      transform: translate(-50%, -50%);
      border-radius: 999px;
      pointer-events: none;
      background: radial-gradient(circle, rgba(34,211,238,.14), rgba(34,211,238,.035) 30%, transparent 70%);
      filter: blur(8px);
      mix-blend-mode: screen;
      transition: left .18s ease-out, top .18s ease-out;
    }

    .netra-corner {
      position: fixed;
      width: 86px;
      height: 86px;
      z-index: 75;
      pointer-events: none;
      opacity: .28;
      filter: drop-shadow(0 0 8px rgba(34,211,238,.35));
    }
    .netra-corner-tl { left: 16px; top: 16px; border-left: 1px solid rgba(34,211,238,.8); border-top: 1px solid rgba(34,211,238,.8); }
    .netra-corner-tr { right: 16px; top: 16px; border-right: 1px solid rgba(34,211,238,.8); border-top: 1px solid rgba(34,211,238,.8); }
    .netra-corner-bl { left: 16px; bottom: 16px; border-left: 1px solid rgba(34,211,238,.8); border-bottom: 1px solid rgba(34,211,238,.8); }
    .netra-corner-br { right: 16px; bottom: 16px; border-right: 1px solid rgba(34,211,238,.8); border-bottom: 1px solid rgba(34,211,238,.8); }
    .netra-corner::after {
      content: ""; position: absolute; width: 28px; height: 1px; background: var(--netra-cyan);
      box-shadow: 0 0 12px var(--netra-cyan); animation: hudCornerPulse 2.5s ease-in-out infinite;
    }
    .netra-corner-tl::after { left: 8px; top: 8px; transform-origin: left; }
    .netra-corner-tr::after { right: 8px; top: 8px; transform-origin: right; }
    .netra-corner-bl::after { left: 8px; bottom: 8px; transform-origin: left; }
    .netra-corner-br::after { right: 8px; bottom: 8px; transform-origin: right; }
    @keyframes hudCornerPulse { 0%,100% { transform: scaleX(.35); opacity: .2; } 50% { transform: scaleX(1); opacity: 1; } }

    .netra-hud-line {
      position: fixed; z-index: 74; pointer-events: none; height: 1px;
      background: linear-gradient(90deg, transparent, rgba(34,211,238,.65), transparent);
      box-shadow: 0 0 12px rgba(34,211,238,.35); opacity: .18;
    }
    .netra-hud-line-a { width: 34vw; left: 3vw; top: 18%; animation: hudRailA 8s ease-in-out infinite; }
    .netra-hud-line-b { width: 26vw; right: 4vw; bottom: 19%; animation: hudRailB 10s ease-in-out infinite; }
    @keyframes hudRailA { 0%,100% { transform: translateX(-30%); opacity: .06; } 50% { transform: translateX(20%); opacity: .35; } }
    @keyframes hudRailB { 0%,100% { transform: translateX(25%); opacity: .05; } 50% { transform: translateX(-20%); opacity: .3; } }

    .netra-particle-field { position: fixed; inset: 0; z-index: -1; pointer-events: none; overflow: hidden; opacity: .7; }
    .netra-particle-field span {
      position: absolute; width: 2px; height: 2px; left: calc((var(--i) * 17) % 100 * 1%); top: calc((var(--i) * 29) % 100 * 1%);
      border-radius: 50%; background: rgba(103,232,249,.8); box-shadow: 0 0 10px rgba(34,211,238,.7);
      animation: particleFloat calc(5s + (var(--i) % 5) * 1.2s) ease-in-out infinite alternate; animation-delay: calc(var(--i) * -.55s);
    }
    @keyframes particleFloat {
      0% { transform: translate3d(calc(var(--netra-mx) * -8px), 12px, 0) scale(.6); opacity: .1; }
      50% { opacity: .85; }
      100% { transform: translate3d(calc(var(--netra-mx) * 14px), -42px, 0) scale(1.4); opacity: .15; }
    }

    .netra-radar {
      position: fixed; width: 190px; height: 190px; right: 22px; bottom: 26px; z-index: 10; pointer-events: none; opacity: .11;
      transform: translate3d(var(--parallax-x), var(--parallax-y), 0); transition: transform .25s ease-out;
    }
    .netra-radar::before {
      content: ""; position: absolute; inset: 0; border-radius: 50%;
      background: repeating-radial-gradient(circle, transparent 0 25px, rgba(34,211,238,.55) 26px 27px);
      mask-image: radial-gradient(circle, black 0 50%, transparent 72%);
    }
    .netra-radar::after { content: ""; position: absolute; inset: 50% 0 auto; height: 1px; background: linear-gradient(90deg, transparent, rgba(34,211,238,.7), transparent); }
    .netra-radar-ring { position: absolute; inset: 50%; border: 1px solid rgba(34,211,238,.45); border-radius: 50%; transform: translate(-50%,-50%); animation: radarRing 3.8s ease-out infinite; }
    .netra-radar-ring.ring-1 { width: 34px; height: 34px; }
    .netra-radar-ring.ring-2 { width: 88px; height: 88px; animation-delay: -1.2s; }
    .netra-radar-ring.ring-3 { width: 150px; height: 150px; animation-delay: -2.4s; }
    @keyframes radarRing { 0%,100% { opacity: .08; transform: translate(-50%,-50%) scale(.86); } 45% { opacity: .55; } 70% { opacity: .1; transform: translate(-50%,-50%) scale(1.04); } }
    .netra-radar-sweep { position: absolute; left: 50%; top: 50%; width: 88px; height: 1px; transform-origin: left center; background: linear-gradient(90deg, rgba(34,211,238,.95), transparent); box-shadow: 0 0 12px rgba(34,211,238,.8); animation: radarSweep 3.2s linear infinite; }
    @keyframes radarSweep { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

    .netra-panel {
      position: relative; overflow: hidden;
      transform: translate3d(calc(var(--netra-mx) * -1.5px), calc(var(--netra-my) * -1px), 0);
      transition: transform .28s ease-out, border-color .3s ease, box-shadow .3s ease;
    }
    .netra-panel::before {
      content: ""; position: absolute; inset: 0; pointer-events: none;
      background: radial-gradient(circle at var(--netra-cursor-x) var(--netra-cursor-y), rgba(34,211,238,.10), transparent 32%);
      opacity: 0; transition: opacity .35s ease;
    }
    .netra-panel:hover::before { opacity: 1; }
    .netra-panel::after {
      content: ""; position: absolute; left: -30%; top: 0; width: 18%; height: 100%; transform: skewX(-18deg);
      background: linear-gradient(90deg, transparent, rgba(255,255,255,.06), transparent); animation: panelSweep 7s ease-in-out infinite; pointer-events: none;
    }
    @keyframes panelSweep { 0%,70% { left:-30%; opacity:0; } 78% { opacity:1; } 92% { left:125%; opacity:0; } 100% { left:125%; opacity:0; } }

    .netra-metric { position: relative; overflow: hidden; animation: metricBreath 3.4s ease-in-out infinite; }
    .netra-metric::after {
      content: ""; position: absolute; left: -120%; top: 0; width: 60%; height: 100%; transform: skewX(-20deg);
      background: linear-gradient(90deg, transparent, rgba(34,211,238,.12), transparent); animation: metricSweep 4.2s ease-in-out infinite;
    }
    @keyframes metricBreath { 0%,100% { box-shadow: inset 0 0 25px rgba(34,211,238,.03), 0 0 15px rgba(34,211,238,.02); } 50% { box-shadow: inset 0 0 30px rgba(34,211,238,.09), 0 0 30px rgba(34,211,238,.07); } }
    @keyframes metricSweep { 0%,55% { left:-120%; } 80% { left:150%; } 100% { left:150%; } }

    .netra-shell button:active { transform: scale(.96) !important; transition-duration: .08s !important; }
    .netra-shell input, .netra-shell textarea, .netra-shell select { transition: border-color .25s ease, box-shadow .25s ease, transform .25s ease, background .25s ease; }
    .netra-shell input:focus, .netra-shell textarea:focus, .netra-shell select:focus { transform: translateY(-1px); box-shadow: 0 0 0 1px rgba(34,211,238,.15), 0 0 22px rgba(34,211,238,.08); }

    @media (max-width: 768px) { .netra-corner, .netra-hud-line, .netra-radar { display:none; } .netra-cursor-aura { width:180px; height:180px; } }
    @media (prefers-reduced-motion: reduce) {
      *, *::before, *::after { animation-duration:.01ms !important; animation-iteration-count:1 !important; scroll-behavior:auto !important; transition-duration:.01ms !important; }
      .netra-cursor-aura, .netra-radar, .netra-particle-field { display:none !important; }
    }



    /* =====================================================
       NETRA // APEX COMMAND CENTER EXTENSION
       High-end motion + interaction layer
       ===================================================== */
    .netra-apex-orbit { position:fixed; width:320px; height:320px; right:-105px; top:22%; border:1px solid rgba(34,211,238,.13); border-radius:50%; pointer-events:none; z-index:1; animation: apexOrbit 18s linear infinite; }
    .netra-apex-orbit::before,.netra-apex-orbit::after{content:"";position:absolute;inset:26px;border:1px dashed rgba(129,140,248,.16);border-radius:50%;}
    .netra-apex-orbit::after{inset:78px;border-style:solid;border-color:rgba(16,185,129,.16);animation:apexSpin 9s linear infinite reverse;}
    @keyframes apexOrbit{to{transform:rotate(360deg)}}
    @keyframes apexSpin{to{transform:rotate(-360deg)}}
    .netra-telemetry-rail{position:fixed;left:18px;bottom:22px;z-index:70;width:220px;padding:10px 12px;border:1px solid rgba(34,211,238,.18);background:rgba(2,6,23,.72);backdrop-filter:blur(14px);border-radius:14px;box-shadow:0 0 30px rgba(34,211,238,.06),inset 0 0 20px rgba(34,211,238,.025);pointer-events:none;}
    .netra-telemetry-title{font:700 9px/1 ui-monospace,SFMono-Regular,Menlo,monospace;letter-spacing:.18em;color:#67e8f9;display:flex;justify-content:space-between;margin-bottom:8px;}
    .netra-telemetry-bars{height:24px;display:flex;align-items:flex-end;gap:3px;overflow:hidden;}
    .netra-telemetry-bars i{display:block;width:3px;border-radius:4px 4px 0 0;background:linear-gradient(to top,#06b6d4,#818cf8);animation:telemetryPulse .7s ease-in-out infinite alternate;opacity:.8;}
    .netra-telemetry-bars i:nth-child(2n){animation-delay:-.25s}.netra-telemetry-bars i:nth-child(3n){animation-delay:-.45s}.netra-telemetry-bars i:nth-child(4n){animation-delay:-.1s}
    @keyframes telemetryPulse{from{height:4px;opacity:.35}to{height:23px;opacity:1}}
    .netra-command-chip{position:relative;overflow:hidden;isolation:isolate;}
    .netra-command-chip::after{content:"";position:absolute;top:0;bottom:0;left:-70%;width:45%;background:linear-gradient(90deg,transparent,rgba(255,255,255,.22),transparent);transform:skewX(-20deg);animation:commandSweep 3.2s ease-in-out infinite;pointer-events:none;}
    @keyframes commandSweep{0%,55%{left:-70%}100%{left:135%}}
    .netra-hud-corners{position:absolute;inset:0;pointer-events:none;border-radius:inherit;overflow:hidden;}
    .netra-hud-corners::before,.netra-hud-corners::after{content:"";position:absolute;width:34px;height:34px;border-color:rgba(34,211,238,.7);border-style:solid;filter:drop-shadow(0 0 7px rgba(34,211,238,.45));}
    .netra-hud-corners::before{left:10px;top:10px;border-width:2px 0 0 2px}.netra-hud-corners::after{right:10px;bottom:10px;border-width:0 2px 2px 0;}
    .netra-apex-panel{position:relative;overflow:hidden;transform:translateZ(0);}
    .netra-apex-panel::before{content:"";position:absolute;inset:-2px;background:conic-gradient(from 0deg,transparent 0 55%,rgba(34,211,238,.28),transparent 70%);animation:apexBorderSpin 5s linear infinite;z-index:-1;}
    .netra-apex-panel::after{content:"";position:absolute;left:-20%;right:-20%;height:1px;top:0;background:linear-gradient(90deg,transparent,#22d3ee,transparent);box-shadow:0 0 18px #22d3ee;animation:apexScan 3.8s ease-in-out infinite;pointer-events:none;}
    @keyframes apexBorderSpin{to{transform:rotate(360deg)}}
    @keyframes apexScan{0%,100%{top:2% ;opacity:0}15%{opacity:1}80%{top:98%;opacity:.7}}
    .netra-metric-live{animation:metricBreathe 2.4s ease-in-out infinite;}
    @keyframes metricBreathe{0%,100%{box-shadow:0 0 0 rgba(34,211,238,0)}50%{box-shadow:0 0 32px rgba(34,211,238,.13),inset 0 0 22px rgba(34,211,238,.04)}}
    .netra-danger-pulse{animation:dangerPulse 1.25s ease-in-out infinite;}
    @keyframes dangerPulse{0%,100%{box-shadow:0 0 10px rgba(239,68,68,.08)}50%{box-shadow:0 0 42px rgba(239,68,68,.3),inset 0 0 25px rgba(239,68,68,.08)}}
    .netra-page-enter{animation:apexPage .72s cubic-bezier(.16,1,.3,1) both;}
    @keyframes apexPage{from{opacity:0;transform:translateY(18px) scale(.985);filter:blur(8px)}to{opacity:1;transform:none;filter:none}}
    .netra-hover-3d{transition:transform .45s cubic-bezier(.2,.8,.2,1),box-shadow .45s ease;transform-style:preserve-3d;}
    .netra-hover-3d:hover{transform:perspective(900px) rotateX(2deg) rotateY(-2deg) translateY(-8px);}
    .netra-kicker{font:700 9px/1 ui-monospace,SFMono-Regular,Menlo,monospace;letter-spacing:.22em;text-transform:uppercase;color:rgba(148,163,184,.7);}
    .netra-data-dot{width:5px;height:5px;border-radius:50%;background:#22d3ee;box-shadow:0 0 10px #22d3ee;animation:dataBlink 1.4s infinite;}
    @keyframes dataBlink{0%,100%{opacity:.25;transform:scale(.7)}50%{opacity:1;transform:scale(1.2)}}
    @media(max-width:768px){.netra-apex-orbit,.netra-telemetry-rail{display:none}.netra-hover-3d:hover{transform:translateY(-4px)}}

  `;


  // =========================================================
  // RENDER
  // =========================================================

  return (
    <div className={`min-h-screen text-slate-100 font-sans flex flex-col netra-shell ${booted ? "netra-boot" : ""}`}>
      <div className="netra-ambient" />
      <div className="netra-ambient two" />
      <div className="netra-ambient three" />
      <div className="netra-cursor-aura" />
      <div className="netra-corner netra-corner-tl" />
      <div className="netra-corner netra-corner-tr" />
      <div className="netra-corner netra-corner-bl" />
      <div className="netra-corner netra-corner-br" />
      <div className="netra-hud-line netra-hud-line-a" />
      <div className="netra-hud-line netra-hud-line-b" />
      <div className="netra-particle-field" aria-hidden="true">
        {Array.from({ length: 18 }).map((_, index) => (
          <span
            key={index}
            style={{
              "--i": index,
              left: `${(index * 17) % 100}%`,
              top: `${(index * 29) % 100}%`,
              width: `${1 + (index % 3)}px`,
              height: `${1 + (index % 3)}px`,
              animationDuration: `${5 + (index % 5) * 1.2}s`,
              animationDelay: `${index * -0.55}s`,
            }}
          />
        ))}
      </div>
      <div className="netra-radar" aria-hidden="true">
        <span className="netra-radar-ring ring-1" />
        <span className="netra-radar-ring ring-2" />
        <span className="netra-radar-ring ring-3" />
        <span className="netra-radar-sweep" />
      </div>

      <style>{styles}</style>

      {/* APEX COMMAND-CENTER AMBIENCE */}
      <div className="netra-apex-orbit" aria-hidden="true" />
      <div className="pointer-events-none fixed inset-0 z-[2] overflow-hidden" aria-hidden="true">
        <div className="absolute left-[7%] top-[34%] w-px h-28 bg-gradient-to-b from-transparent via-cyan-400/30 to-transparent animate-pulse" />
        <div className="absolute right-[8%] top-[55%] w-32 h-px bg-gradient-to-r from-transparent via-indigo-400/25 to-transparent" />
        <div className="absolute left-[35%] top-[12%] w-44 h-px bg-gradient-to-r from-transparent via-cyan-400/20 to-transparent animate-pulse" />
      </div>

      <div className="netra-telemetry-rail hidden sm:block">
        <div className="netra-telemetry-title"><span>LIVE TELEMETRY</span><span className="text-emerald-400">● SYNC</span></div>
        <div className="netra-telemetry-bars" aria-hidden="true">
          {Array.from({ length: 42 }, (_, i) => <i key={i} style={{height:`${6 + ((i * 17) % 18)}px`}} />)}
        </div>
        <div className="mt-2 flex justify-between font-mono text-[8px] text-slate-600"><span>VISION CORE</span><span>NEURAL LINK // ACTIVE</span></div>
      </div>

      {/* ALERT OVERLAY */}

      {isAlertActive && (
        <div className="fixed inset-0 bg-red-600/20 pointer-events-none animate-pulse z-50 border-8 border-red-600" />
      )}

      {/* HEADER */}

      <header className="border-b border-slate-800/80 bg-slate-900/60 backdrop-blur-md sticky top-0 z-40 px-6 py-3.5 flex items-center justify-between">

        <div
          className="flex items-center gap-3 cursor-pointer"
          onClick={() => setActivePage("dashboard")}
        >

          

          <div
          className="flex items-center gap-3 cursor-pointer"
          onClick={() => setActivePage("dashboard")}
        >
          {/* Aryan ka purana logo delete karke ye line daal di */}
          <NetraHeaderLogo />
        </div>

        </div>

        {/* NAV */}

        <nav className="hidden md:flex items-center gap-1 bg-slate-950/60 p-1 rounded-lg border border-slate-800/60 text-xs font-medium text-slate-400">

          {[
            ["dashboard", "Dashboard"],
            ["alerts", "Alerts"],
            ["livefeed", "Live Feed"],
            ["settings", "Settings"],
          ].map(([page, label]) => (

            <button
              key={page}
              onClick={() => setActivePage(page)}
              className={`px-3.5 py-1.5 rounded-md transition-all ${
                activePage === page
                  ? "text-white bg-slate-800 border border-slate-700"
                  : "hover:text-white hover:bg-slate-800/50"
              }`}
            >
              {label}
            </button>

          ))}

        </nav>

        {/* STATUS */}

        <div className="flex items-center gap-3">

          <div className="hidden sm:block text-right font-mono text-xs text-slate-400">
            {currentTime}
          </div>

          {isProcessing && (
            <div className="flex items-center gap-2 bg-amber-950/50 border border-amber-700/50 px-3 py-1.5 rounded-full text-xs">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-500 animate-pulse" />
              <span className="text-amber-300 font-mono text-[11px]">
                Processing...
              </span>
            </div>
          )}

          <div
            className={`flex items-center gap-2 border px-3 py-1.5 rounded-full text-xs ${
              isApiConnected
                ? "bg-emerald-950/40 border-emerald-700/40"
                : "bg-red-950/40 border-red-700/40"
            }`}
          >

            <span
              className={`w-2.5 h-2.5 rounded-full ${
                isApiConnected
                  ? "bg-emerald-500 animate-pulse"
                  : "bg-red-500"
              }`}
            />

            <span
              className={`font-mono text-[11px] ${
                isApiConnected
                  ? "text-emerald-400"
                  : "text-red-400"
              }`}
            >
              API: {isApiConnected ? "Connected" : "Disconnected"}
            </span>

          </div>

        </div>

      </header>

      {/* MAIN */}

      <main className="max-w-7xl mx-auto px-6 py-10 flex-grow w-full netra-main-content netra-page-enter">

        {/* PROCESSING */}

        {isProcessing && (
          <div className="mb-6 p-3.5 bg-amber-950/40 border border-amber-700/50 rounded-xl flex items-center gap-3 netra-processing">

            <span className="w-3 h-3 rounded-full bg-amber-500 animate-pulse" />

            <span className="text-amber-300 font-mono text-xs font-semibold">
              Processing...
            </span>

            <span className="text-amber-400/70 text-xs">
              Processing alert information.
            </span>

          </div>
        )}

        {/* EMERGENCY */}

        {isAlertActive && (
          <div className="mb-8 p-4 bg-red-950/60 border border-red-600/50 rounded-xl flex items-center justify-between netra-alert netra-danger-pulse">

            <div>

              <h3 className="font-bold text-red-200 text-sm">
                EMERGENCY THREAT DETECTED
              </h3>

              <p className="text-xs text-red-300/80 font-mono">
                SOS gesture or high threat signal received.
              </p>

            </div>

            <button
              onClick={() => {
                setIsAlertActive(false);
                setIsProcessing(false);
              }}
              className="px-3 py-1.5 bg-red-900/50 hover:bg-red-800 border border-red-700 text-red-200 rounded-lg text-xs font-mono"
            >
              DISMISS
            </button>

          </div>
        )}

        {/* DASHBOARD */}

        {activePage === "dashboard" && (
          <div>

            <div className="text-center my-10 max-w-4xl mx-auto netra-hero">

              <div className="inline-block mb-5 px-4 py-1.5 bg-cyan-950/60 border border-cyan-800/50 rounded-full">

                <span className="text-xs font-mono text-cyan-400">
                  AI-Powered Safety System
                </span>

              </div>

              {/* =================================================
                  WELCOME TO NETRA
                  "WELCOME TO" = WHITE
                  "NETRA" = ORIGINAL GRADIENT + WAVE
                 ================================================= */}

              <h1 className="text-5xl sm:text-7xl lg:text-8xl font-extrabold tracking-tight mb-7">

                {"Welcome to ".split("").map(
                  (letter, index) => (

                    <span
                      key={`white-${index}`}
                      className="welcome-letter welcome-white"
                    >
                      {letter === " " ? "\u00A0" : letter}
                    </span>

                  )
                )}

                {"Netra".split("").map(
                  (letter, index) => (

                    <span
                      key={`gradient-${index}`}
                      className="welcome-letter welcome-gradient"
                    >
                      {letter}
                    </span>

                  )
                )}

              </h1>

              <p className="text-slate-300 text-base sm:text-lg leading-relaxed mb-8 max-w-2xl mx-auto">
                Real-time threat detection & SOS alert system using AI vision and gesture recognition.
              </p>

              {/* PERSON COUNT */}

              <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-xl text-center mb-4 max-w-xs mx-auto netra-metric netra-metric-live netra-apex-panel netra-hover-3d">

                <div className="text-slate-400 text-xs font-mono uppercase mb-1">
                  Persons Detected
                </div>

                <div className="text-3xl font-extrabold text-cyan-400 font-mono">
                  {liveData?.persons_detected ?? 0}
                </div>

              </div>

              {/* SOS */}

              <button
                onClick={() => {
                  const nextState = !isAlertActive;

                  setIsAlertActive(nextState);

                  if (nextState) {
                    showProcessing(1800);
                  } else {
                    setIsProcessing(false);
                  }
                }}
                className={`netra-sos netra-command-chip px-6 py-3 rounded-xl font-medium text-sm ${
                  isAlertActive
                    ? "bg-red-600 hover:bg-red-700 text-white"
                    : "bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold"
                }`}
              >
                {isAlertActive
                  ? "Reset Emergency Alert"
                  : "Trigger Manual SOS Test"}
              </button>

            </div>

            {/* FEATURES */}

            <div className="grid grid-cols-1 md:grid-cols-3 gap-7 mt-16">

              {/* CAMERA CARD */}

              <div
                onClick={() => setActivePage("yolo_detail")}
                className="feature-card netra-apex-panel netra-hover-3d bg-slate-900/40 border border-slate-800 p-8 rounded-2xl min-h-[250px] flex flex-col justify-center hover:bg-slate-900/80 cursor-pointer"
              >

                <div className="feature-name-box camera-name-box">

                  <span className="text-cyan-300 text-base font-bold font-mono">
                    Camera
                  </span>

                </div>

                <p className="text-slate-400 text-sm leading-relaxed mb-6 text-center">
                  DroidCam live camera with YOLO person and gender detection.
                </p>

                <span className="text-cyan-400 text-sm font-mono text-center">
                  Open Detection Studio →
                </span>

              </div>

              {/* GESTURE CARD */}

              <div
                onClick={() => setActivePage("gesture_detail")}
                className="feature-card netra-apex-panel netra-hover-3d bg-slate-900/40 border border-slate-800 p-8 rounded-2xl min-h-[250px] flex flex-col justify-center hover:bg-slate-900/80 cursor-pointer"
              >

                <div className="feature-name-box gesture-name-box">

                  <span className="text-indigo-300 text-base font-bold font-mono">
                    Gesture
                  </span>

                </div>

                <p className="text-slate-400 text-sm leading-relaxed mb-6 text-center">
                  MediaPipe powered pose estimation for emergency gesture detection.
                </p>

                <span className="text-indigo-400 text-sm font-mono text-center">
                  View Gesture Analyzer →
                </span>

              </div>

              {/* ALERT CARD */}

              <div
                onClick={() => setActivePage("alerts_detail")}
                className="feature-card netra-apex-panel netra-hover-3d bg-slate-900/40 border border-slate-800 p-8 rounded-2xl min-h-[250px] flex flex-col justify-center hover:bg-slate-900/80 cursor-pointer"
              >

                <div className="feature-name-box alert-name-box">

                  <span className="text-emerald-300 text-base font-bold font-mono">
                    Alerts
                  </span>

                </div>

                <p className="text-slate-400 text-sm leading-relaxed mb-6 text-center">
                  Automatic Telegram and cloud alerts when a threat is detected.
                </p>

                <span className="text-emerald-400 text-sm font-mono text-center">
                  Configure Webhooks →
                </span>

              </div>

            </div>

          </div>
        )}

        {/* ALERTS */}

        {activePage === "alerts" && (
          <div className="space-y-6">

            <div className="text-center">

              <h2 className="text-2xl font-bold text-white">
                System Threat & Emergency Logs
              </h2>

              <p className="text-slate-400 text-xs mt-1">
                Real-time alert logs.
              </p>

              <div className="flex justify-center gap-2 mt-4">

                <button
                  onClick={handleSimulateAlert}
                  className="px-3.5 py-1.5 bg-cyan-950 hover:bg-cyan-900 border border-cyan-800 text-cyan-300 rounded-lg text-xs font-mono"
                >
                  Simulate Alert
                </button>

                <button
                  onClick={() => setAlertLogs([])}
                  className="px-3 py-1.5 bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-400 rounded-lg text-xs font-mono"
                >
                  Clear Logs
                </button>

              </div>

            </div>

            <div className="flex justify-center gap-2 border-b border-slate-800 pb-3 text-xs font-mono">

              {["ALL", "CRITICAL", "WARNING"].map(
                (filter) => (

                  <button
                    key={filter}
                    onClick={() => setAlertFilter(filter)}
                    className={`px-3 py-1 rounded-md ${
                      alertFilter === filter
                        ? "bg-slate-800 text-cyan-400 border border-cyan-500/30"
                        : "text-slate-400 hover:text-white"
                    }`}
                  >
                    {filter} (
                    {filter === "ALL"
                      ? alertLogs.length
                      : alertLogs.filter(
                          (l) => l.type === filter
                        ).length}
                    )
                  </button>

                )
              )}

            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 netra-panel font-mono text-xs space-y-3 netra-panel">

              {filteredLogs.length === 0 ? (

                <div className="text-center py-12 text-slate-500">
                  No logs available.
                </div>

              ) : (

                filteredLogs.map((log) => (

                  <div
                    key={log.id}
                    className={`netra-log-row p-3.5 border rounded-xl flex justify-between items-center ${
                      log.type === "CRITICAL"
                        ? "bg-red-950/40 border-red-800/50 text-red-300"
                        : log.type === "WARNING"
                          ? "bg-amber-950/40 border-amber-800/50 text-amber-300"
                          : "bg-slate-950 border-slate-800 text-slate-400"
                    }`}
                  >

                    <div className="flex items-center gap-2.5">

                      <span className="font-bold text-[10px] px-2 py-0.5 rounded bg-black/40 border border-white/10">
                        [{log.type}]
                      </span>

                      <span>{log.message}</span>

                    </div>

                    <span className="text-slate-500 text-[11px]">
                      {log.time}
                    </span>

                  </div>

                ))

              )}

            </div>

          </div>
        )}

        {/* LIVE FEED / DROIDCAM */}

        {activePage === "livefeed" && (
          <div className="space-y-6">

            <div className="text-center">

              <h2 className="text-2xl font-bold text-white">
                Live Vision Stream
              </h2>

              <p className="text-slate-500 text-xs mt-1">
                DroidCam integration for NETRA vision pipeline
              </p>

            </div>

            {/* DROIDCAM INFO */}

            <div className="bg-cyan-950/30 border border-cyan-800/50 rounded-2xl p-5 netra-panel">

              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">

                <div>

                  <h3 className="text-cyan-400 font-bold text-sm font-mono">
                    DROIDCAM CONNECTION
                  </h3>

                  <p className="text-slate-400 text-xs mt-1">
                    Phone IP: 192.168.1.2
                  </p>

                  <p className="text-slate-400 text-xs font-mono">
                    Port: 4747
                  </p>

                </div>

                <div className="text-right">

                  <p className="text-slate-500 text-[10px] font-mono">
                    DROIDCAM SERVER
                  </p>

                  <p className="text-cyan-300 text-xs font-mono">
                    {DROIDCAM_URL}
                  </p>

                </div>

              </div>

            </div>

            {/* CONNECTION PANEL */}

            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 netra-panel">

              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">

                {/* CAMERA 1 */}

                <div>

                  <label className="block text-slate-400 mb-1.5 text-[11px] font-mono">
                    DroidCam Camera #1
                  </label>

                  <input
                    type="text"
                    value={camera1Url}
                    onChange={(e) =>
                      handleCamera1UrlChange(e.target.value)
                    }
                    placeholder="http://192.168.1.2:4747/video"
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 netra-input text-cyan-300 placeholder:text-slate-600 focus:outline-none focus:border-cyan-500 font-mono text-xs"
                  />

                  <button
                    onClick={connectCamera1}
                    disabled={camera1Connecting}
                    className="w-full mt-3 px-5 py-2.5 bg-cyan-500 hover:bg-cyan-400 disabled:bg-slate-700 disabled:text-slate-500 text-slate-950 font-bold rounded-xl text-xs"
                  >
                    {camera1Connecting
                      ? "Connecting DroidCam..."
                      : camera1Online
                        ? "Reconnect DroidCam"
                        : "Connect DroidCam"}
                  </button>

                </div>

                {/* CAMERA 2 */}

                <div>

                  <label className="block text-slate-400 mb-1.5 text-[11px] font-mono">
                    Optional Camera #2
                  </label>

                  <input
                    type="text"
                    value={camera2Url}
                    onChange={(e) =>
                      handleCamera2UrlChange(e.target.value)
                    }
                    placeholder="http://192.168.1.X:8080/video"
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 netra-input text-indigo-300 placeholder:text-slate-600 focus:outline-none focus:border-indigo-500 font-mono text-xs"
                  />

                  <button
                    onClick={connectCamera2}
                    disabled={
                      camera2Connecting ||
                      !camera2Url.trim()
                    }
                    className="w-full mt-3 px-5 py-2.5 bg-indigo-500 hover:bg-indigo-400 disabled:bg-slate-700 disabled:text-slate-500 text-white font-bold rounded-xl text-xs"
                  >
                    {camera2Connecting
                      ? "Connecting..."
                      : camera2Online
                        ? "Reconnect Camera #2"
                        : "Connect Camera #2"}
                  </button>

                </div>

              </div>

              {/* STATUS */}

              <div className="text-center mt-5">

                {cameraSyncStatus && (
                  <span
                    className={`text-[11px] font-mono ${
                      cameraSyncStatus.type === "SUCCESS"
                        ? "text-emerald-400"
                        : cameraSyncStatus.type === "INFO"
                          ? "text-cyan-400"
                          : "text-red-400"
                    }`}
                  >
                    {cameraSyncStatus.message}
                  </span>
                )}

              </div>

            </div>

            {/* CAMERA GRID */}

            <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">

              {/* CAMERA 1 */}

              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 netra-panel">

                <div className="flex items-center justify-between mb-4">

                  <div>

                    <h3 className="text-white font-bold text-sm">
                      DroidCam #1
                    </h3>

                    <p className="text-slate-500 text-[11px] font-mono break-all">
                      {camera1Url}
                    </p>

                  </div>

                  <div
                    className={`flex items-center gap-2 px-3 py-1.5 rounded-full ${
                      camera1Online
                        ? "bg-emerald-950/50 border border-emerald-700/40"
                        : "bg-red-950/50 border border-red-700/40"
                    }`}
                  >

                    <span
                      className={`w-2.5 h-2.5 rounded-full ${
                        camera1Online
                          ? "bg-emerald-500 animate-pulse"
                          : "bg-red-500"
                      }`}
                    />

                    <span
                      className={`text-[11px] font-mono ${
                        camera1Online
                          ? "text-emerald-400"
                          : "text-red-400"
                      }`}
                    >
                      {camera1Online
                        ? "LIVE"
                        : camera1Connecting
                          ? "CONNECTING"
                          : "OFFLINE"}
                    </span>

                  </div>

                </div>

                <div className="relative w-full aspect-video bg-black rounded-xl overflow-hidden border border-slate-800 netra-camera-frame">

                  {camera1Url && camera1Refresh > 0 ? (

                    <img
                      key={`droidcam-${camera1Refresh}`}
                      src={AI_RAW_FEED_URL}
                      alt="DroidCam Live Feed"
                      className="w-full h-full object-contain"
                      onLoad={handleCamera1Load}
                      onError={handleCamera1Error}
                    />

                  ) : (

                    <div className="absolute inset-0 flex flex-col items-center justify-center">

                      <div className="w-16 h-16 rounded-full bg-cyan-950 border border-cyan-800 flex items-center justify-center mb-4">

                        <span className="text-cyan-400 text-2xl">
                          📷
                        </span>

                      </div>

                      <div className="text-slate-300 font-mono text-sm">
                        DROIDCAM READY
                      </div>

                      <div className="text-slate-500 text-[11px] mt-1">
                        Click Connect DroidCam
                      </div>

                    </div>

                  )}

                  {camera1Connecting && (

                    <div className="absolute inset-0 flex flex-col items-center justify-center bg-slate-950/75 backdrop-blur-sm">

                      <div className="w-10 h-10 rounded-full border-4 border-cyan-500/30 border-t-cyan-400 animate-spin mb-4" />

                      <div className="text-cyan-400 font-mono text-xs font-bold">
                        CONNECTING DROIDCAM...
                      </div>

                      <div className="text-slate-500 text-[10px] font-mono mt-2">
                        192.168.1.2:4747
                      </div>

                    </div>

                  )}

                  {camera1Url &&
                    camera1Refresh > 0 &&
                    !camera1Online &&
                    !camera1Connecting && (

                      <div className="absolute inset-0 flex flex-col items-center justify-center bg-slate-950/80">

                        <div className="w-14 h-14 rounded-full bg-red-950 border border-red-800 flex items-center justify-center mb-4">

                          <span className="text-red-500 text-2xl">
                            !
                          </span>

                        </div>

                        <div className="text-red-400 font-mono text-sm font-bold">
                          DROIDCAM OFFLINE
                        </div>

                        <div className="text-slate-500 text-[11px] mt-2 text-center px-5">
                          Check phone Wi-Fi and DroidCam app.
                        </div>

                        <button
                          onClick={connectCamera1}
                          className="mt-3 px-4 py-1.5 bg-cyan-500 hover:bg-cyan-400 text-slate-950 rounded-lg text-[11px] font-bold"
                        >
                          Reconnect
                        </button>

                      </div>

                    )}

                  {camera1Online && (

                    <div className="absolute top-3 left-3 flex items-center gap-2 bg-black/70 px-3 py-1.5 rounded-lg">

                      <span className="w-2.5 h-2.5 rounded-full bg-red-500 animate-pulse netra-live-dot" />

                      <span className="text-red-400 text-[11px] font-mono font-bold">
                        LIVE
                      </span>

                    </div>

                  )}

                  <div className="absolute bottom-3 left-3 bg-black/70 px-3 py-1.5 rounded-lg">

                    <span className="text-slate-300 text-[11px] font-mono">
                      NETRA-DROIDCAM-01
                    </span>

                  </div>

                </div>

                <div className="grid grid-cols-3 gap-3 mt-4">

                  <div className="bg-slate-950 border border-slate-800 rounded-xl p-3 text-center">

                    <div className="text-slate-500 text-[10px] font-mono">
                      DEVICE
                    </div>

                    <div className="text-cyan-400 text-xs font-mono mt-1">
                      DroidCam
                    </div>

                  </div>

                  <div className="bg-slate-950 border border-slate-800 rounded-xl p-3 text-center">

                    <div className="text-slate-500 text-[10px] font-mono">
                      PORT
                    </div>

                    <div className="text-cyan-400 text-xs font-mono mt-1">
                      4747
                    </div>

                  </div>

                  <div className="bg-slate-950 border border-slate-800 rounded-xl p-3 text-center">

                    <div className="text-slate-500 text-[10px] font-mono">
                      STATUS
                    </div>

                    <div
                      className={`text-xs font-mono mt-1 ${
                        camera1Online
                          ? "text-emerald-400"
                          : "text-red-400"
                      }`}
                    >
                      {camera1Online
                        ? "Connected"
                        : "Offline"}
                    </div>

                  </div>

                </div>

              </div>

              {/* CAMERA 2 */}

              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 netra-panel">

                <div className="flex items-center justify-between mb-4">

                  <div>

                    <h3 className="text-white font-bold text-sm">
                      Camera #2
                    </h3>

                    <p className="text-slate-500 text-[11px] font-mono break-all">
                      {camera2Url || "Not configured"}
                    </p>

                  </div>

                  <div
                    className={`flex items-center gap-2 px-3 py-1.5 rounded-full ${
                      camera2Online
                        ? "bg-emerald-950/50 border border-emerald-700/40"
                        : "bg-red-950/50 border border-red-700/40"
                    }`}
                  >

                    <span
                      className={`w-2.5 h-2.5 rounded-full ${
                        camera2Online
                          ? "bg-emerald-500 animate-pulse"
                          : "bg-red-500"
                      }`}
                    />

                    <span
                      className={`text-[11px] font-mono ${
                        camera2Online
                          ? "text-emerald-400"
                          : "text-red-400"
                      }`}
                    >
                      {camera2Online
                        ? "LIVE"
                        : camera2Connecting
                          ? "CONNECTING"
                          : "OFFLINE"}
                    </span>

                  </div>

                </div>

                <div className="relative w-full aspect-video bg-black rounded-xl overflow-hidden border border-slate-800 netra-camera-frame">

                  {camera2Url && camera2Refresh > 0 ? (

                    <img
                      key={`camera2-${camera2Refresh}`}
                      src={camera2Url}
                      alt="Camera 2 Live Feed"
                      className="w-full h-full object-contain"
                      onLoad={handleCamera2Load}
                      onError={handleCamera2Error}
                    />

                  ) : (

                    <div className="absolute inset-0 flex flex-col items-center justify-center">

                      <div className="w-16 h-16 rounded-full bg-slate-900 border border-slate-700 flex items-center justify-center mb-4">

                        <span className="text-slate-500 text-2xl">
                          📷
                        </span>

                      </div>

                      <div className="text-slate-400 font-mono text-sm">
                        CAMERA #2
                      </div>

                      <div className="text-slate-600 text-[11px] mt-1">
                        Optional camera
                      </div>

                    </div>

                  )}

                  {camera2Connecting && (

                    <div className="absolute inset-0 flex flex-col items-center justify-center bg-slate-950/75">

                      <div className="w-10 h-10 rounded-full border-4 border-indigo-500/30 border-t-indigo-400 animate-spin mb-4" />

                      <div className="text-indigo-400 font-mono text-xs">
                        CONNECTING...
                      </div>

                    </div>

                  )}

                </div>

                {/* CAMERA 2 DEVICE / PORT / STATUS */}

                <div className="grid grid-cols-3 gap-3 mt-4">

                  <div className="bg-slate-950 border border-slate-800 rounded-xl p-3 text-center">

                    <div className="text-slate-500 text-[10px] font-mono">
                      DEVICE
                    </div>

                    <div className="text-indigo-400 text-xs font-mono mt-1">
                      Camera #2
                    </div>

                  </div>

                  <div className="bg-slate-950 border border-slate-800 rounded-xl p-3 text-center">

                    <div className="text-slate-500 text-[10px] font-mono">
                      PORT
                    </div>

                    <div className="text-indigo-400 text-xs font-mono mt-1">
                      {camera2Url
                        ? (() => {
                            try {
                              return new URL(camera2Url).port || "N/A";
                            } catch {
                              return "N/A";
                            }
                          })()
                        : "N/A"}
                    </div>

                  </div>

                  <div className="bg-slate-950 border border-slate-800 rounded-xl p-3 text-center">

                    <div className="text-slate-500 text-[10px] font-mono">
                      STATUS
                    </div>

                    <div
                      className={`text-xs font-mono mt-1 ${
                        camera2Online
                          ? "text-emerald-400"
                          : "text-red-400"
                      }`}
                    >
                      {camera2Online
                        ? "Connected"
                        : "Offline"}
                    </div>

                  </div>

                </div>

              </div>

            </div>

            {/* AI PROCESSED FEED - FIX: this whole panel was missing in this
                version. It shows the engine's actual output (YOLO boxes +
                pose skeleton drawn on top of Camera #1's frames). */}

            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 netra-panel">

              <div className="flex items-center justify-between mb-4">

                <div>

                  <h3 className="text-white font-bold text-sm">
                    AI Processed Feed
                  </h3>

                  <p className="text-slate-500 text-[11px] font-mono break-all">
                    YOLO + pose detection on Camera #1
                  </p>

                </div>

                <div
                  className={`flex items-center gap-2 px-3 py-1.5 rounded-full ${
                    camera1Online && isApiConnected
                      ? "bg-emerald-950/50 border border-emerald-700/40"
                      : "bg-red-950/50 border border-red-700/40"
                  }`}
                >

                  <span
                    className={`w-2.5 h-2.5 rounded-full ${
                      camera1Online && isApiConnected
                        ? "bg-emerald-500 animate-pulse"
                        : "bg-red-500"
                    }`}
                  />

                  <span
                    className={`text-[11px] font-mono ${
                      camera1Online && isApiConnected
                        ? "text-emerald-400"
                        : "text-red-400"
                    }`}
                  >
                    {camera1Online && isApiConnected
                      ? "PROCESSING"
                      : camera1Connecting
                        ? "CONNECTING"
                        : "OFFLINE"}
                  </span>

                </div>

              </div>

              <div className="relative w-full aspect-video bg-black rounded-xl overflow-hidden border border-slate-800 netra-camera-frame">

                {camera1Refresh > 0 ? (

                  <img
                    key={`ai-feed-${camera1Refresh}`}
                    src={AI_LIVE_FEED_URL}
                    alt="AI Processed Feed"
                    className="w-full h-full object-contain"
                  />

                ) : (

                  <div className="absolute inset-0 flex flex-col items-center justify-center">

                    <div className="w-16 h-16 rounded-full bg-slate-900 border border-slate-700 flex items-center justify-center mb-4">

                      <span className="text-slate-500 text-2xl">
                        🧠
                      </span>

                    </div>

                    <div className="text-slate-400 font-mono text-sm">
                      AI FEED
                    </div>

                    <div className="text-slate-600 text-[11px] mt-1">
                      Connect Camera #1 to start processing
                    </div>

                  </div>

                )}

              </div>

              <div className="grid grid-cols-3 gap-3 mt-4">

                <div className="bg-slate-950 border border-slate-800 rounded-xl p-3 text-center">

                  <div className="text-slate-500 text-[10px] font-mono">
                    ENGINE
                  </div>

                  <div className="text-indigo-400 text-xs font-mono mt-1">
                    YOLOv8-Pose
                  </div>

                </div>

                <div className="bg-slate-950 border border-slate-800 rounded-xl p-3 text-center">

                  <div className="text-slate-500 text-[10px] font-mono">
                    PORT
                  </div>

                  <div className="text-indigo-400 text-xs font-mono mt-1">
                    8001
                  </div>

                </div>

                <div className="bg-slate-950 border border-slate-800 rounded-xl p-3 text-center">

                  <div className="text-slate-500 text-[10px] font-mono">
                    STATUS
                  </div>

                  <div
                    className={`text-xs font-mono mt-1 ${
                      camera1Online && isApiConnected
                        ? "text-emerald-400"
                        : "text-red-400"
                    }`}
                  >
                    {camera1Online && isApiConnected
                      ? "Processing"
                      : "Offline"}
                  </div>

                </div>

              </div>

            </div>

          </div>
        )}

        {/* SETTINGS */}

        {activePage === "settings" && (

          <div className="space-y-6 max-w-2xl mx-auto">

            <div className="text-center">

              <h2 className="text-2xl font-bold text-white">
                System Configuration
              </h2>

              <p className="text-slate-400 text-xs">
                Adjust AI thresholds and notification preferences.
              </p>

              {saveToast && (

                <div className="mt-3">

                  <span className="text-xs bg-emerald-950 border border-emerald-700 text-emerald-400 px-3 py-1 rounded-lg">
                    Settings Saved!
                  </span>

                </div>

              )}

            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 netra-panel space-y-6">

              <div className="p-4 bg-slate-950 rounded-xl border border-slate-800">

                <div className="flex justify-between items-center">

                  <div>

                    <div className="font-semibold text-white">
                      YOLO Confidence
                    </div>

                    <div className="text-slate-400 text-[11px]">
                      Minimum detection confidence
                    </div>

                  </div>

                  <span className="font-mono text-cyan-400 bg-cyan-950 px-2.5 py-1 rounded">
                    {confidence}%
                  </span>

                </div>

                <input
                  type="range"
                  min="50"
                  max="95"
                  value={confidence}
                  onChange={(e) =>
                    setConfidence(Number(e.target.value))
                  }
                  className="w-full accent-cyan-500 mt-4"
                />

              </div>

              <div className="flex justify-between items-center p-4 bg-slate-950 rounded-xl border border-slate-800">

                <div>

                  <div className="font-semibold text-white">
                    Telegram Alert Dispatcher
                  </div>

                  <div className="text-slate-400 text-[11px]">
                    Forward emergency alerts to Telegram.
                  </div>

                </div>

                <button
                  onClick={() =>
                    setTelegramEnabled(!telegramEnabled)
                  }
                  className={`w-12 h-6 flex items-center rounded-full p-1 ${
                    telegramEnabled
                      ? "bg-emerald-600 justify-end"
                      : "bg-slate-800 justify-start"
                  }`}
                >

                  <span className="w-4 h-4 rounded-full bg-white" />

                </button>

              </div>

              <div className="flex justify-end">

                <button
                  onClick={handleSaveSettings}
                  className="px-5 py-2.5 bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold rounded-xl text-xs"
                >
                  Save Changes
                </button>

              </div>

            </div>

          </div>

        )}

        {/* YOLO DETAIL */}

        {activePage === "yolo_detail" && (

          <div className="space-y-6 relative min-h-[520px]">

            <h2 className="text-2xl font-bold text-white text-center">
              YOLO Real-Time Detection Model
            </h2>

            <div className="grid md:grid-cols-2 gap-6">

              <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl netra-panel">

                <h3 className="text-sm font-bold text-cyan-400 mb-3 text-center">
                  Model Specifications
                </h3>

                <ul className="text-xs text-slate-300 space-y-2 font-mono">

                  <li>• YOLOv8 / YOLOv11</li>
                  <li>• Person Detection</li>
                  <li>• Gender Classification</li>
                  <li>• Threat Object Detection</li>
                  <li>• Real-Time Processing</li>

                </ul>

              </div>

              <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl netra-panel">

                <h3 className="text-sm font-bold text-emerald-400 mb-3 text-center">
                  Pipeline
                </h3>

                <div className="text-xs text-slate-300 font-mono text-center space-y-3">

                  <div>DroidCam</div>
                  <div>↓</div>
                  <div>Video Stream</div>
                  <div>↓</div>
                  <div>YOLO Detection</div>
                  <div>↓</div>
                  <div>NETRA Backend</div>

                </div>

              </div>

            </div>

            <button
              onClick={() => setActivePage("dashboard")}
              className="back-dashboard-btn netra-back absolute bottom-0 right-0 px-5 py-2.5 bg-slate-900 hover:bg-cyan-950 border border-slate-700 hover:border-cyan-500 text-cyan-400 rounded-xl text-xs font-mono"
            >
              ← Back to Dashboard
            </button>

          </div>

        )}

        {/* GESTURE DETAIL */}

        {activePage === "gesture_detail" && (

          <div className="space-y-6 relative min-h-[520px]">

            <h2 className="text-2xl font-bold text-white text-center">
              MediaPipe SOS Gesture Tracker
            </h2>

            <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl netra-panel font-mono text-xs text-slate-300 space-y-4">

              <div className="text-indigo-400 font-bold text-center">
                [KEYPOINT LANDMARKS ACTIVE]
              </div>

              <p className="text-center">
                MediaPipe can track hand and body landmarks for SOS gesture recognition.
              </p>

              <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl text-emerald-400 text-center">
                Trigger Gesture: Raised Hand / Open Palm SOS
              </div>

            </div>

            <button
              onClick={() => setActivePage("dashboard")}
              className="back-dashboard-btn netra-back absolute bottom-0 right-0 px-5 py-2.5 bg-slate-900 hover:bg-indigo-950 border border-slate-700 hover:border-indigo-500 text-indigo-400 rounded-xl text-xs font-mono"
            >
              ← Back to Dashboard
            </button>

          </div>

        )}

        {/* ALERT DETAIL */}

        {activePage === "alerts_detail" && (

          <div className="space-y-6 max-w-3xl mx-auto relative min-h-[520px]">

            <h2 className="text-2xl font-bold text-white text-center">
              Telegram & Webhook Dispatcher
            </h2>

            <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl netra-panel space-y-5 text-xs">

              <p className="text-slate-300 text-center">
                Configure Telegram Bot details for emergency notifications.
              </p>

              <div className="space-y-4 font-mono">

                <div>

                  <label className="block text-slate-400 mb-1.5">
                    Telegram Bot Token
                  </label>

                  <input
                    type="password"
                    value={botToken}
                    onChange={(e) =>
                      setBotToken(e.target.value)
                    }
                    placeholder="Enter bot token"
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 netra-input text-cyan-300 focus:outline-none focus:border-cyan-500"
                  />

                </div>

                <div>

                  <label className="block text-slate-400 mb-1.5">
                    Target Chat / Group ID
                  </label>

                  <input
                    type="text"
                    value={chatId}
                    onChange={(e) =>
                      setChatId(e.target.value)
                    }
                    placeholder="-100xxxxxxxxxx"
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 netra-input text-cyan-300 focus:outline-none focus:border-cyan-500"
                  />

                </div>

              </div>

              <div className="flex items-center justify-between">

                <button
                  onClick={handleSendTestMessage}
                  disabled={testStatus === "SENDING"}
                  className="px-5 py-2.5 bg-emerald-500 hover:bg-emerald-400 disabled:bg-slate-800 text-slate-950 font-bold rounded-xl text-xs"
                >
                  {testStatus === "SENDING"
                    ? "Processing..."
                    : "Send Test Notification"}
                </button>

                {testStatus === "SUCCESS" && (

                  <span className="text-emerald-400 font-mono text-xs">
                    Test notification simulated successfully.
                  </span>

                )}

              </div>

            </div>

            <button
              onClick={() => setActivePage("dashboard")}
              className="back-dashboard-btn netra-back absolute bottom-0 right-0 px-5 py-2.5 bg-slate-900 hover:bg-emerald-950 border border-slate-700 hover:border-emerald-500 text-emerald-400 rounded-xl text-xs font-mono"
            >
              ← Back to Dashboard
            </button>

          </div>

        )}

      </main>
      <div className="netra-footer"><NetraFooter /></div>

    </div>
  );
}

export default App;