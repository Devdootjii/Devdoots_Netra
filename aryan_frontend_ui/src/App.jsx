function App() {
  return (
    <div className="min-h-screen bg-gray-950 text-white">
      
      {/* Navbar */}
      <nav className="bg-gray-900/80 backdrop-blur-md border-b border-gray-800 px-6 py-4 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          
          {/* Logo */}
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center font-bold text-sm">
              N
            </div>
            <span className="text-xl font-semibold tracking-wide">
              Project <span className="text-blue-400">Netra</span>
            </span>
          </div>

          {/* Links */}
          <div className="hidden md:flex items-center gap-8 text-sm font-medium">
            <a href="#" className="text-blue-400">Dashboard</a>
            <a href="#" className="text-gray-400 hover:text-white transition">Alerts</a>
            <a href="#" className="text-gray-400 hover:text-white transition">Live Feed</a>
            <a href="#" className="text-gray-400 hover:text-white transition">Settings</a>
          </div>

          {/* Status Badge */}
          <div className="flex items-center gap-2 text-xs bg-green-500/10 text-green-400 px-3 py-1.5 rounded-full border border-green-500/20">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
            System Online
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <div className="max-w-7xl mx-auto px-6 pt-20 pb-16">
        <div className="text-center">
          <div className="inline-flex items-center gap-2 bg-blue-500/10 text-blue-400 text-xs font-medium px-3 py-1 rounded-full border border-blue-500/20 mb-6">
            AI-Powered Safety System
          </div>

          <h1 className="text-5xl md:text-6xl font-bold mb-6 leading-tight">
            Welcome to <span className="text-blue-400">Project Netra</span>
          </h1>

          <p className="text-gray-400 text-lg md:text-xl max-w-2xl mx-auto mb-10">
            Real-time threat detection & SOS alert system using AI vision and gesture recognition.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-4">
            <button className="bg-blue-600 hover:bg-blue-500 transition px-6 py-3 rounded-lg font-medium text-sm">
              Go to Dashboard
            </button>
            <button className="bg-gray-800 hover:bg-gray-700 transition px-6 py-3 rounded-lg font-medium text-sm border border-gray-700">
              View Live Feed
            </button>
          </div>
        </div>

        {/* Updated Feature Cards based on requirements */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-20">
          
          {/* Card 1: Live Camera Stream */}
          <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6 hover:border-blue-500/50 transition">
            <div className="w-10 h-10 bg-blue-600/20 text-blue-400 rounded-lg flex items-center justify-center mb-4 text-lg">
              📹
            </div>
            <h3 className="font-semibold text-lg mb-2">Live Camera Stream</h3>
            <p className="text-gray-400 text-sm">
              Real-time video feed monitoring with AI object and gesture detection.
            </p>
          </div>

          {/* Card 2: Recent Alerts */}
          <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6 hover:border-blue-500/50 transition">
            <div className="w-10 h-10 bg-purple-600/20 text-purple-400 rounded-lg flex items-center justify-center mb-4 text-lg">
              🚨
            </div>
            <h3 className="font-semibold text-lg mb-2">Recent Alerts</h3>
            <p className="text-gray-400 text-sm">
              Instant notification logs and emergency trigger history.
            </p>
          </div>

          {/* Card 3: Analytics Graph */}
          <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6 hover:border-blue-500/50 transition">
            <div className="w-10 h-10 bg-green-600/20 text-green-400 rounded-lg flex items-center justify-center mb-4 text-lg">
              📊
            </div>
            <h3 className="font-semibold text-lg mb-2">Analytics Graph</h3>
            <p className="text-gray-400 text-sm">
              Data visualization for threat statistics and performance metrics.
            </p>
          </div>

        </div>
      </div>
    </div>
  )
}

export default App