import cv2

stream = cv2.VideoCapture(0)

if not stream.isOpened():
    print("No stream")
    exit()

while True:
    ret, frame = stream.read()

    if not ret:
        print("No more stream")
        break

    cv2.imshow("WebCam", frame)

    if cv2.waitKey(1) == ord('q'):
        break

stream.release()

# fixed error letter w must be capitalized
cv2.destroyAllWindows()