"""
depth.py - EXPERIMENTAL relative depth for detected objects (Depth Anything V2 Small).

Depth Anything V2 gives *relative* depth only (no meters/feet). Each frame's depth
map is normalized to 0..1 (1 = nearest part of THAT frame), so "close / nearby / far"
means "close compared to the rest of the scene", not a verified physical distance.

Usage (same frame for YOLO and depth):

    from depth import DepthEstimator

    depth = DepthEstimator()                       # loads model; raises if it can't
    results = model(frame, verbose=False)
    lines = depth.describe(frame, results[0], model.names)
    # ["person | Left | Nearby", "chair | Center | Close"]

    items = depth.estimate_objects(frame, results[0], model.names)   # list of dicts
"""

import time

import cv2
import numpy as np
import torch

MODEL_ID = "depth-anything/Depth-Anything-V2-Small-hf"

# Normalized relative depth (0 = far side of scene, 1 = nearest) -> category.
CLOSE_THRESHOLD = 0.66
NEARBY_THRESHOLD = 0.33

# Only the central part of each box is sampled, to avoid background at the edges.
BOX_CORE = 0.5
# Percentile (not median) of that region: the object is the nearest thing in its own box, so
# a higher percentile ignores background showing through thin or non-rectangular objects.
BOX_PERCENTILE = 75

INPUT_SIZE = 518  # model's native size (multiple of 14); smaller = faster, less accurate


def horizontal_position(cx, width):
    """Left / Center / Right thirds of the frame."""
    ratio = cx / width
    if ratio < 1 / 3:
        return "Left"
    if ratio > 2 / 3:
        return "Right"
    return "Center"


def depth_category(score):
    """Relative score (0..1, higher = nearer) -> close / nearby / far."""
    if score >= CLOSE_THRESHOLD:
        return "close"
    if score >= NEARBY_THRESHOLD:
        return "nearby"
    return "far"


class DepthEstimator:
    def __init__(self, model_id=MODEL_ID):
        # Imported here so the rest of the app never needs transformers unless depth is used.
        from transformers import AutoImageProcessor, AutoModelForDepthEstimation

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.processor = AutoImageProcessor.from_pretrained(model_id)
        self.model = AutoModelForDepthEstimation.from_pretrained(model_id).to(self.device).eval()
        self.last_ms = 0.0  # time of the last estimate_map call, for performance checks

    @torch.inference_mode()
    def estimate_map(self, frame_bgr):
        """Return a float32 map in 0..1 (1 = nearest), sized INPUT_SIZE-ish, not the frame size."""
        start = time.time()
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        inputs = self.processor(
            images=rgb, return_tensors="pt",
            size={"height": INPUT_SIZE, "width": INPUT_SIZE}, keep_aspect_ratio=False,
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        depth = self.model(**inputs).predicted_depth[0].float().cpu().numpy()  # larger = nearer

        lo, hi = np.percentile(depth, [2, 98])  # percentiles so outliers don't squash the range
        depth = np.clip((depth - lo) / max(hi - lo, 1e-6), 0.0, 1.0).astype(np.float32)
        self.last_ms = (time.time() - start) * 1000
        return depth

    @staticmethod
    def score_box(depth_map, xyxy, frame_w, frame_h):
        """Relative depth (0..1) of the central part of a YOLO box (frame coordinates)."""
        mh, mw = depth_map.shape
        x1, y1, x2, y2 = xyxy
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        hw, hh = (x2 - x1) * BOX_CORE / 2, (y2 - y1) * BOX_CORE / 2
        # scale frame coordinates to depth-map coordinates
        sx, sy = mw / frame_w, mh / frame_h
        c1, c2 = int(max(0, (cx - hw) * sx)), int(min(mw, np.ceil((cx + hw) * sx)))
        r1, r2 = int(max(0, (cy - hh) * sy)), int(min(mh, np.ceil((cy + hh) * sy)))
        if c2 <= c1 or r2 <= r1:  # degenerate box
            c1, c2 = min(max(int(cx * sx), 0), mw - 1), min(max(int(cx * sx), 0), mw - 1) + 1
            r1, r2 = min(max(int(cy * sy), 0), mh - 1), min(max(int(cy * sy), 0), mh - 1) + 1
        return float(np.percentile(depth_map[r1:r2, c1:c2], BOX_PERCENTILE))

    def estimate_objects(self, frame_bgr, result, names):
        """One dict per YOLO box, in the same order as result.boxes."""
        h, w = frame_bgr.shape[:2]
        depth_map = self.estimate_map(frame_bgr)
        items = []
        for box in result.boxes:
            xyxy = box.xyxy[0].tolist()
            score = self.score_box(depth_map, xyxy, w, h)
            items.append({
                "label": names[int(box.cls[0])],
                "horizontal": horizontal_position((xyxy[0] + xyxy[2]) / 2, w),
                "depth": depth_category(score),
                "score": score,  # relative, NOT a distance
            })
        return items

    def describe(self, frame_bgr, result, names):
        """Display strings like 'Person | Left | Nearby', nearest first."""
        items = self.estimate_objects(frame_bgr, result, names)
        items.sort(key=lambda i: i["score"], reverse=True)
        return [f"{i['label'].capitalize()} | {i['horizontal']} | {i['depth'].capitalize()}" for i in items]


# Self-test: python depth.py [image_path]   (uses webcam frame if no path is given)
if __name__ == "__main__":
    import sys
    from ultralytics import YOLO

    frame = cv2.imread(sys.argv[1]) if len(sys.argv) > 1 else None
    if frame is None:
        cam = cv2.VideoCapture(0)
        ok, frame = cam.read()
        cam.release()
        if not ok:
            sys.exit("No image path given and no camera frame available")

    yolo = YOLO("yolo26n.pt")
    est = DepthEstimator()
    res = yolo(frame, verbose=False)[0]
    for line in est.describe(frame, res, yolo.names):
        print(line)
    print(f"depth time: {est.last_ms:.0f} ms on {est.device}")
