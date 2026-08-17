# Day 4 Task 2 - Edge Case Testing Report
**Tester:** Rajbhar (AI/ML Data)

## Lighting Conditions Test Results:

1. **Low Light (Dark Room):**
   - **Result:** AI FAILED to detect the SOS signal.
   - **Reason:** Camera feed was too dark and noisy. MediaPipe could not extract hand landmarks.

2. **Bright Light (Flashlight/Glare):**
   - **Result:** AI FAILED to detect the SOS signal.
   - **Reason:** High exposure and glare washed out the hand features, blinding the detection model.

**Conclusion:** 
The current model cannot handle extreme lighting. The AI pipeline needs a preprocessing step (like OpenCV brightness/contrast normalization or Histogram Equalization) before passing the frames to the detection model.