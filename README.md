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

## reading_mode.py

Responsibilities:

- Check camera frames for a large document-like rectangle (paper, menu, flyer)
- Straighten (perspective-correct) the page when the user presses Scan Document
- Run OCR (EasyOCR) to extract the text
- Keep the text in memory only, for later use (get_document_context())

Used by: GUI2.py

Main role:
Reading Mode (see the Reading Mode section below)

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

## 5. Install OCR for Reading Mode (EasyOCR)
pip install easyocr==1.7.2 --no-deps

Why --no-deps: EasyOCR normally also installs opencv-python-headless, which
overwrites our normal opencv-python and can break camera windows (cv2.imshow in cam.py).
The small libraries EasyOCR needs (scikit-image, shapely, pyclipper, python-bidi, ninja)
are already installed by requirements.txt in step 4.

The first scan downloads the OCR model files (about 100 MB) to ~/.EasyOCR
in your home folder, NOT into the project folder.

If camera windows ever break because opencv-python-headless got installed anyway:
pip uninstall -y opencv-python-headless opencv-python
pip install opencv-python==4.13.0.92

---

# Running the Program

Program execute by running: python main.py

GUI version (camera + YOLO + narration + Reading Mode): python GUI2.py

---

# Reading Mode (V1)

Reading Mode helps the user read paper documents such as a restaurant menu, a printed page,
a flyer, or a sign with a lot of text. It runs inside GUI2.py while normal YOLO detection
keeps working.

How it works:

Camera
↓
Every 0.5s OpenCV checks for a large rectangle that looks like a page
↓
Page found → green outline, "Scan Document" button turns on,
narration says "Document detected. Scan available." (once, not repeatedly)
↓
User presses Scan Document (scanning is never automatic)
↓
One frame is captured, the page is straightened, OCR reads the text
↓
The text is read aloud and kept in memory
↓
The captured image is thrown away

Storage rules:

- Nothing is saved to disk (no screenshots, no text files)
- Only one document is kept; a new scan replaces the old one
- The text expires after 10 minutes, or when the program is closed
- Future code (for example an LLM answering questions about the menu)
  can get the text with reading_mode.get_document_context()

Speech: Reading Mode uses the existing narration2.py. Its messages use
speak(..., priority=True) so the scan result is not skipped by the normal
2 second object narration cooldown.

Current limits (V1): needs a page with visible edges against a contrasting background,
English only, OCR runs on the CPU (a few seconds per scan), and long documents are
read aloud in full.

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