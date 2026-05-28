---
tags: [user, face_landmark_detection_and_gesture_data_collection, face-recognition, computer-vision, claude, ai-conversation]
---



# Face landmark detection and gesture data collection

**Created:** 2026-05-05 14:45  
**Updated:** 2026-05-05 14:45

> Part of [[Claude Conversations Hub]]

---

### 🧑 CJ · 2026-05-05 14:45

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

pyhton projects 2026\face> & C:/Python312/python.exe "c:/pyhton projects 2026/face/face_idenity.py"
WARNING: All log messages before absl::InitializeLog() is called are written to STDERR
I0000 00:00:1777992168.065147   27568 port.cc:153] oneDNN custom operations are on. You may see slightly different numerical results due to floating-point round-off errors from different computation orders. To turn them off, set the environment variable `TF_ENABLE_ONEDNN_OPTS=0`.
WARNING: All log messages before absl::InitializeLog() is called are written to STDERR
I0000 00:00:1777992169.646194   27568 port.cc:153] oneDNN custom operations are on. You may see slightly different numerical results due to floating-point round-off errors from different computation orders. To turn them off, set the environment variable `TF_ENABLE_ONEDNN_OPTS=0`.
W0000 00:00:1777992171.513967    2772 face_landmarker_graph.cc:180] Sets FaceBlendshapesGraph acceleration to xnnpack by default.
INFO: Created TensorFlow Lite XNNPACK delegate for CPU.
W0000 00:00:1777992171.520339   37224 inference_feedback_manager.cc:121] Feedback manager requires a model with a single signature inference. Disabling support for feedback tensors.
W0000 00:00:1777992171.531310   37224 inference_feedback_manager.cc:121] Feedback manager requires a model with a single signature inference. Disabling support for feedback tensors.
Keys: 1=fist  2=one  3=two  4=three  f=four  p=palm  u=thumbs up  d=thumbs down  b=peak
ESC to quit
Traceback (most recent call last):
  File "c:\pyhton projects 2026\face\face_idenity.py", line 99, in <module>
    face_count = detector.getfaceCount()
                 ^^^^^^^^^^^^^^^^^^^^^
AttributeError: 'FaceTracking' object has no attribute 'getfaceCount'. Did you mean: 'getFaceCount'?
PS C:\pyhton projects 2026\face>

---

### 🤖 Claude · 2026-05-05 14:45

The error is a simple typo — `getfaceCount()` should be `getFaceCount()` (capital F). Fix it on line 99:

```python
# Change this:
face_count = detector.getfaceCount()

# To this:
face_count = detector.getFaceCount()
```

While you're at it, there are a couple of other bugs in `face_identity.py` worth fixing:

**1. `draw_counts` uses `cv2.circle` instead of `cv2.rectangle`** (lines with the panel background and bar):
```python
# Wrong — cv2.circle takes a center point and radius, not two corners
cv2.circle(img, (panel_x - 10, 0), (w, len(GESTURES) * 32 + 20), (0, 0, 0), -1)
cv2.circle(img, (panel_x, y - 16), (panel_x + bar_width, y + 4), bar_color, -1)

# Correct:
cv2.rectangle(img, (panel_x - 10, 0), (w, len(GESTURES) * 32 + 20), (0, 0, 0), -1)
cv2.rectangle(img, (panel_x, y - 16), (panel_x + bar_width, y + 4), bar_color, -1)
```

**2. `findFaces` doesn't return `img` when no face is detected**, so `img` becomes `None` on those frames:
```python
# Add a return at the end of findFaces regardless of detection:
    return img   # move this outside the if-block, or add a second return
```

In `facetracking.py`, the current code only hits `return img` inside the `if draw and self.results.face_landmarks:` block. Add a fallback:

```python
        if draw and self.results.face_landmarks:
            # ... drawing code ...
            pass

        return img  # always return, whether or not a face was found
```

The `getfaceCount` typo is what's crashing you right now — the rectangle fix prevents a future crash once you have multiple gestures and the bar tries to render.

---
claude-conversations-hub face-landmark-detection-and-gesture-data-collection

## Tags
#claude-conversations-hub #face #face-landmark-detection-and-gesture-data-collection
