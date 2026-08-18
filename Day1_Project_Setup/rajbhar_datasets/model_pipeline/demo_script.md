# Project Netra - Final Demo Script Sequences
**Prepared by:** Rajbhar (AI/ML Data)

Demo day ke liye yeh 4 sequences sabse safe aur perfect hain (extreme lighting avoid karni hai):

1. **Sequence 1: Normal Walking (Baseline Check)**
   - **Action:** Ek insaan camera ke samne normal walk karke nikal jayega.
   - **Expected Output:** Normal. No alert. System stable rahega.

2. **Sequence 2: Clear SOS Gesture (Threat Check)**
   - **Action:** Insaan ruk kar proper roshni (good lighting) mein SOS hand gesture (ungliyan fold karna) dikhayega.
   - **Expected Output:** THREAT DETECTED. Cloud sync trigger hoga aur Telegram par alert jayega.

3. **Sequence 3: Group Presence / Talking (False Positive Check)**
   - **Action:** Do log camera ke samne aakar normal hath hila kar baat karenge.
   - **Expected Output:** Normal. AI confuse nahi hoga aur false positive alert nahi jayega.

4. **Sequence 4: SOS Gesture While Moving (Dynamic Check)**
   - **Action:** Insaan chalte-chalte SOS signal dega. 
   - **Expected Output:** THREAT DETECTED. Model motion ke beech mein bhi accurate detection karega.

**Note for Presenter:** Demo ke waqt ensure karein ki room mein sufficient lighting ho, kyunki low light/glare test fail ho chuke hain.