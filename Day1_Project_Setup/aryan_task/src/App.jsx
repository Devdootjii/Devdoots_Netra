import React, { useEffect, useRef, useState } from "react";

function App() {
  // =========================================================
  // API
  // =========================================================

  const API_URL = "http://127.0.0.1:8000/api/ai-stream";

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

    /* =====================================================
       WELCOME TEXT WAVE - SAME ANIMATION
       ===================================================== */

    .welcome-letter {
      display: inline-block;
      position: relative;
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
      transition:
        transform .28s cubic-bezier(.2,.8,.2,1),
        filter .25s ease;
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

    /*
      Soft light behind card.
      Normally hidden.
      Cursor aate hi halki glow dikhegi.
    */

    .feature-card::before {
      content: "";
      position: absolute;
      z-index: -1;
      left: 10%;
      right: 10%;
      bottom: -18px;
      height: 55%;
      border-radius: 50%;
      background: rgba(34,211,238,.18);
      filter: blur(35px);
      opacity: 0;
      transform: scale(.8);
      transition:
        opacity .35s ease,
        transform .35s ease,
        filter .35s ease;
      pointer-events: none;
    }

    .feature-card:nth-child(2)::before {
      background: rgba(129,140,248,.18);
    }

    .feature-card:nth-child(3)::before {
      background: rgba(16,185,129,.16);
    }

    .feature-card:hover {
      transform: translateY(-10px);
      box-shadow:
        0 18px 45px rgba(0,0,0,.25);
    }

    .feature-card:hover::before {
      opacity: 1;
      transform: scale(1);
      filter: blur(32px);
    }

    .feature-card:nth-child(1):hover {
      border-color: rgba(34,211,238,.35);
    }

    .feature-card:nth-child(2):hover {
      border-color: rgba(129,140,248,.35);
    }

    .feature-card:nth-child(3):hover {
      border-color: rgba(16,185,129,.35);
    }

    .feature-name-box {
      display: flex;
      align-items: center;
      justify-content: center;
      width: fit-content;
      min-width: 130px;
      margin: 0 auto 16px;
      padding: 8px 18px;
      border-radius: 8px;
      background: rgba(15,23,42,.9);
      border: 1px solid rgba(71,85,105,.7);
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
  `;

  // =========================================================
  // RENDER
  // =========================================================

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans">

      <style>{styles}</style>

      {/* =====================================================
          ALERT OVERLAY
      ===================================================== */}

      {isAlertActive && (
        <div className="fixed inset-0 bg-red-600/20 pointer-events-none animate-pulse z-50 border-8 border-red-600" />
      )}

      {/* =====================================================
          HEADER
      ===================================================== */}

      <header className="border-b border-slate-800/80 bg-slate-900/60 backdrop-blur-md sticky top-0 z-40 px-6 py-3.5 flex items-center justify-between">

        <div
          className="flex items-center gap-3 cursor-pointer"
          onClick={() => setActivePage("dashboard")}
        >

          <div className="w-9 h-9 rounded-full bg-cyan-950 border border-cyan-500/40 flex items-center justify-center shadow-lg shadow-cyan-500/20">
            <span className="text-cyan-400 font-black">N</span>
          </div>

          <h1 className="font-black font-mono netra-logo text-cyan-400">
            <span className="text-2xl">N</span>
            <span className="text-xl">ETR</span>
            <span className="text-2xl">A</span>
          </h1>

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

      {/* =====================================================
          MAIN
      ===================================================== */}

      <main className="max-w-7xl mx-auto px-6 py-10">

        {/* PROCESSING */}

        {isProcessing && (
          <div className="mb-6 p-3.5 bg-amber-950/40 border border-amber-700/50 rounded-xl flex items-center gap-3">

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
          <div className="mb-8 p-4 bg-red-950/60 border border-red-600/50 rounded-xl flex items-center justify-between">

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

        {/* =====================================================
            DASHBOARD
        ===================================================== */}

        {activePage === "dashboard" && (
          <div>

            <div className="text-center my-10 max-w-4xl mx-auto">

              <div className="inline-block mb-5 px-4 py-1.5 bg-cyan-950/60 border border-cyan-800/50 rounded-full">

                <span className="text-xs font-mono text-cyan-400">
                  AI-Powered Safety System
                </span>

              </div>

              <h1 className="text-5xl sm:text-7xl lg:text-8xl font-extrabold tracking-tight mb-7">

                {"Welcome to Netra".split("").map(
                  (letter, index) => (

                    <span
                      key={index}
                      className="welcome-letter"
                    >
                      {letter === " " ? "\u00A0" : letter}
                    </span>

                  )
                )}

              </h1>

              <p className="text-slate-300 text-base sm:text-lg leading-relaxed mb-8 max-w-2xl mx-auto">
                Real-time threat detection & SOS alert system using AI vision and gesture recognition.
              </p>

              {/* PERSON COUNT */}

              <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-xl text-center mb-4 max-w-xs mx-auto">

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
                className={`px-6 py-3 rounded-xl font-medium text-sm ${
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
                className="feature-card bg-slate-900/40 border border-slate-800 p-8 rounded-2xl min-h-[250px] flex flex-col justify-center hover:bg-slate-900/80 cursor-pointer"
              >

                <div className="feature-name-box border-cyan-800/50">

                  <span className="text-cyan-400 text-base font-bold font-mono">
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
                className="feature-card bg-slate-900/40 border border-slate-800 p-8 rounded-2xl min-h-[250px] flex flex-col justify-center hover:bg-slate-900/80 cursor-pointer"
              >

                <div className="feature-name-box border-indigo-800/50">

                  <span className="text-indigo-400 text-base font-bold font-mono">
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
                className="feature-card bg-slate-900/40 border border-slate-800 p-8 rounded-2xl min-h-[250px] flex flex-col justify-center hover:bg-slate-900/80 cursor-pointer"
              >

                <div className="feature-name-box border-emerald-800/50">

                  <span className="text-emerald-400 text-base font-bold font-mono">
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

        {/* =====================================================
            ALERTS
        ===================================================== */}

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

            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 font-mono text-xs space-y-3">

              {filteredLogs.length === 0 ? (

                <div className="text-center py-12 text-slate-500">
                  No logs available.
                </div>

              ) : (

                filteredLogs.map((log) => (

                  <div
                    key={log.id}
                    className={`p-3.5 border rounded-xl flex justify-between items-center ${
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

        {/* =====================================================
            LIVE FEED / DROIDCAM
        ===================================================== */}

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

            <div className="bg-cyan-950/30 border border-cyan-800/50 rounded-2xl p-5">

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

            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">

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
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-cyan-300 placeholder:text-slate-600 focus:outline-none focus:border-cyan-500 font-mono text-xs"
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
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-indigo-300 placeholder:text-slate-600 focus:outline-none focus:border-indigo-500 font-mono text-xs"
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

              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">

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

                <div className="relative w-full aspect-video bg-black rounded-xl overflow-hidden border border-slate-800">

                  {camera1Url && camera1Refresh > 0 ? (

                    <img
                      key={`droidcam-${camera1Refresh}`}
                      src={camera1Url}
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

                      <span className="w-2.5 h-2.5 rounded-full bg-red-500 animate-pulse" />

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

              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">

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

                <div className="relative w-full aspect-video bg-black rounded-xl overflow-hidden border border-slate-800">

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

              </div>

            </div>

          </div>
        )}

        {/* =====================================================
            SETTINGS
        ===================================================== */}

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

            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-6">

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

        {/* =====================================================
            YOLO DETAIL
        ===================================================== */}

        {activePage === "yolo_detail" && (

          <div className="space-y-6 relative min-h-[520px]">

            <h2 className="text-2xl font-bold text-white text-center">
              YOLO Real-Time Detection Model
            </h2>

            <div className="grid md:grid-cols-2 gap-6">

              <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl">

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

              <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl">

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
              className="back-dashboard-btn absolute bottom-0 right-0 px-5 py-2.5 bg-slate-900 hover:bg-cyan-950 border border-slate-700 hover:border-cyan-500 text-cyan-400 rounded-xl text-xs font-mono"
            >
              ← Back to Dashboard
            </button>

          </div>

        )}

        {/* =====================================================
            GESTURE DETAIL
        ===================================================== */}

        {activePage === "gesture_detail" && (

          <div className="space-y-6 relative min-h-[520px]">

            <h2 className="text-2xl font-bold text-white text-center">
              MediaPipe SOS Gesture Tracker
            </h2>

            <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl font-mono text-xs text-slate-300 space-y-4">

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
              className="back-dashboard-btn absolute bottom-0 right-0 px-5 py-2.5 bg-slate-900 hover:bg-indigo-950 border border-slate-700 hover:border-indigo-500 text-indigo-400 rounded-xl text-xs font-mono"
            >
              ← Back to Dashboard
            </button>

          </div>

        )}

        {/* =====================================================
            ALERT DETAIL
        ===================================================== */}

        {activePage === "alerts_detail" && (

          <div className="space-y-6 max-w-3xl mx-auto relative min-h-[520px]">

            <h2 className="text-2xl font-bold text-white text-center">
              Telegram & Webhook Dispatcher
            </h2>

            <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl space-y-5 text-xs">

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
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-cyan-300 focus:outline-none focus:border-cyan-500"
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
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-cyan-300 focus:outline-none focus:border-cyan-500"
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
              className="back-dashboard-btn absolute bottom-0 right-0 px-5 py-2.5 bg-slate-900 hover:bg-emerald-950 border border-slate-700 hover:border-emerald-500 text-emerald-400 rounded-xl text-xs font-mono"
            >
              ← Back to Dashboard
            </button>

          </div>

        )}

      </main>

    </div>
  );
}

export default App;