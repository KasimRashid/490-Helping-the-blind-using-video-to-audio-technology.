# 490-Helping-the-visually-disabled-use-video-to-audio-technology

# What is YOLO Was

YOLO26 (You Only Look Once) the core object detection system.

For testing yolo26n is used but there are more powerful versions. just used this version to test if it works.

YOLO is a real-time computer vision model developed by Ultralytics that can detect multiple objects in a single image frame.

What it can offer:

- Real-time object detection
- High detection accuracy
- and it runs locally on computer


detect objects like:
- person
- chair
- car
- phone
- laptop
- bottle
- dog

---

# Current System Architecture

main.py
│
├── cam.py → camera input
│
├── detection.py →  object detection
│
└── geometry.py → spatial calculations

---

# Module Responsibilities (work in progress feel free to add or edit)

## main.py

Main program controller.

Responsibilities (work in progress):

- Start the application
- Coordinate camera and detection modules
- Manage narration logic

---

## cam.py

Responsibilities (work in progress):

- Open webcam using OpenCV
- Capture frames from the camera
- Send frames to the detection system

Main role:
frame capture

---

## detection.py

Responsibilities (work in progress):

- Run the YOLO model
- Detect objects inside each frame
- Return detected object labels

Potential Example output:
["person", "chair", "laptop"]
Detected object #: Laptop: color red
Detected object #: Pencil: color yellow

Main role:
use yolo26 version to map objects to labels

---

## geometry.py

Responsibilities (work in progress):

- Analyze object location
- Determine relative position to the user

Possible examples of outputs can be:
person → left side
chair → center
Distance of person: 20cm
Height: 2 in

Main role: 
we can calculate the position of object relative to the distance from the camera

---

# Current System

Currently the system performs the following:
cam.py --> YOLO object detection --> display detected objects

So that means Yolo works with the following:
- Camera input works
- YOLO detection works
- Real-time processing is possible

---

# Installation Instructions

## 1. Clone the repository command
git clone https://github.com/KasimRashid/490-Helping-the-blind-using-video-to-audio-technology..git
cd 490-Helping-the-blind-using-video-to-audio-technology.

---

## 2. Create a virtual environment (so we have same python environment)
python3 -m venv venv

---

## 3. Activate the virtual environment

### Mac / Linux
source venv/bin/activate

### Windows
venv\Scripts\activate

---

## 4. Install required libraries (so we have same packages)
pip install -r requirements.txt

This installs all required libraries for using yolo including:

- Ultralytics YOLO
- OpenCV
- PyTorch
- NumPy

---

# Running the Program

Program execute by running: python main.py

---

# Future Development Plans (work in progress)

## 1. Audio Narration

Detected objects will be converted into speech feedback.

Example:
Person detected ahead.
Chair detected on the right.

Possible implementation: pyttsx3 text to speech 

---

## 2. Object Position Detection

Feature that we read data that we have from detection and geomotry functions

Example outputs:
person left
chair center 20 cm
Red table right 

Example narration:
Chair is center 20 cm from your position. Red table right.
Person in front of you.

---

## 3. Picture mode???

We can still use an api but we should limit how it is used. An example where an api can be useful is when user presses describe button the camera captures the image and a api like Google or Azure can analyzes scene and we can use python to narrate the description of scene back to user. So basically we use the speed of the api to get the description then we use python to narrate in a timely manner.

Example narration:
A person takes a picture in the park
"You are in a park with a group of people talking, walking, biking, and the sky is clear blue."


---