import cv2

# import YOLO from ultralytics
from ultralytics import YOLO
#from narration.py
from narration import make_sentence, speak

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
    results = model(frame, verbose=False)
    labels = []

    #for narration
    for box in results[0].boxes:
        cls_id = int(box.cls[0])
        label = model.names[cls_id]
        labels.append(label)
    #for debugging
    print("Labels found:", labels)

    message = make_sentence(labels)
    speak(message)

    # draw detection results on frame
    annotated_frame = results[0].plot()


    # show annotated frame instead of raw frame
    cv2.imshow("YOLO Camera Detection", annotated_frame)


    if cv2.waitKey(1) == ord('q'):
        break


stream.release()

# fixed error letter w must be capitalized
cv2.destroyAllWindows()