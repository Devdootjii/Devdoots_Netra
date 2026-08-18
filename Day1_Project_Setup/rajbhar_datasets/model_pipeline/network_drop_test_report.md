# Day 5 Task 2 - Network Drop Test Report
**Tester:** Rajbhar (AI/ML Data)

## Test Scenario:
* **Action:** System live chalte hue IP camera (phone) ka Wi-Fi band kiya gaya aur 10 second baad dobara on kiya gaya.

## Observation & Recovery Time:
* **Wi-Fi Off:** Video feed instantly freeze ho gayi. UI par Aryan ka "Camera Offline" indicator successfully show hua.
* **Wi-Fi On (After 10 seconds):** 
* **Recovery Time:** System ko auto-recover karne aur wapas naye frames lane mein lagbhag **8-12 seconds** ka lag aaya. 
* **Issue:** OpenCV purane buffer kiye hue frames process kar raha tha, jiski wajah se live feed delay ho gayi.

**Conclusion:** 
System auto-recover kar raha hai, lekin buffer latency bohot zyada hai. DS team ko OpenCV mein `cv2.CAP_PROP_BUFFERSIZE = 1` set karke is lag ko zero karna hoga.