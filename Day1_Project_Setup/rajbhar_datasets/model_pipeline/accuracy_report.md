# AI Model Live Metric Tracking - Day 3 Task 2
**Prepared by:** Rajbhar (AI/ML Data)

**Google Sheet Link:** [https://docs.google.com/spreadsheets/d/15WGttgk4RBa7wRY35XC0MW7r_pBHYS2sU933iHmiBrk/edit?usp=sharing]

## False Positives & Accuracy Report (Real Dataset):

1. **Video:** `hand_signal_for_help(720p).mp4` (Abnormal)
   - **Action:** Clear SOS hand signal.
   - **AI Result:** SOS Detected Successfully (Accurate).
   - **False Positive:** No.

2. **Video:** `27268-363287559_medium.mp4` (Normal)
   - **Action:** Normal hand gestures while talking.
   - **AI Result:** AI confused normal movement with SOS.
   - **False Positive:** YES (Needs strictness optimization by Balram/Ritesh).

3. **Video:** `She’s_Asking_for_Help..._Did_You...` (Abnormal)
   - **Action:** SOS signal in vertical shorts format.
   - **AI Result:** AI missed the signal.
   - **False Negative:** YES (MediaPipe needs tuning for vertical videos).

4. **Video:** `31822-389009323_medium.mp4` (Normal)
   - **Action:** Regular normal activity.
   - **AI Result:** Normal (Accurate).
   - **Performance Issue:** FPS dropped to 18. Frame skipping logic required to maintain minimum 20-25 FPS.

**Conclusion:** System is detecting most SOS signals correctly, but there are issues with false positives on normal hand movements. AI team also needs to optimize FPS with frame skipping.
