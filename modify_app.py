import re

def main():
    filename = 'App.jsx'
    with open(filename, 'r') as f:
        content = f.read()
    
    # 1. Remove DROIDCAM_URL and DROIDCAM_VIDEO_URL constants
    content = re.sub(r'const DROIDCAM_URL = "http://192\.168\.1\.2:4747";', '', content)
    content = re.sub(r'const DROIDCAM_VIDEO_URL = "http://192\.168\.1\.2:4747/video";', '', content)
    
    # 2. Change the comment block
    content = content.replace('// =========================================================\n  // DROIDCAM / CAMERA STATE\n  // =========================================================', '// =========================================================\n  // WEBCAM / CAMERA STATE\n  // =========================================================')
    
    # 3. Change the useState line for camera1Url
    content = re.sub(r'const\s+\[camera1Url,\s*setCamera1Url\]\s*=\s*useState\([^)]*\)', 'const [camera1Url, setCamera1Url] = useState("")', content)
    
    # 4. Remove the normalizeCameraUrl function
    content = re.sub(r'const normalizeCameraUrl = \(url\) => \{[\s\S]*?\}', '', content)
    
    # 5. Remove the connectCamera1 function
    content = re.sub(r'const connectCamera1 = \(\) => \{[\s\S]*?\}', '', content)
    
    # 6. Remove the handleCamera1UrlChange function
    content = re.sub(r'const handleCamera1UrlChange = \(value\) => \{[\s\S]*?\}', '', content)
    
    # 7. Update messages in handler functions
    content = content.replace('"DroidCam Camera #1 is LIVE."', '"Webcam feed is LIVE."')
    content = content.replace('"DroidCam stream failed. Make sure http://192\.168\.1\.2:4747 is reachable."', '"Webcam stream failed. Check engine status."')
    content = content.replace('"AI engine is processing Camera #1 feed."', '"AI engine is processing Webcam feed."')
    
    # 8. Replace the livefeed section
    start_marker = '{/* LIVE FEED / DROIDCAM */}'
    end_marker = '{/* SETTINGS */}'
    start_index = content.find(start_marker)
    end_index = content.find(end_marker)
    if start_index != -1 and end_index != -1:
        new_start_marker = '{/* LIVE FEED / WEBCAM */}'
        new_livefeed = '''{activePage === "livefeed" && (
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
              className={	ext-xs font-mono mt-1 }  
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
          className={lex items-center gap-2 px-3 py-1.5 rounded-full }  
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
            className={	ext-xs font-mono mt-1 }  
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
)}'''
        # Replace the section from start_index to end_index with newStartMarker + newline + newLivefeed + newline
        content = content[:start_index] + new_start_marker + '\n' + new_livefeed + '\n' + content[end_index:]
    else:
        print("Could not find livefeed section markers")
        return
    
    # 9. Update the YOLO detail section pipeline diagram: change "DroidCam" to "Webcam"
    content = content.replace('<div>DroidCam</div>', '<div>Webcam</div>')
    
    # 10. Update the initial alert log message
    content = content.replace('SOS Signal Hand Gesture Detected in Camera #1', 
                              'SOS Signal Hand Gesture Detected in Webcam #1')
    
    with open(filename, 'w') as f:
        f.write(content)
    
    print("File modified successfully.")

if __name__ == '__main__':
    main()
