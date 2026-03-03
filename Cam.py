import cv2

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