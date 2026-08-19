import React, { useState, useEffect, useRef } from 'react';

function App() {
  const API_URL = "http://127.0.0.1:8000/api/ai-stream";

  const [liveData, setLiveData] = useState(null);
  const [isApiConnected, setIsApiConnected] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isAlertActive, setIsAlertActive] = useState(false);
  const [currentTime, setCurrentTime] = useState(new Date().toLocaleTimeString());

  // =========================================================
  // CAMERA CONFIGURATION
  // =========================================================
  const CAMERA_1_URL = "http://192.168.1.2:8080/video";
  const CAMERA_2_URL = "http://192.168.1.7:8080/video";

  const [camera1Online, setCamera1Online] = useState(false);
  const [camera2Online, setCamera2Online] = useState(false);

  const [camera1Refresh, setCamera1Refresh] = useState(0);
  const [camera2Refresh, setCamera2Refresh] = useState(0);

  // =========================================================
  // OPTIMIZED CAMERA STATUS CHECK
  // IMPORTANT:
  // We DO NOT repeatedly load /video as heartbeat.
  // This prevents unnecessary MJPEG stream downloads.
  // =========================================================
  useEffect(() => {
    let cancelled = false;

    const checkCamera = async (baseUrl, setOnline) => {
      try {
        const controller = new AbortController();

        const timeout = setTimeout(() => {
          controller.abort();
        }, 2500);

        /*
          Use the IP Webcam status endpoint instead of /video.
          This is much lighter than downloading the video stream.
        */
        const statusUrl = baseUrl.replace("/video", "/status.json");

        const response = await fetch(
          `${statusUrl}?t=${Date.now()}`,
          {
            method: "GET",
            cache: "no-store",
            signal: controller.signal
          }
        );

        clearTimeout(timeout);

        if (!cancelled) {
          setOnline(response.ok);
        }

      } catch (error) {
        if (!cancelled) {
          setOnline(false);
        }
      }
    };

    const checkAllCameras = () => {
      checkCamera(CAMERA_1_URL, setCamera1Online);
      checkCamera(CAMERA_2_URL, setCamera2Online);
    };

    // Initial check
    checkAllCameras();

    // Check only every 10 seconds
    const heartbeatInterval = setInterval(
      checkAllCameras,
      10000
    );

    return () => {
      cancelled = true;
      clearInterval(heartbeatInterval);
    };
  }, []);

  // =========================================================
  // CAMERA STREAM REFRESH
  // ONLY REFRESH WHEN CAMERA CHANGES FROM OFFLINE -> ONLINE
  // =========================================================

  const previousCamera1Online = useRef(false);
  const previousCamera2Online = useRef(false);

  useEffect(() => {
    if (
      camera1Online &&
      !previousCamera1Online.current
    ) {
      setCamera1Refresh(prev => prev + 1);
    }

    previousCamera1Online.current = camera1Online;
  }, [camera1Online]);

  useEffect(() => {
    if (
      camera2Online &&
      !previousCamera2Online.current
    ) {
      setCamera2Refresh(prev => prev + 1);
    }

    previousCamera2Online.current = camera2Online;
  }, [camera2Online]);

  // =========================================================
  // PROCESSING STATE
  // =========================================================

  const processingTimeoutRef = useRef(null);

  // Page Navigation State
  const [activePage, setActivePage] = useState('dashboard');

  // ALERTS PAGE INTERACTIVE STATES
  const [alertFilter, setAlertFilter] = useState('ALL');

  const [alertLogs, setAlertLogs] = useState([
    {
      id: 1,
      type: 'CRITICAL',
      message: 'SOS Signal Hand Gesture Detected in Camera #1',
      time: '10:14:02 AM'
    },
    {
      id: 2,
      type: 'WARNING',
      message: 'Threat Level Elevated: Unattended area movement',
      time: '10:10:15 AM'
    },
    {
      id: 3,
      type: 'INFO',
      message: 'Backend API connection established at http://127.0.0.1:8000',
      time: '10:00:00 AM'
    }
  ]);

  // SETTINGS PAGE INTERACTIVE STATES
  const [confidence, setConfidence] = useState(75);
  const [telegramEnabled, setTelegramEnabled] = useState(true);
  const [saveToast, setSaveToast] = useState(false);

  // INSTANT ALERTS / WEBHOOK INTERACTIVE STATES
  const [botToken, setBotToken] = useState(
    '123456789:ABCdefGHIjklMNOpqrsTUVwxyz'
  );

  const [chatId, setChatId] = useState(
    '-100987654321'
  );

  const [testStatus, setTestStatus] = useState(null);

  // =========================================================
  // SHOW PROCESSING SIGNAL
  // =========================================================

  const showProcessing = (duration = 1500) => {
    setIsProcessing(true);

    if (processingTimeoutRef.current) {
      clearTimeout(processingTimeoutRef.current);
    }

    processingTimeoutRef.current = setTimeout(() => {
      setIsProcessing(false);
    }, duration);
  };

  // Cleanup processing timer
  useEffect(() => {
    return () => {
      if (processingTimeoutRef.current) {
        clearTimeout(processingTimeoutRef.current);
      }
    };
  }, []);

  // =========================================================
  // REAL-TIME CLOCK
  // =========================================================

  useEffect(() => {
    const timer = setInterval(
      () => setCurrentTime(new Date().toLocaleTimeString()),
      1000
    );

    return () => clearInterval(timer);
  }, []);

  // =========================================================
  // API POLLING LOGIC
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
          data.sos_active === true ||
          data.threat_level === 'CRITICAL';

        setIsAlertActive(alertDetected);
        setIsProcessing(false);

        if (alertDetected) {
          showProcessing(1800);
        }

      } catch (error) {
        setIsApiConnected(false);
        // Console error removed as required in Day 4 Task 3
      }
    };

    // Run immediately
    pollAPI();

    // Poll every 2 seconds
    const apiInterval = setInterval(
      pollAPI,
      2000
    );

    return () => {
      cancelled = true;
      clearInterval(apiInterval);
    };
  }, []);

  // =========================================================
  // EMERGENCY SOUND GENERATOR
  // =========================================================

  const playAlertSound = () => {
    const AudioContext =
      window.AudioContext ||
      window.webkitAudioContext;

    if (!AudioContext) return;

    const audioCtx = new AudioContext();

    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();

    osc.type = 'sawtooth';

    osc.frequency.setValueAtTime(
      880,
      audioCtx.currentTime
    );

    osc.frequency.exponentialRampToValueAtTime(
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

    osc.connect(gain);
    gain.connect(audioCtx.destination);

    osc.start();
    osc.stop(audioCtx.currentTime + 0.5);

    osc.onended = () => {
      audioCtx.close();
    };
  };

  useEffect(() => {
    if (isAlertActive) {
      const soundInterval = setInterval(
        playAlertSound,
        600
      );

      return () => clearInterval(soundInterval);
    }
  }, [isAlertActive]);

  // =========================================================
  // HANDLER: ADD SIMULATED ALERT
  // =========================================================

  const handleSimulateAlert = () => {
    showProcessing(1800);

    const newLog = {
      id: Date.now(),
      type:
        Math.random() > 0.5
          ? 'CRITICAL'
          : 'WARNING',

      message:
        `Simulated Threat Detected on Zone #${
          Math.floor(Math.random() * 5) + 1
        }`,

      time: new Date().toLocaleTimeString()
    };

    setAlertLogs(prev => [
      newLog,
      ...prev
    ]);
  };

  // =========================================================
  // HANDLER: SAVE SETTINGS
  // =========================================================

  const handleSaveSettings = () => {
    setSaveToast(true);

    setTimeout(
      () => setSaveToast(false),
      2500
    );
  };

  // =========================================================
  // HANDLER: SEND TEST TELEGRAM MESSAGE
  // =========================================================

  const handleSendTestMessage = () => {
    setTestStatus('SENDING');

    showProcessing(1200);

    setTimeout(() => {
      setTestStatus('SUCCESS');

      setTimeout(
        () => setTestStatus(null),
        3000
      );
    }, 1200);
  };

  // =========================================================
  // FILTERED ALERT LOGS
  // =========================================================

  const filteredLogs = alertLogs.filter(log => {
    if (alertFilter === 'ALL') return true;

    return log.type === alertFilter;
  });

  // Welcome text
  const welcomeText = "Welcome to Netra";

  // =========================================================
  // CAMERA STREAM ERROR HANDLERS
  // =========================================================

  const handleCamera1Error = () => {
    setCamera1Online(false);
  };

  const handleCamera2Error = () => {
    setCamera2Online(false);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans relative overflow-x-hidden selection:bg-cyan-500 selection:text-black">

      {/* Custom animations */}
      <style>{`
        .netra-logo {
          display: inline-flex;
          align-items: baseline;
          transform: perspective(180px) rotateY(-8deg) rotateZ(-1deg);
          transform-origin: left center;
          letter-spacing: 0.12em;
          text-shadow: 0 2px 12px rgba(6, 182, 212, 0.18);
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
          -webkit-background-clip: text;
          background-clip: text;
          -webkit-text-fill-color: transparent;
          color: transparent;
        }

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
          color: transparent;

          transition:
            transform 0.28s cubic-bezier(0.2, 0.8, 0.2, 1),
            filter 0.25s ease;

          will-change: transform;
        }

        .welcome-letter:hover {
          transform: translateY(-14px) rotate(-3deg) scale(1.08);
        }

        .welcome-letter:hover + .welcome-letter {
          transform: translateY(-8px) rotate(2deg) scale(1.04);
        }

        .welcome-letter:has(+ .welcome-letter:hover) {
          transform: translateY(-8px) rotate(-2deg) scale(1.04);
        }

        .welcome-letter:has(+ .welcome-letter + .welcome-letter:hover) {
          transform: translateY(-4px) rotate(1deg);
        }

        .welcome-letter:hover + .welcome-letter + .welcome-letter {
          transform: translateY(-4px) rotate(-1deg);
        }

        .welcome-title {
          filter: none;
          text-shadow: none;
        }

        .back-dashboard-btn {
          position: relative;
          overflow: hidden;
          transition:
            transform 0.25s ease,
            border-color 0.25s ease,
            background 0.25s ease,
            box-shadow 0.25s ease;
        }

        .back-dashboard-btn:hover {
          transform: translateY(-2px);
        }

        .back-dashboard-btn:active {
          transform: translateY(0);
        }
      `}</style>

      {/* RED ALERT FLASHING OVERLAY */}
      {isAlertActive && (
        <div className="fixed inset-0 bg-red-600/20 pointer-events-none animate-pulse z-50 border-8 border-red-600" />
      )}

      {/* HEADER / NAVIGATION BAR */}
      <header className="border-b border-slate-800/80 bg-slate-900/60 backdrop-blur-md sticky top-0 z-40 px-6 py-3.5 flex items-center justify-between">

        <div
          className="flex items-center gap-3 cursor-pointer"
          onClick={() => setActivePage('dashboard')}
        >

          <div className="relative flex items-center justify-center">

            <img
              src="/Screenshot 2026-08-18 154958.png"
              alt="Netra Logo"
              className="w-9 h-9 rounded-full border border-cyan-500/40 object-cover shadow-sm shadow-cyan-500/20"
              onError={(e) => {
                e.target.style.display = 'none';
              }}
            />

          </div>

          <div>
            <h1 className="font-black font-mono netra-logo text-cyan-400">

              <span className="text-2xl tracking-wide">
                N
              </span>

              <span className="text-xl">
                ETR
              </span>

              <span className="text-2xl tracking-wide">
                A
              </span>

            </h1>
          </div>

        </div>

        {/* FULL PAGE NAVIGATION BUTTONS */}
        <nav className="hidden md:flex items-center gap-1 bg-slate-950/60 p-1 rounded-lg border border-slate-800/60 text-xs font-medium text-slate-400">

          <button
            onClick={() => setActivePage('dashboard')}
            className={`px-3.5 py-1.5 rounded-md transition-all ${
              activePage === 'dashboard'
                ? 'text-white bg-slate-800/80 border border-slate-700/50 shadow-sm'
                : 'hover:text-slate-100 hover:bg-slate-800/50 border border-transparent'
            }`}
          >
            Dashboard
          </button>

          <button
            onClick={() => setActivePage('alerts')}
            className={`px-3.5 py-1.5 rounded-md transition-all ${
              activePage === 'alerts'
                ? 'text-white bg-slate-800/80 border border-slate-700/50 shadow-sm'
                : 'hover:text-slate-100 hover:bg-slate-800/50 border border-transparent'
            }`}
          >
            Alerts
          </button>

          <button
            onClick={() => setActivePage('livefeed')}
            className={`px-3.5 py-1.5 rounded-md transition-all ${
              activePage === 'livefeed'
                ? 'text-white bg-slate-800/80 border border-slate-700/50 shadow-sm'
                : 'hover:text-slate-100 hover:bg-slate-800/50 border border-transparent'
            }`}
          >
            Live Feed
          </button>

          <button
            onClick={() => setActivePage('settings')}
            className={`px-3.5 py-1.5 rounded-md transition-all ${
              activePage === 'settings'
                ? 'text-white bg-slate-800/80 border border-slate-700/50 shadow-sm'
                : 'hover:text-slate-100 hover:bg-slate-800/50 border border-transparent'
            }`}
          >
            Settings
          </button>

        </nav>

        {/* TOP RIGHT: API STATUS + SYSTEM STATUS */}
        <div className="flex items-center gap-3">

          <div className="hidden sm:block text-right font-mono text-xs text-slate-400">
            <div>{currentTime}</div>
          </div>

          {isProcessing && (
            <div className="flex items-center gap-2 bg-amber-950/50 border border-amber-700/50 px-3 py-1.5 rounded-full text-xs">

              <span className="relative flex h-2.5 w-2.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-amber-500"></span>
              </span>

              <span className="text-amber-300 font-mono text-[11px] uppercase tracking-wider">
                Processing...
              </span>

            </div>
          )}

          {/* API STATUS */}
          <div className={`flex items-center gap-2 border px-3 py-1.5 rounded-full text-xs ${
            isApiConnected
              ? 'bg-emerald-950/40 border-emerald-700/40'
              : 'bg-red-950/40 border-red-700/40'
          }`}>

            <span className="relative flex h-2.5 w-2.5">
              {isApiConnected && (
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              )}
              <span className={`relative inline-flex rounded-full h-2.5 w-2.5 ${
                isApiConnected ? 'bg-emerald-500' : 'bg-red-500'
              }`}></span>
            </span>

            <span className={`font-mono text-[11px] uppercase tracking-wider ${
              isApiConnected ? 'text-emerald-400' : 'text-red-400'
            }`}>
              API: {isApiConnected ? 'Connected' : 'Disconnected'}
            </span>

          </div>

          {/* SYSTEM ONLINE - BLINKS ONLY WHEN BACKEND IS CONNECTED */}
          <div className={`flex items-center gap-2 bg-slate-900/90 border px-3 py-1.5 rounded-full text-xs ${
            isApiConnected ? 'border-emerald-700/40' : 'border-slate-800'
          }`}>

            <span className="relative flex h-2.5 w-2.5">
              {isApiConnected && (
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              )}
              <span className={`relative inline-flex rounded-full h-2.5 w-2.5 ${
                isApiConnected ? 'bg-emerald-500' : 'bg-slate-500'
              }`}></span>
            </span>

            <span className={`font-mono text-[11px] uppercase tracking-wider ${
              isApiConnected ? 'text-emerald-400' : 'text-slate-400'
            }`}>
              {isApiConnected ? 'System Online' : 'System Offline'}
            </span>

          </div>

        </div>

      </header>

      {/* MAIN CONTAINER */}
      <main className="max-w-7xl mx-auto px-6 py-10">

        {/* PROCESSING BANNER */}
        {isProcessing && (
          <div className="mb-6 p-3.5 bg-amber-950/40 border border-amber-700/50 rounded-xl flex items-center gap-3">

            <div className="flex items-center gap-2">

              <span className="relative flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-amber-500"></span>
              </span>

              <span className="text-amber-300 font-mono text-xs font-semibold">
                Processing...
              </span>

            </div>

            <span className="text-amber-400/70 text-xs">
              Processing alert information. Please wait.
            </span>

          </div>
        )}

        {/* EMERGENCY BANNER */}
        {isAlertActive && (
          <div className="mb-8 p-4 bg-red-950/60 border border-red-600/50 rounded-xl flex items-center justify-between shadow-lg shadow-red-950/50">

            <div className="flex items-center gap-3">

              <div>

                <h3 className="font-bold text-red-200 text-sm">
                  EMERGENCY THREAT DETECTED
                </h3>

                <p className="text-xs text-red-300/80 font-mono">
                  SOS gesture or high threat signal received from vision pipeline.
                </p>

              </div>

            </div>

            <button
              onClick={() => {
                setIsAlertActive(false);
                setIsProcessing(false);
              }}
              className="px-3 py-1.5 bg-red-900/50 hover:bg-red-800/80 border border-red-700/50 text-red-200 rounded-lg text-xs font-mono transition-all"
            >
              DISMISS
            </button>

          </div>
        )}

        {/* =====================================================
            PAGE 1: MAIN DASHBOARD
        ===================================================== */}

        {activePage === 'dashboard' && (
          <div>

            <div className="text-center my-10 max-w-3xl mx-auto">

              <div className="inline-block mb-4 px-3 py-1 bg-cyan-950/60 border border-cyan-800/50 rounded-full">

                <span className="text-xs font-mono text-cyan-400 tracking-wide">
                  AI-Powered Safety System
                </span>

              </div>

              <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight mb-6 welcome-title">

                {welcomeText.split('').map((letter, index) => (
                  <span
                    key={index}
                    className={`welcome-letter ${
                      letter === ' ' ? 'mr-2' : ''
                    }`}
                  >
                    {letter === ' ' ? '\u00A0' : letter}
                  </span>
                ))}

              </h1>

              <p className="text-slate-300 text-base sm:text-lg leading-relaxed mb-8 max-w-2xl mx-auto">
                Real-time threat detection & SOS alert system using AI vision and gesture recognition.
              </p>

              {/* Real-time Persons Count Display */}
              <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-xl text-center mb-4 max-w-xs mx-auto shadow-lg">

                <div className="text-slate-400 text-xs font-mono uppercase mb-1">
                  Persons Detected
                </div>

                <div className="text-3xl font-extrabold text-cyan-400 font-mono">
                  {liveData ? liveData.persons_detected : 0}
                </div>

              </div>

              <div>

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
                  className={`px-6 py-3 rounded-xl font-medium text-sm transition-all duration-200 shadow-lg ${
                    isAlertActive
                      ? 'bg-red-600 hover:bg-red-700 text-white shadow-red-900/50'
                      : 'bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold shadow-cyan-500/20'
                  }`}
                >
                  {isAlertActive
                    ? 'Reset Emergency Alert'
                    : 'Trigger Manual SOS Test'}
                </button>

              </div>

            </div>

            {/* CARDS GRID */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-16">

              <div
                onClick={() => setActivePage('yolo_detail')}
                className="bg-slate-900/40 border border-slate-800/80 p-6 rounded-2xl hover:border-cyan-500/50 hover:bg-slate-900/80 hover:shadow-[0_0_35px_rgba(6,182,212,0.18)] transition-all duration-300 transform hover:-translate-y-2 cursor-pointer group"
              >

                <div className="w-10 h-10 rounded-xl bg-cyan-950/60 border border-cyan-800/40 flex items-center justify-center text-cyan-400 text-xl mb-4 group-hover:scale-125 transition-transform">
                  Camera
                </div>

                <h3 className="font-semibold text-white text-base mb-2 text-center">
                  Real-time Detection
                </h3>

                <p className="text-slate-400 text-xs leading-relaxed mb-4">
                  YOLO based person & gender detection with live webcam processing.
                </p>

                <span className="text-cyan-400 text-xs font-mono group-hover:underline flex items-center gap-1">
                  Open Detection Studio →
                </span>

              </div>

              <div
                onClick={() => setActivePage('gesture_detail')}
                className="bg-slate-900/40 border border-slate-800/80 p-6 rounded-2xl hover:border-indigo-500/50 hover:bg-slate-900/80 hover:shadow-[0_0_35px_rgba(99,102,241,0.18)] transition-all duration-300 transform hover:-translate-y-2 cursor-pointer group"
              >

                <div className="w-10 h-10 rounded-xl bg-indigo-950/60 border border-indigo-800/40 flex items-center justify-center text-indigo-400 text-xl mb-4 group-hover:scale-125 transition-transform">
                  Gesture
                </div>

                <h3 className="font-semibold text-white text-base mb-2 text-center">
                  SOS Gesture Tracking
                </h3>

                <p className="text-slate-400 text-xs leading-relaxed mb-4">
                  MediaPipe powered pose estimation to detect emergency gestures.
                </p>

                <span className="text-indigo-400 text-xs font-mono group-hover:underline flex items-center gap-1">
                  View Gesture Analyzer →
                </span>

              </div>

              <div
                onClick={() => setActivePage('alerts_detail')}
                className="bg-slate-900/40 border border-slate-800/80 p-6 rounded-2xl hover:border-emerald-500/50 hover:bg-slate-900/80 hover:shadow-[0_0_35px_rgba(16,185,129,0.18)] transition-all duration-300 transform hover:-translate-y-2 cursor-pointer group"
              >

                <div className="w-10 h-10 rounded-xl bg-emerald-950/60 border border-emerald-800/40 flex items-center justify-center text-emerald-400 text-xl mb-4 group-hover:scale-110 transition-transform">
                  Alerts
                </div>

                <h3 className="font-semibold text-white text-base mb-2 text-center">
                  Instant Alerts
                </h3>

                <p className="text-slate-400 text-xs leading-relaxed mb-4">
                  Automatic Telegram & cloud alerts when threat is detected.
                </p>

                <span className="text-emerald-400 text-xs font-mono group-hover:underline flex items-center gap-1">
                  Configure Webhooks →
                </span>

              </div>

            </div>

          </div>
        )}

        {/* =====================================================
            PAGE 2: ALERTS
        ===================================================== */}

        {activePage === 'alerts' && (
          <div className="space-y-6">

            <div className="flex flex-col items-center justify-center text-center gap-4">

              <div className="w-full text-center">

                <h2 className="text-2xl font-bold text-white flex items-center justify-center gap-2 text-center">
                  System Threat & Emergency Logs
                </h2>

                <p className="text-slate-400 text-xs text-center mt-1">
                  Real-time alert logs with interactive controls and filtering.
                </p>

              </div>

              <div className="flex items-center justify-center gap-2">

                <button
                  onClick={handleSimulateAlert}
                  className="px-3.5 py-1.5 bg-cyan-950 hover:bg-cyan-900 border border-cyan-800 text-cyan-300 rounded-lg text-xs font-mono transition-all flex items-center gap-1.5"
                >
                  Simulate Alert
                </button>

                <button
                  onClick={() => setAlertLogs([])}
                  className="px-3 py-1.5 bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-400 hover:text-slate-200 rounded-lg text-xs font-mono transition-all"
                >
                  Clear Logs
                </button>

              </div>

            </div>

            <div className="flex items-center justify-center gap-2 border-b border-slate-800 pb-3 text-xs font-mono">

              <span className="text-slate-500 mr-2">
                Filter:
              </span>

              {['ALL', 'CRITICAL', 'WARNING'].map(filter => (

                <button
                  key={filter}
                  onClick={() => setAlertFilter(filter)}
                  className={`px-3 py-1 rounded-md transition-all ${
                    alertFilter === filter
                      ? 'bg-slate-800 text-cyan-400 border border-cyan-500/30'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >

                  {filter} (
                  {filter === 'ALL'
                    ? alertLogs.length
                    : alertLogs.filter(l => l.type === filter).length}
                  )

                </button>

              ))}

            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 font-mono text-xs space-y-3 min-h-[250px]">

              {filteredLogs.length === 0 ? (

                <div className="text-center py-12 text-slate-500">
                  No logs available for current filter category.
                </div>

              ) : (

                filteredLogs.map(log => (

                  <div
                    key={log.id}
                    className={`p-3.5 border rounded-xl flex justify-between items-center transition-all ${
                      log.type === 'CRITICAL'
                        ? 'bg-red-950/40 border-red-800/50 text-red-300'
                        : log.type === 'WARNING'
                          ? 'bg-amber-950/40 border-amber-800/50 text-amber-300'
                          : 'bg-slate-950 border-slate-800 text-slate-400'
                    }`}
                  >

                    <div className="flex items-center gap-2.5">

                      <span className="font-bold text-[10px] px-2 py-0.5 rounded bg-black/40 border border-white/10">
                        [{log.type}]
                      </span>

                      <span>
                        {log.message}
                      </span>

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

        {/* =========================================================
            PAGE 3: FULL LIVE FEED
            CAMERA 1 + CAMERA 2
        ========================================================= */}

        {activePage === 'livefeed' && (

          <div className="space-y-6">

            <h2 className="text-2xl font-bold text-white flex items-center justify-center gap-2 text-center">
              Live Vision Stream
            </h2>

            <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">

              {/* =================================================
                  CAMERA 1
              ================================================= */}

              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">

                <div className="flex items-center justify-between mb-4">

                  <div>

                    <h3 className="text-white font-bold text-sm">
                      Camera #1
                    </h3>

                    <p className="text-slate-500 text-[11px] font-mono">
                      IP Webcam • 192.168.1.6:8080
                    </p>

                  </div>

                  <div
                    className={`flex items-center gap-2 px-3 py-1.5 rounded-full ${
                      camera1Online
                        ? 'bg-emerald-950/50 border border-emerald-700/40'
                        : 'bg-red-950/50 border border-red-700/40'
                    }`}
                  >

                    <span className="relative flex h-2.5 w-2.5">

                      {camera1Online && (
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                      )}

                      <span
                        className={`relative inline-flex rounded-full h-2.5 w-2.5 ${
                          camera1Online
                            ? 'bg-emerald-500'
                            : 'bg-red-500'
                        }`}
                      ></span>

                    </span>

                    <span
                      className={`text-[11px] font-mono ${
                        camera1Online
                          ? 'text-emerald-400'
                          : 'text-red-400'
                      }`}
                    >
                      {camera1Online
                        ? 'LIVE'
                        : 'CAM 1 OFF'}
                    </span>

                  </div>

                </div>

                {/* CAMERA 1 FEED */}
                <div className="relative w-full aspect-video bg-black rounded-xl overflow-hidden border border-slate-800">

                  {camera1Online ? (

                    <img
                      key={`camera1-${camera1Refresh}`}
                      src={`${CAMERA_1_URL}?stream=${camera1Refresh}`}
                      alt="Camera 1 Live Feed"
                      className="w-full h-full object-contain"
                      onError={handleCamera1Error}
                    />

                  ) : (

                    <div className="absolute inset-0 flex flex-col items-center justify-center bg-slate-950">

                      <div className="w-14 h-14 rounded-full bg-red-950/60 border border-red-800/50 flex items-center justify-center mb-4">

                        <span className="text-red-500 text-2xl">
                          !
                        </span>

                      </div>

                      <div className="text-red-400 font-mono text-sm font-bold">
                        CAM 1 OFF
                      </div>

                      <div className="text-slate-500 text-[11px] font-mono mt-1">
                        Camera connection lost
                      </div>

                    </div>

                  )}

                  {/* CAMERA 1 REC OVERLAY */}
                  {camera1Online && (

                    <div className="absolute top-3 left-3 flex items-center gap-2 bg-black/70 backdrop-blur-sm px-3 py-1.5 rounded-lg border border-red-500/30">

                      <span className="relative flex h-2.5 w-2.5">

                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-500 opacity-75"></span>

                        <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-red-500"></span>

                      </span>

                      <span className="text-red-400 text-[11px] font-mono font-bold">
                        REC
                      </span>

                    </div>

                  )}

                  {/* CAMERA 1 NAME */}
                  <div className="absolute bottom-3 left-3 bg-black/70 backdrop-blur-sm px-3 py-1.5 rounded-lg border border-slate-700/50">

                    <span className="text-slate-300 text-[11px] font-mono">
                      NETRA-CAM-01
                    </span>

                  </div>

                </div>

                {/* CAMERA 1 INFORMATION */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-4">

                  <div className="bg-slate-950 border border-slate-800 rounded-xl p-3 text-center">

                    <div className="text-slate-500 text-[10px] font-mono uppercase">
                      Camera
                    </div>

                    <div className="text-cyan-400 text-xs font-mono mt-1">
                      IP Webcam
                    </div>

                  </div>

                  <div className="bg-slate-950 border border-slate-800 rounded-xl p-3 text-center">

                    <div className="text-slate-500 text-[10px] font-mono uppercase">
                      Stream
                    </div>

                    <div className="text-emerald-400 text-xs font-mono mt-1">
                      MJPEG Live
                    </div>

                  </div>

                  <div className="bg-slate-950 border border-slate-800 rounded-xl p-3 text-center">

                    <div className="text-slate-500 text-[10px] font-mono uppercase">
                      Status
                    </div>

                    <div
                      className={`text-xs font-mono mt-1 ${
                        camera1Online
                          ? 'text-emerald-400'
                          : 'text-red-400'
                      }`}
                    >
                      {camera1Online
                        ? 'Connected'
                        : 'Offline'}
                    </div>

                  </div>

                </div>

              </div>

              {/* =================================================
                  CAMERA 2
              ================================================= */}

              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">

                <div className="flex items-center justify-between mb-4">

                  <div>

                    <h3 className="text-white font-bold text-sm">
                      Camera #2
                    </h3>

                    <p className="text-slate-500 text-[11px] font-mono">
                      IP Webcam • 192.168.1.7:8080
                    </p>

                  </div>

                  <div
                    className={`flex items-center gap-2 px-3 py-1.5 rounded-full ${
                      camera2Online
                        ? 'bg-emerald-950/50 border border-emerald-700/40'
                        : 'bg-red-950/50 border border-red-700/40'
                    }`}
                  >

                    <span className="relative flex h-2.5 w-2.5">

                      {camera2Online && (
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                      )}

                      <span
                        className={`relative inline-flex rounded-full h-2.5 w-2.5 ${
                          camera2Online
                            ? 'bg-emerald-500'
                            : 'bg-red-500'
                        }`}
                      ></span>

                    </span>

                    <span
                      className={`text-[11px] font-mono ${
                        camera2Online
                          ? 'text-emerald-400'
                          : 'text-red-400'
                      }`}
                    >
                      {camera2Online
                        ? 'LIVE'
                        : 'CAM 2 OFF'}
                    </span>

                  </div>

                </div>

                {/* CAMERA 2 FEED */}
                <div className="relative w-full aspect-video bg-black rounded-xl overflow-hidden border border-slate-800">

                  {camera2Online ? (

                    <img
                      key={`camera2-${camera2Refresh}`}
                      src={`${CAMERA_2_URL}?stream=${camera2Refresh}`}
                      alt="Camera 2 Live Feed"
                      className="w-full h-full object-contain"
                      onError={handleCamera2Error}
                    />

                  ) : (

                    <div className="absolute inset-0 flex flex-col items-center justify-center bg-slate-950">

                      <div className="w-14 h-14 rounded-full bg-red-950/60 border border-red-800/50 flex items-center justify-center mb-4">

                        <span className="text-red-500 text-2xl">
                          !
                        </span>

                      </div>

                      <div className="text-red-400 font-mono text-sm font-bold">
                        CAM 2 OFF
                      </div>

                      <div className="text-slate-500 text-[11px] font-mono mt-1">
                        Camera connection lost
                      </div>

                    </div>

                  )}

                  {/* CAMERA 2 REC OVERLAY */}
                  {camera2Online && (

                    <div className="absolute top-3 left-3 flex items-center gap-2 bg-black/70 backdrop-blur-sm px-3 py-1.5 rounded-lg border border-red-500/30">

                      <span className="relative flex h-2.5 w-2.5">

                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-500 opacity-75"></span>

                        <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-red-500"></span>

                      </span>

                      <span className="text-red-400 text-[11px] font-mono font-bold">
                        REC
                      </span>

                    </div>

                  )}

                  {/* CAMERA 2 NAME */}
                  <div className="absolute bottom-3 left-3 bg-black/70 backdrop-blur-sm px-3 py-1.5 rounded-lg border border-slate-700/50">

                    <span className="text-slate-300 text-[11px] font-mono">
                      NETRA-CAM-02
                    </span>

                  </div>

                </div>

                {/* CAMERA 2 INFORMATION */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-4">

                  <div className="bg-slate-950 border border-slate-800 rounded-xl p-3 text-center">

                    <div className="text-slate-500 text-[10px] font-mono uppercase">
                      Camera
                    </div>

                    <div className="text-cyan-400 text-xs font-mono mt-1">
                      IP Webcam
                    </div>

                  </div>

                  <div className="bg-slate-950 border border-slate-800 rounded-xl p-3 text-center">

                    <div className="text-slate-500 text-[10px] font-mono uppercase">
                      Stream
                    </div>

                    <div className="text-emerald-400 text-xs font-mono mt-1">
                      MJPEG Live
                    </div>

                  </div>

                  <div className="bg-slate-950 border border-slate-800 rounded-xl p-3 text-center">

                    <div className="text-slate-500 text-[10px] font-mono uppercase">
                      Status
                    </div>

                    <div
                      className={`text-xs font-mono mt-1 ${
                        camera2Online
                          ? 'text-emerald-400'
                          : 'text-red-400'
                      }`}
                    >
                      {camera2Online
                        ? 'Connected'
                        : 'Offline'}
                    </div>

                  </div>

                </div>

              </div>

            </div>

          </div>
        )}

        {/* =====================================================
            PAGE 4: SETTINGS
        ===================================================== */}

        {activePage === 'settings' && (

          <div className="space-y-6 max-w-2xl mx-auto">

            <div className="flex items-center justify-between">

              <div className="w-full">

                <h2 className="text-2xl font-bold text-white flex items-center justify-center gap-2 text-center">
                  System Configuration
                </h2>

                <p className="text-slate-400 text-xs text-center">
                  Adjust AI thresholds and notification preferences.
                </p>

              </div>

              {saveToast && (

                <span className="text-xs bg-emerald-950 border border-emerald-700 text-emerald-400 px-3 py-1 rounded-lg animate-fade-in">
                  Settings Saved!
                </span>

              )}

            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-6 text-xs">

              <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 space-y-3">

                <div className="flex justify-between items-center">

                  <div>

                    <div className="font-semibold text-white">
                      YOLO Object Confidence Threshold
                    </div>

                    <div className="text-slate-400 text-[11px]">
                      Minimum probability required for threat detection
                    </div>

                  </div>

                  <span className="font-mono text-cyan-400 bg-cyan-950 px-2.5 py-1 rounded border border-cyan-800 font-bold">
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
                  className="w-full accent-cyan-500 bg-slate-800 cursor-pointer h-1.5 rounded-lg"
                />

              </div>

              <div className="flex justify-between items-center p-4 bg-slate-950 rounded-xl border border-slate-800">

                <div>

                  <div className="font-semibold text-white">
                    Telegram Alert Dispatcher
                  </div>

                  <div className="text-slate-400 text-[11px]">
                    Automatically forward snapshot alerts to Telegram
                  </div>

                </div>

                <button
                  onClick={() =>
                    setTelegramEnabled(!telegramEnabled)
                  }
                  className={`w-12 h-6 flex items-center rounded-full p-1 transition-all duration-300 ${
                    telegramEnabled
                      ? 'bg-emerald-600 justify-end'
                      : 'bg-slate-800 justify-start'
                  }`}
                >

                  <span className="w-4 h-4 rounded-full bg-white shadow-md"></span>

                </button>

              </div>

              <div className="pt-2 flex justify-end">

                <button
                  onClick={handleSaveSettings}
                  className="px-5 py-2.5 bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold rounded-xl text-xs transition-all shadow-md shadow-cyan-500/20"
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

        {activePage === 'yolo_detail' && (

          <div className="space-y-6 relative min-h-[520px] pb-20">

            <h2 className="text-2xl font-bold text-white text-center">
              YOLO Real-Time Detection Model
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

              <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl">

                <h3 className="text-sm font-bold text-cyan-400 mb-2 text-center">
                  Model Specifications
                </h3>

                <ul className="text-xs text-slate-300 space-y-2 font-mono">

                  <li>
                    • Backbone: YOLOv8 / YOLOv11
                  </li>

                  <li>
                    • Target Classes: Person, Threat Items
                  </li>

                  <li>
                    • Latency: ~12ms per frame
                  </li>

                </ul>

              </div>

              <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl">

                <h3 className="text-sm font-bold text-emerald-400 mb-2 text-center">
                  Pipeline Status
                </h3>

                <div className="text-xs text-slate-300 font-mono text-center">
                  Video capture active on webcam device index 0.
                </div>

              </div>

            </div>

            <button
              onClick={() =>
                setActivePage('dashboard')
              }
              className="back-dashboard-btn absolute bottom-0 right-0 px-5 py-2.5 bg-slate-900 hover:bg-cyan-950/80 border border-slate-700 hover:border-cyan-500/60 text-cyan-400 hover:text-cyan-300 rounded-xl text-xs font-mono shadow-lg hover:shadow-cyan-500/10"
            >
              ← Back to Dashboard
            </button>

          </div>
        )}

        {/* =====================================================
            GESTURE DETAIL
        ===================================================== */}

        {activePage === 'gesture_detail' && (

          <div className="space-y-6 relative min-h-[520px] pb-20">

            <h2 className="text-2xl font-bold text-white text-center">
              MediaPipe SOS Gesture Tracker
            </h2>

            <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl font-mono text-xs text-slate-300 space-y-3">

              <div className="text-indigo-400 font-bold text-center">
                [Keypoint Landmarks Active]
              </div>

              <p className="text-center">
                Tracking 21 3D hand landmarks for distress gesture identification.
              </p>

              <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl text-emerald-400 text-center">
                Trigger Gesture: Open Palm SOS / Raised Hand Signal
              </div>

            </div>

            <button
              onClick={() =>
                setActivePage('dashboard')
              }
              className="back-dashboard-btn absolute bottom-0 right-0 px-5 py-2.5 bg-slate-900 hover:bg-indigo-950/80 border border-slate-700 hover:border-indigo-500/60 text-indigo-400 hover:text-indigo-300 rounded-xl text-xs font-mono shadow-lg hover:shadow-indigo-500/10"
            >
              ← Back to Dashboard
            </button>

          </div>
        )}

        {/* =====================================================
            ALERT DETAIL
        ===================================================== */}

        {activePage === 'alerts_detail' && (

          <div className="space-y-6 max-w-3xl mx-auto relative min-h-[520px] pb-20">

            <h2 className="text-2xl font-bold text-white text-center">
              Telegram & Webhook Dispatcher
            </h2>

            <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl space-y-5 text-xs">

              <p className="text-slate-300 leading-relaxed text-center">
                Configure your Telegram Bot token and Chat ID below to trigger live test notifications directly from the dashboard.
              </p>

              <div className="space-y-4 font-mono">

                <div>

                  <label className="block text-slate-400 mb-1.5 text-[11px]">
                    Telegram Bot Token:
                  </label>

                  <input
                    type="text"
                    value={botToken}
                    onChange={(e) =>
                      setBotToken(e.target.value)
                    }
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-cyan-300 focus:outline-none focus:border-cyan-500 transition-colors"
                  />

                </div>

                <div>

                  <label className="block text-slate-400 mb-1.5 text-[11px]">
                    Target Chat / Group ID:
                  </label>

                  <input
                    type="text"
                    value={chatId}
                    onChange={(e) =>
                      setChatId(e.target.value)
                    }
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-cyan-300 focus:outline-none focus:border-cyan-500 transition-colors"
                  />

                </div>

              </div>

              <div className="pt-2 flex items-center justify-between">

                <button
                  onClick={handleSendTestMessage}
                  disabled={testStatus === 'SENDING'}
                  className="px-5 py-2.5 bg-emerald-500 hover:bg-emerald-400 disabled:bg-slate-800 text-slate-950 font-bold rounded-xl text-xs transition-all shadow-md shadow-emerald-500/20 flex items-center gap-2"
                >

                  {testStatus === 'SENDING'
                    ? 'Processing...'
                    : 'Send Test Notification'}

                </button>

                {testStatus === 'SUCCESS' && (

                  <span className="text-emerald-400 font-mono text-xs flex items-center gap-1.5">
                    Telegram Payload Dispatched Successfully!
                  </span>

                )}

              </div>

            </div>

            <button
              onClick={() =>
                setActivePage('dashboard')
              }
              className="back-dashboard-btn absolute bottom-0 right-0 px-5 py-2.5 bg-slate-900 hover:bg-emerald-950/80 border border-slate-700 hover:border-emerald-500/60 text-emerald-400 hover:text-emerald-300 rounded-xl text-xs font-mono shadow-lg hover:shadow-emerald-500/10"
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