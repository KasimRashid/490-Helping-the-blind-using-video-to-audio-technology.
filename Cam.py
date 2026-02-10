import cv2
# run with 
# C:\Users\krash\miniconda3\python.exe C:\Users\krash\OneDrive\Desktop\CPSC490\Cam.py

stream = cv2.VideoCapture(0)

if not stream.isOpened():
    print("No stream")
    exit()

while(True):
    ret, frame = stream.read()
    if not ret:
        print("not more stream")
        break
    cv2.imshow("WebCam", frame)
    if cv2.waitKey(1) == ord('q'):
        break
stream.release()
cv2.destroyAllwindows() 
