---
tags: [user, face_landmark_data_collection_system, face-recognition, computer-vision, claude, ai-conversation]
---



# Face landmark data collection system

**Created:** 2026-05-05 14:41  
**Updated:** 2026-05-05 14:41

> Part of [[Claude Conversations Hub]]

---

### 🧑 CJ · 2026-05-05 14:41

```python
import cv2
import csv
import os
import facetracking as ft

GESTURES = ["cj" ]

KEY_MAP = {
    "1": 0
}

SAVE_FILE = "1gesture_data.csv"

cap = cv2.VideoCapture(0)
detector = ft.FaceTracking()

# 84 features: 42 per hand (x0,y0...x20,y20) for left then right
if not os.path.exists(SAVE_FILE):
    with open(SAVE_FILE, "w", newline="") as f:
        header = [f"{axis}{i}" for i in range(21) for axis in ("x", "y")] + ["label"]

        csv.writer(f).writerow(header)

def get_counts():
    counts = {g: 0 for g in GESTURES}
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                label = row.get("label", "")
                if label in counts:
                    counts[label] += 1
    return counts

def draw_counts(img, counts, active_label=None):
    h, w, _ = img.shape
    panel_x = w - 220
    cv2.circle(img, (panel_x - 10, 0), (w, len(GESTURES) * 32 + 20), (0, 0, 0), -1)
    for i, gesture in enumerate(GESTURES):
        count = counts[gesture]
        y = 28 + i * 32
        color = (0, 255, 255) if gesture == active_label else (200, 200, 200)
        bar_width = min(int((count / 150) * 160), 160)
        bar_color = (0, 180, 80) if gesture == active_label else (60, 60, 60)
        cv2.circle(img, (panel_x, y - 16), (panel_x + bar_width, y + 4), bar_color, -1)
        cv2.putText(img, f"{gesture}: {count}", (panel_x, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
    return img

def extract(lm_list, w, h):
    """Normalize one hand's landmarks relative to wrist. Returns 42 floats."""
    if not lm_list:
        return [0.0] * 42  # pad missing hand with zeros
    row = []
    for idx, cx, cy in lm_list:
        row.append(cx / w)
        row.append(cy / h)
    wrist_x, wrist_y = row[0], row[1]
    return [v - (wrist_x if i % 2 == 0 else wrist_y) for i, v in enumerate(row)]

print("Keys: 1=fist  2=one  3=two  4=three  f=four  p=palm  u=thumbs up  d=thumbs down  b=peak")
print("ESC to quit")

counts = get_counts()
active_label = None

while True:
    success, img = cap.read()
    if not success:
        continue

    img = cv2.flip(img, 1)
    img = detector.findFaces(img)

    lm_list_0 = detector.findPosition(img, face_no=0)

    key = cv2.waitKey(1) & 0xFF
    if key == 27:
        break

    key_char = chr(key) if key < 128 else ""

    if key_char in KEY_MAP and (lm_list_0 ):
        active_label = GESTURES[KEY_MAP[key_char]]
        h, w, _ = img.shape

        row = extract(lm_list_0, w, h)
        row.append(active_label)

        with open(SAVE_FILE, "a", newline="") as f:
            csv.writer(f).writerow(row)

        counts[active_label] += 1

        cv2.putText(img, f"SAVED: {active_label}", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

    # Show how many hands are detected
    face_count = detector.getfaceCount()
    cv2.putText(img, f"faces: {face_count}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    img = draw_counts(img, counts, active_label)
    cv2.imshow("face Collector", img)

cap.release()
cv2.destroyAllWindows()
```


```python
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import os
import urllib.request
import time

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['GLOG_minloglevel'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

MODEL_PATH = os.path.join(os.path.dirname(__file__), 'face_landmarker.task')
if not os.path.exists(MODEL_PATH):
    print("Downloading face_landmarker.task ...")
    url = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/latest/face_landmarker.task"
    urllib.request.urlretrieve(url, MODEL_PATH)

# Face mesh connections for drawing
CONNECTIONS = [
    (10,338),(338,297),(297,332),(332,284),(284,251),(251,389),(389,356),
    (356,454),(454,323),(323,361),(361,288),(288,397),(397,365),(365,379),
    (379,378),(378,400),(400,377),(377,152),(152,148),(148,176),(176,149),
    (149,150),(150,136),(136,172),(172,58),(58,132),(132,93),(93,234),
    (234,127),(127,162),(162,21),(21,54),(54,103),(103,67),(67,109),(109,10)
]


class FaceTracking:

    def __init__(self):
        BaseOptions        = python.BaseOptions
        FaceLandmarker     = vision.FaceLandmarker
        FaceLandmarkerOpts = vision.FaceLandmarkerOptions
        VisionRunningMode  = vision.RunningMode

        options = FaceLandmarkerOpts(
            base_options                  = BaseOptions(model_asset_path=MODEL_PATH),
            running_mode                  = VisionRunningMode.VIDEO,
            num_faces                     = 1,
            min_face_detection_confidence = 0.5,
            min_face_presence_confidence  = 0.5,
            min_tracking_confidence       = 0.5,
        )

        self.landmarker = FaceLandmarker.create_from_options(options)
        self.results    = None

    def findFaces(self, img, draw=True):
        rgb   = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        ts_ms = int(time.time() * 1000)

        self.results = self.landmarker.detect_for_video(image, ts_ms)

        if draw and self.results.face_landmarks:
            h, w, _ = img.shape                                     # fixed: was "h , w _"
            for face_landmarks in self.results.face_landmarks:      # fixed: was self.last_results
                pts = [(int(lm.x * w), int(lm.y * h))              # fixed: was "int(lm * w)"
                       for lm in face_landmarks]

                # Draw connections
                for a, b in CONNECTIONS:
                    cv2.line(img, pts[a], pts[b], (0, 255, 0), 1)
                # Draw landmark dots
                for x, y in pts:
                    cv2.circle(img, (x, y), 1, (0, 200, 255), -1)

            return img    
    def findPosition(self, img, face_no=0):
        lm_list = []
        if self.results and self.results.face_landmarks:        # fixed: self.last_results → self.results
            if face_no < len(self.results.face_landmarks):      # fixed: self.last_results → self.results
                h, w, _ = img.shape
                for idx, lm in enumerate(self.results.face_landmarks[face_no]):   # fixed
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    lm_list.append([idx, cx, cy])
        return lm_list

    def getFaceCount(self):                                     # renamed from getHandCount
        if self.results and self.results.face_landmarks:        # fixed: self.last_results → self.results
            return len(self.results.face_landmarks)
        return 0
```

---

### 🤖 Claude · 2026-05-05 14:41

The user has two Python files - `face_idenity.py` and `facetracking.py`. Looking at the errors and the code, I can see the issues:

1. In `face_idenity.py`, line 99 calls `detector.getfaceCount()` (lowercase 'f') but the method in `facetracking.py` is `getFaceCount()` (uppercase 'F').

2. In `facetracking.py`, the `findFaces` method only returns `img` inside the `if draw` block - if `draw=True` but no faces found, or if the draw block runs, it returns img, but there's a missing `return img` at the end of the function.

3. The `draw_counts` function has a bug: `cv2.circle` is being used where `cv2.rectangle` should be used for drawing the panel background.

The main issue from the error logs:
- First error: `'FaceTracking' object has no attribute 'last_results'` - this was fixed in the provided facetracking.py
- Second error: `'FaceTracking' object has no attribute 'findPosition'` - also fixed
- Third error: `'FaceTracking' object has no attribute 'getfaceCount'. Did you mean: 'getFaceCount'?`

So the fix needed is in `face_idenity.py` line 99: change `detector.getfaceCount()` to `detector.getFaceCount()`.

Also in `facetracking.py`, `findFaces` is missing a `return img` at the end (outside the if block).

Let me focus on the clear issues:

1. `face_idenity.py` line 99: `getfaceCount()` → `getFaceCount()`
2. `facetracking.py` `findFaces`: missing `return img` at the bottom (outside if block)
3. `draw_counts` uses `cv2.circle` instead of `cv2.rectangle` for the background panel

The user is asking me to fix these issues. Let me present the corrected files.Looking at your error log and code, there are three issues to fix:

1. **`face_idenity.py` line 99** — calls `getfaceCount()` (lowercase `f`) but the method is `getFaceCount()`.
2. **`facetracking.py` `findFaces`** — missing a `return img` outside the `if draw` block, so it returns `None` when `draw=False` or when no faces are found.
3. **`face_idenity.py` `draw_counts`** — uses `cv2.circle` (wrong) where `cv2.rectangle` is needed for the background panel.

Here are the corrected files:

**`face_idenity.py`** — two fixes (rectangle + getFaceCount):

```python
import cv2
import csv
import os
import facetracking as ft

GESTURES = ["cj"]

KEY_MAP = {
    "1": 0
}

SAVE_FILE = "1gesture_data.csv"

cap = cv2.VideoCapture(0)
detector = ft.FaceTracking()

if not os.path.exists(SAVE_FILE):
    with open(SAVE_FILE, "w", newline="") as f:
        header = [f"{axis}{i}" for i in range(21) for axis in ("x", "y")] + ["label"]
        csv.writer(f).writerow(header)

def get_counts():
    counts = {g: 0 for g in GESTURES}
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                label = row.get("label", "")
                if label in counts:
                    counts[label] += 1
    return counts

def draw_counts(img, counts, active_label=None):
    h, w, _ = img.shape
    panel_x = w - 220
    # FIX: use rectangle instead of circle for background panel
    cv2.rectangle(img, (panel_x - 10, 0), (w, len(GESTURES) * 32 + 20), (0, 0, 0), -1)
    for i, gesture in enumerate(GESTURES):
        count = counts[gesture]
        y = 28 + i * 32
        color = (0, 255, 255) if gesture == active_label else (200, 200, 200)
        bar_width = min(int((count / 150) * 160), 160)
        bar_color = (0, 180, 80) if gesture == active_label else (60, 60, 60)
        # FIX: use rectangle instead of circle for progress bar
        cv2.rectangle(img, (panel_x, y - 16), (panel_x + bar_width, y + 4), bar_color, -1)
        cv2.putText(img, f"{gesture}: {count}", (panel_x, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
    return img

def extract(lm_list, w, h):
    if not lm_list:
        return [0.0] * 42
    row = []
    for idx, cx, cy in lm_list:
        row.append(cx / w)
        row.append(cy / h)
    wrist_x, wrist_y = row[0], row[1]
    return [v - (wrist_x if i % 2 == 0 else wrist_y) for i, v in enumerate(row)]

print("Keys: 1=fist  2=one  3=two  4=three  f=four  p=palm  u=thumbs up  d=thumbs down  b=peak")
print("ESC to quit")

counts = get_counts()
active_label = None

while True:
    success, img = cap.read()
    if not success:
        continue

    img = cv2.flip(img, 1)
    img = detector.findFaces(img)

    lm_list_0 = detector.findPosition(img, face_no=0)

    key = cv2.waitKey(1) & 0xFF
    if key == 27:
        break

    key_char = chr(key) if key < 128 else ""

    if key_char in KEY_MAP and lm_list_0:
        active_label = GESTURES[KEY_MAP[key_char]]
        h, w, _ = img.shape

        row = extract(lm_list_0, w, h)
        row.append(active_label)

        with open(SAVE_FILE, "a", newline="") as f:
            csv.writer(f).writerow(row)

        counts[active_label] += 1

        cv2.putText(img, f"SAVED: {active_label}", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

    # FIX: getFaceCount() — capital F
    face_count = detector.getFaceCount()
    cv2.putText(img, f"faces: {face_count}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    img = draw_counts(img, counts, active_label)
    cv2.imshow("face Collector", img)

cap.release()
cv2.destroyAllWindows()
```

**`facetracking.py`** — one fix (`findFaces` always returns `img`):

```python
    def findFaces(self, img, draw=True):
        rgb   = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        ts_ms = int(time.time() * 1000)

        self.results = self.landmarker.detect_for_video(image, ts_ms)

        if draw and self.results.face_landmarks:
            h, w, _ = img.shape
            for face_landmarks in self.results.face_landmarks:
                pts = [(int(lm.x * w), int(lm.y * h))
                       for lm in face_landmarks]
                for a, b in CONNECTIONS:
                    cv2.line(img, pts[a], pts[b], (0, 255, 0), 1)
                for x, y in pts:
                    cv2.circle(img, (x, y), 1, (0, 200, 255), -1)

        return img  # FIX: moved outside the if-block so img is always returned
```

**Summary of all changes:**

| File | Line | Bug | Fix |
|------|------|-----|-----|
| `face_idenity.py` | 99 | `getfaceCount()` | `getFaceCount()` |
| `face_idenity.py` | `draw_counts` | `cv2.circle` used for rectangles | `cv2.rectangle` |
| `facetracking.py` | `findFaces` | `return img` inside `if` block only | moved `return img` outside `if` |

---
claude-conversations-hub face-landmark-data-collection-system

## Tags
#claude-conversations-hub #face #face-landmark-data-collection-system
