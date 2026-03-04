import cv2

# import YOLO from ultralytics
from ultralytics import YOLO


# load simplets YOLO model yolo26n to test if it works
model = YOLO("yolo26n.pt")


stream = cv2.VideoCapture(0)

if not stream.isOpened():
    print("No stream")
    exit()

while True:
    ret, frame = stream.read()

    if not ret:
        print("No more stream")
        break


    # run YOLO detection on frame
    results = model(frame)


    # draw detection results on frame
    annotated_frame = results[0].plot()


    # show annotated frame instead of raw frame
    cv2.imshow("YOLO Camera Detection", annotated_frame)


    if cv2.waitKey(1) == ord('q'):
        break


stream.release()

# fixed error letter w must be capitalized
cv2.destroyAllWindows()