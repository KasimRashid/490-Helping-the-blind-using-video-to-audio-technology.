# 490 - Helping the visually disabled use video-to-audio technology

Our CPSC 490 project. The app uses a webcam to detect objects, works out roughly where they are, and reads that out loud. Everything runs locally.

The main application is `GUI2.py`.

## How it works

For each camera frame:

1. **YOLO26** (`yolo26n.pt`, the nano model) detects objects and gives a label and bounding box for each one.
2. **`location.py`** turns each box into a phrase like `person on your left, nearby`. Direction comes from which third of the frame the box center is in (left, ahead, right), plus `high` or `low` for the top or bottom third. The distance word comes from box size: 25% of the frame or more is `close`, 5% or more is `nearby`, smaller is `far`.
3. **`narration2.py`** speaks that sentence offline with `pyttsx3`. It won't repeat the same sentence within 2 seconds.

The GUI shows the camera feed with YOLO boxes, the current narration sentence, the detected objects, and these controls: Pause/Resume, Narration on/off, Voice Speed, Male/Female voice, Depth on/off, and Quit.

## Depth estimation (this branch)

The `feature/depth-estimation` branch adds `depth.py`, which uses **Depth Anything V2 Small** to estimate depth for every pixel of the same frame YOLO used. For each YOLO box it samples the middle of the box, compares it to the rest of the scene, and labels the object `Close`, `Nearby`, or `Far`.

Depth is off by default. Click **DEPTH: OFF** to turn it on. The first time, the model downloads (needs internet once) and the button shows `LOADING...` while the camera keeps running. When it's on, the Detected panel shows one line per object, nearest first:

```
Person | Left | Nearby
Chair | Center | Close
```

The same lines print in the terminal when they change. If the model fails to load or run, the app prints a `[DEPTH]` message and keeps going with YOLO only.

Right now depth is display-only. The spoken narration still uses the size-based distance from `location.py`, so the two can disagree. For example, a small object right in front of the camera may be spoken as `far` while depth shows `Close`.

Depth Anything V2 gives relative depth, not real distances. The labels only mean "closer or farther compared to the rest of this frame," so if everything is far away, the nearest object can still show as `Close`. The thresholds were picked by hand, so labels can flicker near the cutoffs.

## Setup

Requires Python 3.11+ (tested on 3.12) and a webcam.

```
git clone https://github.com/KasimRashid/490-Helping-the-blind-using-video-to-audio-technology..git
cd 490-Helping-the-blind-using-video-to-audio-technology.
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pip install pyttsx3
```

On Mac/Linux, activate with `source venv/bin/activate` instead.

`pyttsx3` is needed by `narration2.py` but isn't in `requirements.txt` yet. This branch adds `transformers` to `requirements.txt` for depth estimation.

Run the app:

```
python GUI2.py
```

### Optional: NVIDIA GPU

`requirements.txt` installs CPU-only PyTorch. YOLO runs fine on CPU, but depth is slow (about 3-4 updates per second in our tests). With an NVIDIA GPU, install the CUDA build:

```
pip install --force-reinstall --no-deps torch==2.10.0 torchvision==0.25.0 --index-url https://download.pytorch.org/whl/cu128
```

`python -c "import torch; print(torch.cuda.is_available())"` should print `True`. No code changes are needed since the app uses the GPU when it's available and falls back to CPU otherwise. On an RTX 3060 Ti we got about 20 depth updates per second with narration off.

## Main files

| File | Purpose | Status |
|---|---|---|
| `GUI2.py` | Main app: camera, YOLO, GUI, narration | Existing, DEPTH toggle added on this branch |
| `location.py` | Direction and size-based distance phrases from YOLO boxes | Existing |
| `narration2.py` | Offline text-to-speech with `pyttsx3` | Existing |
| `yolo26n.pt` | YOLO26 nano model weights | Existing |
| `depth.py` | Depth Anything V2 Small relative depth labels | New on this branch |

`depth.py` can also be tested on its own: `python depth.py path/to/image.jpg` (or no argument to use the webcam).

Older files like `GUI.py`, `cam.py`, and `main.py` are earlier versions and prototypes that `GUI2.py` doesn't use.
