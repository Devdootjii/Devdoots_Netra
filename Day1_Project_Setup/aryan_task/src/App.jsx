import { useState, useEffect, useRef } from 'react'

function App() {
  const [isAlertActive, setIsAlertActive] = useState(false)
  const intervalRef = useRef(null)

  // Emergency Bell / Alert Sound generator
  const playAlertSound = () => {
    const audioCtx = new (window.AudioContext || window.webkitAudioContext)()
    
    // First High Tone
    const osc1 = audioCtx.createOscillator()
    const gain1 = audioCtx.createGain()
    osc1.type = 'sine'
    osc1.frequency.setValueAtTime(880, audioCtx.currentTime)
    gain1.gain.setValueAtTime(0.3, audioCtx.currentTime)
    gain1.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.3)

    osc1.connect(gain1)
    gain1.connect(audioCtx.destination)
    osc1.start(audioCtx.currentTime)
    osc1.stop(audioCtx.currentTime + 0.3)

    // Second Tone
    const osc2 = audioCtx.createOscillator()
    const gain2 = audioCtx.createGain()
    osc2.type = 'triangle'
    osc2.frequency.setValueAtTime(660, audioCtx.currentTime + 0.15)
    gain2.gain.setValueAtTime(0.3, audioCtx.currentTime + 0.15)
    gain2.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.45)

    osc2.connect(gain2)
    gain2.connect(audioCtx.destination)
    osc2.start(audioCtx.currentTime + 0.15)
    osc2.stop(audioCtx.currentTime + 0.45)
  }

  useEffect(() => {
    if (isAlertActive) {
      playAlertSound()
      intervalRef.current = setInterval(() => {
        playAlertSound()
      }, 900)
    } else {
      clearInterval(intervalRef.current)
    }
    return () => clearInterval(intervalRef.current)
  }, [isAlertActive])

  // Radius-Based Smooth Wave Effect Component
  const WaveText = ({ text, highlightText = "" }) => {
    const [mousePos, setMousePos] = useState({ x: -1000, y: -1000 })

    const handleMouseMove = (e) => {
      setMousePos({ x: e.clientX, y: e.clientY })
    }

    const handleMouseLeave = () => {
      setMousePos({ x: -1000, y: -1000 })
    }

    const renderWaveChars = (str, isHighlight = false) => {
      return str.split("").map((char, index) => (
        <WaveChar 
          key={index} 
          char={char} 
          mousePos={mousePos} 
          isHighlight={isHighlight}
        />
      ))
    }

    return (
      <span 
        onMouseMove={handleMouseMove} 
        onMouseLeave={handleMouseLeave}
        className="inline-block cursor-default select-none py-2"
      >
        {renderWaveChars(text, false)}
        {highlightText && renderWaveChars(highlightText, true)}
      </span>
    )
  }

  const WaveChar = ({ char, mousePos, isHighlight }) => {
    const ref = useRef(null)
    const [transformStyle, setTransformStyle] = useState({})

    useEffect(() => {
      if (!ref.current) return
      const rect = ref.current.getBoundingClientRect()
      const charX = rect.left + rect.width / 2
      const charY = rect.top + rect.height / 2

      const dist = Math.hypot(mousePos.x - charX, mousePos.y - charY)
      const radius = 60 // Wave influence radius in pixels

      if (dist < radius) {
        const factor = 1 - dist / radius
        const translateY = -factor * 12 // Upward wave bump
        const scale = 1 + factor * 0.25 // Smooth letter scaling

        setTransformStyle({
          transform: `translateY(${translateY}px) scale(${scale})`,
          transition: 'transform 0.1s ease-out'
        })
      } else {
        setTransformStyle({
          transform: 'translateY(0px) scale(1)',
          transition: 'transform 0.3s ease-in-out'
        })
      }
    }, [mousePos])

    return (
      <span
        ref={ref}
        style={transformStyle}
        className={`inline-block ${isHighlight ? 'text-blue-400' : 'text-white'}`}
      >
        {char === " " ? "\u00A0" : char}
      </span>
    )
  }

  return (
    <div className={`min-h-screen bg-gray-950 text-white transition-all duration-300 ${
      isAlertActive ? 'border-4 border-red-500 animate-pulse' : 'border-4 border-transparent'
    }`}>
      
      {/* Navbar */}
      <nav className="bg-gray-900/80 backdrop-blur-md border-b border-gray-800 px-6 py-4 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center font-bold text-sm">N</div>
            <span className="text-xl font-semibold tracking-wide">
              Project <span className="text-blue-400">Netra</span>
            </span>
          </div>

          <div className="hidden md:flex items-center gap-8 text-sm font-medium">
            <a href="#" className="text-blue-400">Dashboard</a>
            <a href="#" className="text-gray-400 hover:text-white transition">Alerts</a>
            <a href="#" className="text-gray-400 hover:text-white transition">Live Feed</a>
            <a href="#" className="text-gray-400 hover:text-white transition">Settings</a>
          </div>

          <div className={`flex items-center gap-2 text-xs px-3 py-1.5 rounded-full border ${
            isAlertActive 
              ? 'bg-red-500/10 text-red-400 border-red-500/30' 
              : 'bg-green-500/10 text-green-400 border-green-500/20'
          }`}>
            <div className={`w-2 h-2 rounded-full ${isAlertActive ? 'bg-red-400 animate-ping' : 'bg-green-400'}`}></div>
            {isAlertActive ? 'ALERT ACTIVE' : 'System Online'}
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-6 pt-12 pb-16">
        
        {isAlertActive && (
          <div className="mb-8 bg-red-500/10 border border-red-500/50 text-red-400 px-5 py-4 rounded-xl flex items-center justify-between animate-pulse">
            <div className="flex items-center gap-3">
              <span className="text-xl">🚨</span>
              <div>
                <p className="font-semibold">SOS Alert Detected!</p>
                <p className="text-sm text-red-300">Emergency gesture detected. Notifying authorities...</p>
              </div>
            </div>
            <button 
              onClick={() => setIsAlertActive(false)}
              className="text-xs bg-red-500/20 hover:bg-red-500/30 px-3 py-1 rounded-lg transition"
            >
              Dismiss
            </button>
          </div>
        )}

        <div className="text-center">
          <div className="inline-flex items-center gap-2 bg-blue-500/10 text-blue-400 text-xs font-medium px-3 py-1 rounded-full border border-blue-500/20 mb-6">
            AI-Powered Safety System
          </div>

          {/* Dynamic Wave Effect Heading */}
          <h1 className="text-5xl md:text-6xl font-bold mb-6 leading-tight">
            <WaveText text="Welcome to Project " highlightText="Netra" />
          </h1>

          {/* Subtitle */}
          <p className="text-gray-400 text-lg md:text-xl max-w-2xl mx-auto mb-10">
            Real-time threat detection & SOS alert system using AI vision and gesture recognition.
          </p>

          <button 
            onClick={() => setIsAlertActive(!isAlertActive)}
            className={`px-6 py-3 rounded-lg font-medium text-sm transition ${
              isAlertActive 
                ? 'bg-red-600 hover:bg-red-500' 
                : 'bg-blue-600 hover:bg-blue-500'
            }`}
          >
            {isAlertActive ? 'Stop Alert' : 'Trigger SOS Alert'}
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-20">
          <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6 hover:-translate-y-2 hover:shadow-xl hover:shadow-blue-500/20 hover:border-blue-500/40 transition-all duration-300 cursor-pointer">
            <div className="w-10 h-10 bg-blue-600/20 text-blue-400 rounded-lg flex items-center justify-center mb-4 text-lg">👁️</div>
            <h3 className="font-semibold text-lg mb-2">Real-time Detection</h3>
            <p className="text-gray-400 text-sm">YOLO based person & gender detection with live webcam processing.</p>
          </div>

          <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6 hover:-translate-y-2 hover:shadow-xl hover:shadow-purple-500/20 hover:border-purple-500/40 transition-all duration-300 cursor-pointer">
            <div className="w-10 h-10 bg-purple-600/20 text-purple-400 rounded-lg flex items-center justify-center mb-4 text-lg">✋</div>
            <h3 className="font-semibold text-lg mb-2">SOS Gesture Tracking</h3>
            <p className="text-gray-400 text-sm">MediaPipe powered pose estimation to detect emergency gestures.</p>
          </div>

          <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6 hover:-translate-y-2 hover:shadow-xl hover:shadow-green-500/20 hover:border-green-500/40 transition-all duration-300 cursor-pointer">
            <div className="w-10 h-10 bg-green-600/20 text-green-400 rounded-lg flex items-center justify-center mb-4 text-lg">🚨</div>
            <h3 className="font-semibold text-lg mb-2">Instant Alerts</h3>
            <p className="text-gray-400 text-sm">Automatic Telegram & cloud alerts when threat is detected.</p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App 