# Day 5 Task 1 - IP Camera Distance Testing
**Tester:** Rajbhar (AI/ML Data)
**Camera Used:** Smartphone IP Webcam (via Wi-Fi)

## Test Results:
1. **2 Meter Distance:**
   - **Action:** Performed SOS hand gesture 2 meters away from the smartphone camera.
   - **Result:** AI detected the SOS signal almost instantly. Hand landmarks were clear despite minor Wi-Fi latency.
   - **Accuracy:** 95% (Pass)
   
2. **5 Meter Distance:**
   - **Action:** Performed SOS hand gesture 5 meters away.
   - **Result:** System struggled. Phone camera's digital zoom and Wi-Fi frame dropping (latency) made the hand look blurry. MediaPipe lost tracking of fingers.
   - **Accuracy:** 30% (Fail)

**Conclusion:** 
IP Camera setup is working well for close range (up to 2-3 meters). However, for 5 meters or more, the AI is failing due to blurry frames and network latency. DS Team needs to look into frame buffering optimization to fix this.