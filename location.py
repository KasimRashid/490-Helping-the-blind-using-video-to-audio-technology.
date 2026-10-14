"""
location.py - tells the user WHERE a detected item is.

Takes YOLO results and turns each bounding box into a spoken-friendly
position such as "person on your left, close" or "chair ahead".

Assumes the camera faces the same way the user does (wearable / held
forward), so left in the image = left of the user.

Usage with the existing code (cam.py / GUI2.py):

    from location import describe_locations, make_location_sentence, where_is

    results = model(frame, verbose=False)
    h, w = frame.shape[:2]
    items = describe_locations(results[0], model.names, w, h)
    message = make_location_sentence(items)       # "person on your left, close; chair ahead"
    speak(message)

    where_is("chair", items)                       # "chair ahead, nearby" or "No chair found"
"""

MAX_ITEMS = 4  # max objects per sentence, so narration stays short

# Fraction of frame width/height used to split into thirds
LEFT_LIMIT = 1 / 3
RIGHT_LIMIT = 2 / 3
TOP_LIMIT = 1 / 3
BOTTOM_LIMIT = 2 / 3

# Box area / frame area -> rough distance. Only an estimate:
# big objects (a car) and small ones (a cup) look different at the same distance.
CLOSE_RATIO = 0.25
NEARBY_RATIO = 0.05


def get_horizontal(cx, width):
    """Left / ahead / right based on the box center."""
    ratio = cx / width
    if ratio < LEFT_LIMIT:
        return "on your left"
    if ratio > RIGHT_LIMIT:
        return "on your right"
    return "ahead"


def get_vertical(cy, height):
    """High / low / level based on the box center."""
    ratio = cy / height
    if ratio < TOP_LIMIT:
        return "high"
    if ratio > BOTTOM_LIMIT:
        return "low"
    return ""


def get_distance(box_area, frame_area):
    """Rough distance word from how much of the frame the box fills."""
    ratio = box_area / frame_area
    if ratio >= CLOSE_RATIO:
        return "close"
    if ratio >= NEARBY_RATIO:
        return "nearby"
    return "far"


def describe_locations(result, names, width, height):
    """
    Build a list of dicts, one per detected object, nearest (largest) first.
    result = results[0] from model(frame); names = model.names.
    """
    items = []
    frame_area = float(width * height)

    for box in result.boxes:
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        area = max(0.0, x2 - x1) * max(0.0, y2 - y1)
        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2

        items.append({
            "label": names[int(box.cls[0])],
            "horizontal": get_horizontal(cx, width),
            "vertical": get_vertical(cy, height),
            "distance": get_distance(area, frame_area),
            "area": area,
        })

    items.sort(key=lambda i: i["area"], reverse=True)
    return items


def _phrase(item):
    """e.g. 'person on your left, close'."""
    parts = [item["horizontal"]]
    if item["vertical"]:
        parts.append(item["vertical"])
    parts.append(item["distance"])
    return f"{item['label']} " + ", ".join(parts)


def make_location_sentence(items):
    """Combine items into one sentence. Duplicate phrases are counted."""
    if not items:
        return "No objects detected"

    counts = {}
    for item in items[:MAX_ITEMS]:
        phrase = _phrase(item)
        counts[phrase] = counts.get(phrase, 0) + 1

    phrases = []
    for phrase, n in counts.items():
        phrases.append(phrase if n == 1 else f"{n} x {phrase}")

    return "; ".join(phrases)


def where_is(target, items):
    """Answer 'where is the <target>?' using the list from describe_locations."""
    target = target.lower().strip()
    matches = [i for i in items if i["label"].lower() == target]

    if not matches:
        return f"No {target} found"

    return "; ".join(_phrase(m) for m in matches[:MAX_ITEMS])


# Quick self-test with fake boxes (no camera or YOLO needed): python location.py
if __name__ == "__main__":
    class _Box:
        def __init__(self, cls, xyxy):
            self.cls = [cls]
            self.xyxy = [type("T", (), {"tolist": lambda s, v=xyxy: v})()]

    class _Result:
        boxes = [
            _Box(0, [20, 100, 250, 450]),    # person, left, big
            _Box(1, [280, 150, 360, 230]),   # chair, center, small
            _Box(2, [500, 10, 540, 40]),     # phone, right, high, far
        ]

    names = {0: "person", 1: "chair", 2: "phone"}
    found = describe_locations(_Result(), names, 640, 480)
    print(make_location_sentence(found))
    print(where_is("chair", found))
    print(where_is("dog", found))