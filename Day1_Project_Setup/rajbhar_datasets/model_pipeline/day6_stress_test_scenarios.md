# Day 6 - Full System Pipeline Stress Test Scenarios
**Prepared by:** Rajbhar (AI/ML Data)

Team, Day 6 ke stress test ke liye humein in 5 physical scenarios ko test karna hai:

* **Scenario 1:** Cam 1 par normal walking, Cam 2 par SOS. (Check: System should only trigger alert for Cam 2).
* **Scenario 2:** Cam 1 par low light mein SOS. (Check: Verify if the AI model drops frames or accurately detects the gesture in poor visibility).
* **Scenario 3:** Cam 1 aur Cam 2 dono par ek sath SOS gesture. (Check: Backend concurrency and rate-limiting logic. System should not crash under simultaneous alerts).
* **Scenario 4:** Cam 2 par bright light/glare ke sath normal walking. (Check: False positive rate. Ensure glare doesn't trick the AI into sending a fake alert).
* **Scenario 5:** Cam 1 par normal group presence (2-3 log baat kar rahe hain) aur 5 meter ki doori par Cam 2 mein SOS. (Check: Camera clarity and distance latency under full load).