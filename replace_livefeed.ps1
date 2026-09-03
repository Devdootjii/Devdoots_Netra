 = 'App.jsx'
 = Get-Content -Raw -Path 

 = '{activePage === "livefeed" && ('
 = .IndexOf()
if ( -lt 0) {
    Write-Error "Start marker not found"
    exit 1
}

# We need to find the matching closing parenthesis for the one after '&&'
# Actually, the pattern is: {activePage === "livefeed" && ( ... ) }
# So from the startIndex, we have the '{', then the content until '&&', then '('
# Let's find the opening parenthesis after '&&'
 = .IndexOf('&&', )
if ( -lt 0) {
    Write-Error "'&&' not found after start marker"
    exit 1
}
 = .IndexOf('(', )
if ( -lt 0) {
    Write-Error "Opening parenthesis not found after '&&'"
    exit 1
}

# Now find the matching closing parenthesis
 = 0
 = 
while ( -lt .Length) {
     = []
    if ( -eq '(') { ++ }
    elseif ( -eq ')') { -- }
    if ( -eq 0) { break }
    ++
}
if ( -ge .Length) {
    Write-Error "Matching closing parenthesis not found"
    exit 1
}
 = 

# After the closing parenthesis, we expect optional whitespace and then a closing curly brace for the object literal
 = .IndexOf(')', ) # we already have 
# Actually, we need to find the '}' after the closing parenthesis
 = .Substring( + 1)
 = .IndexOf('}')
if ( -lt 0) {
    Write-Error "Closing curly brace not found after closing parenthesis"
    exit 1
}
 =  + 1 + 

# Now we have the range to replace: from  to  (inclusive)
# We'll replace this segment with our new livefeed block.

 = @'{activePage === "livefeed" && (
  <div className="space-y-6">

    <div className="text-center">

      <h2 className="text-2xl font-bold text-white">
        Live Vision Stream
      </h2>

      <p className="text-slate-500 text-xs mt-1">
        Webcam integration for NETRA vision pipeline
      </p>

    </div>

    {/* WEBCAM INFO */}

    <div className="bg-cyan-950/30 border border-cyan-800/50 rounded-2xl p-5 netra-panel">

      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">

        <div>

          <h3 className="text-cyan-400 font-bold text-sm font-mono">
            WEBCAM SOURCE
          </h3>

          <p className="text-slate-400 text-xs mt-1">
            Integrated Webcam
          </p>

          <p className="text-slate-400 text-xs font-mono">
            Device: Default Webcam
          </p>

        </div>

        <div className="text-right">

          <p className="text-slate-500 text-[10px] font-mono">
            WEBCAM STATUS
          </p>

          <p className="text-cyan-300 text-xs font-mono">
            Ready
          </p>

        </div>

      </div>

    </div>

    {/* STATUS */}

    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 netra-panel">

      <div className="grid grid-cols-1 max-w-md mx-auto gap-5">

        {/* WEBCAM */}

        <div>

          <label className="block text-slate-400 mb-1.5 text-[11px] font-mono">
            Webcam
          </label>

          {/* No URL input needed for webcam */}

          <button
            onClick={() => {
              // Simulate a refresh to bust cache if needed
              setCamera1Refresh(prev => prev + 1);
            }}
            disabled={camera1Connecting}
            className="w-full mt-3 px-5 py-2.5 bg-cyan-500 hover:bg-cyan-400 disabled:bg-slate-700 disabled:text-slate-950 font-bold rounded-xl text-xs"
          >
            {camera1Connecting
              ? "Refreshing Webcam..."
              : camera1Online
                ? "Reconnect Webcam"
                : "Initialize Webcam"}
          </button>

        </div>

      </div>

      {/* STATUS */}

      <div className="text-center mt-5">

        {cameraSyncStatus && (

          <span
            className={	ext-[11px] font-mono }  
          >
            {cameraSyncStatus.message}
          </span>  

        )}

      </div>

    </div>

    {/* CAMERA GRID */}

    <div className="grid grid-cols-1 gap-6">

      {/* WEBCAM */}

      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 netra-panel">

        <div className="flex items-center justify-between mb-4">

          <div>

            <h3 className="text-white font-bold text-sm">
              Webcam #1
            </h3>

            <p className="text-slate-500 text-[11px] font-mono break-all">
              Integrated Webcam Feed
            </p>

          </div>

          <div
            className={lex items-center gap-2 px-3 py-1.5 rounded-full }  
          >

            <span
              className={w-2.5 h-2.5 rounded-full }  
            />

            <span
              className={text-[11px] font-mono }  
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

          {/* Raw feed from engine (webcam frames without overlay) */}

          {camera1Refresh > 0 ? (

            <img
              key={webcam-raw-}
              src={AI_RAW_FEED_URL}
              alt="Webcam Raw Feed"
              className="w-full h-full object-contain"
              onLoad={handleRawFeedLoad}
              onError={handleRawFeedError}
            />

          ) : (

            <div className="absolute inset-0 flex flex-col items-center justify-center">

              <div className="w-16 h-16 rounded-full bg-slate-900 border border-slate-700 flex items-center justify-center mb-4">

                <span className="text-slate-500 text-2xl">
                  📷
                </span>

              </div>

              <div className="text-slate-300 font-mono text-sm">
                WEBCAM READY
              </div>

              <div className="text-slate-500 text-[11px] mt-1">
                Click Initialize Webcam
              </div>

              </div>

          )}

          {camera1Connecting && (

            <div className="absolute inset-0 flex flex-col items-center justify-center bg-slate-950/75 backdrop-blur-sm">

              <div className="w-10 h-10 rounded-full border-4 border-cyan-500/30 border-t-cyan-400 animate-spin mb-4" />

              <div className="text-cyan-400 font-mono text-xs font-bold">
                INITIALIZING WEBCAM...
              </div>

              <div className="text-slate-500 text-[10px] font-mono mt-2">
                Integrated Webcam
              </div>

            </div>

          )}

          {camera1Refresh > 0 &&
            !camera1Online &&
            !camera1Connecting && (

              <div className="absolute inset-0 flex flex-col items-center justify-center bg-slate-950/80">

                <div className="w-14 h-14 rounded-full bg-red-950 border border-red-800 flex items-center justify-center mb-4">

                  <span className="text-red-500 text-2xl">
                    !
                  </span>

                </div>

                <div className="text-red-400 font-mono text-sm font-bold">
                  WEBCAM OFFLINE
                </div>

                <div className="text-slate-500 text-[11px] mt-2 text-center px-5">
                  Check engine status and webcam permissions.
                </div>

                <button
                  onClick={() => {
                    setCamera1Refresh(prev => prev + 1);
                  }}
                  className="mt-3 px-4 py-1.5 bg-cyan-500 hover:bg-cyan-400 text-slate-950 rounded-lg text-[11px] font-bold"
                >
                  Reinitialize
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
              NETRA-WEBCAM-01
            </span>

          </div>

        </div>

        <div className="grid grid-cols-3 gap-3 mt-4">

          <div className="bg-slate-950 border border-slate-800 rounded-xl p-3 text-center">

            <div className="text-slate-500 text-[10px] font-mono">
              DEVICE
            </div>

            <div className="text-cyan-400 text-xs font-mono mt-1">
              Webcam
            </div>

          </div>

          <div className="bg-slate-950 border border-slate-800 rounded-xl p-3 text-center">

            <div className="text-slate-500 text-[10px] font-mono">
              PORT
            </div>

            <div className="text-cyan-400 text-xs font-mono mt-1">
              0 (Default)
            </div>

          </div>

          <div className="bg-slate-950 border border-slate-800 rounded-xl p-3 text-center">

            <div className="text-slate-500 text-[10px] font-mono">
              STATUS
            </div>

            <div
              className={text-xs font-mono mt-1 }  
            >
              {camera1Online && isApiConnected
                ? "Processing"
                : "Offline"}
            </div>

          </div>

        </div>

      </div>

    </div>

    {/* AI PROCESSED FEED */}

    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 netra-panel">

      <div className="flex items-center justify-between mb-4">

        <div>

          <h3 className="text-white font-bold text-sm">
            AI Processed Feed
          </h3>

          <p className="text-slate-500 text-[11px] font-mono break-all">
            YOLO + pose detection on Webcam Feed
          </p>

        </div>

        <div
          className={flex items-center gap-2 px-3 py-1.5 rounded-full }  
        >

          <span
            className={w-2.5 h-2.5 rounded-full }  
          />

          <span
            className={text-[11px] font-mono }  
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
            key={webcam-ai-}
            src={AI_LIVE_FEED_URL}
            alt="AI Processed Feed"
            className="w-full h-full object-contain"
            onLoad={handleAiFeedLoad}
            onError={handleAiFeedError}
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
              Initialize Webcam to start processing
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
            className={text-xs font-mono mt-1 }  
          >
            {camera1Online && isApiConnected
              ? "Processing"
              : "Offline"}
            </div>

          </div>

        </div>

      </div>

    </div>

  </div>
}'

# Replace the segment
 = .Substring(0, ) +  + .Substring( + 1)

# Write back
Set-Content -Path  -Value  -Encoding UTF8

Write-Host "Livefeed section replaced successfully."
