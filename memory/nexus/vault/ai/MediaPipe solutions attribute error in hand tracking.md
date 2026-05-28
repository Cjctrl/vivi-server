---
tags: [user, mediapipe_solutions_attribute_error_in_hand_tracking, claude, ai-conversation]
---



# MediaPipe solutions attribute error in hand tracking

**Created:** 2026-05-01 15:42  
**Updated:** 2026-05-01 15:43

> Part of [[Claude Conversations Hub]]

---

### 🧑 CJ · 2026-05-01 15:43

PS C:\pyhton projects 2026\hands> & C:/Python312/python.exe "c:/pyhton projects 2026/hands/main_hand_[tracking.py](http://tracking.py)"
Traceback (most recent call last):
  File "c:\pyhton projects 2026\hands\main_hand_[tracking.py](http://tracking.py)", line 18, in <module>
    tracker = HandTracker(max_hands=1, detection_confidence=0.7)
  File "c:\pyhton projects 2026\hands\hand_[tracker.py](http://tracker.py)", line 11, in __init__
    [self.mp](http://self.mp)_hands = [mp.solutions](http://mp.solutions).hands
                    ^^^^^^^^^^^^
AttributeError: module 'mediapipe' has no attribute 'solutions'
PS C:\pyhton projects 2026\hands> 

```python
"""Hand tracking utility using MediaPipe."""
import cv2
import mediapipe as mp
import numpy as np
import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

class HandTracker:
    def __init__(self, max_hands=1, detection_confidence=0.7, tracking_confidence=0.5):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_hands,
            min_detection_confidence=detection_confidence,
            min_tracking_confidence=tracking_confidence
        )

    def get_hand_roi(self, frame, padding=20):
        """Extract hand region of interest from frame.
        
        Args:
            frame: OpenCV image (BGR)
            padding: pixel padding around hand bounding box
        
        Returns:
            roi: cropped hand region or full frame if no hand detected
            landmarks: hand landmarks or None
        """
        h, w, _ = frame.shape
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb)
        
        if results.multi_hand_landmarks:
            lms = results.multi_hand_landmarks[0]
            xs = [lm.x for lm in lms.landmark]
            ys = [lm.y for lm in lms.landmark]
            
            x1 = max(0, int(min(xs) * w - padding))
            x2 = min(w, int(max(xs) * w + padding))
            y1 = max(0, int(min(ys) * h - padding))
            y2 = min(h, int(max(ys) * h + padding))
            
            roi = frame[y1:y2, x1:x2]
            return roi, lms
        
        return frame, None

```

---

### 🤖 Claude · 2026-05-01 15:43

The error is `AttributeError: module 'mediapipe' has no attribute 'solutions'`. This is a known issue with newer versions of MediaPipe (0.10+) where the `mp.solutions` API was changed/removed in favor of the new Tasks API.## The Problem

This is a version compatibility issue. MediaPipe **0.10+** removed the legacy `mp.solutions` API in favor of a new Tasks-based API. Your installed version is too new for the old-style code.

You have two options:

---

### Option 1: Pin to an older MediaPipe version (quickest fix)

```bash
pip install mediapipe==0.9.3.0
```

This restores `mp.solutions.hands` and your code works as-is.

---

### Option 2: Rewrite for the new MediaPipe Tasks API (recommended long-term)

```python
"""Hand tracking utility using MediaPipe Tasks API (mediapipe >= 0.10)."""
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np
import os
import urllib.request

os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

MODEL_PATH = "hand_landmarker.task"
MODEL_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"

class HandTracker:
    def __init__(self, max_hands=1, detection_confidence=0.7, tracking_confidence=0.5):
        # Download model if not present
        if not os.path.exists(MODEL_PATH):
            print("Downloading hand landmark model...")
            urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)

        base_options = python.BaseOptions(model_asset_path=MODEL_PATH)
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,  # Use VIDEO for live frames
            num_hands=max_hands,
            min_hand_detection_confidence=detection_confidence,
            min_tracking_confidence=tracking_confidence
        )
        self.detector = vision.HandLandmarker.create_from_options(options)
        self._frame_ts = 0  # timestamp counter for VIDEO mode

    def get_hand_roi(self, frame, padding=20):
        """Extract hand region of interest from frame.

        Args:
            frame: OpenCV image (BGR)
            padding: pixel padding around hand bounding box

        Returns:
            roi: cropped hand region or full frame if no hand detected
            landmarks: hand landmarks or None
        """
        h, w, _ = frame.shape
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

        self._frame_ts += 33  # ~30fps in milliseconds
        results = self.detector.detect_for_video(mp_image, self._frame_ts)

        if results.hand_landmarks:
            lms = results.hand_landmarks[0]
            xs = [lm.x for lm in lms]
            ys = [lm.y for lm in lms]

            x1 = max(0, int(min(xs) * w - padding))
            x2 = min(w, int(max(xs) * w + padding))
            y1 = max(0, int(min(ys) * h - padding))
            y2 = min(h, int(max(ys) * h + padding))

            roi = frame[y1:y2, x1:x2]
            return roi, lms

        return frame, None
```

---

### Key differences in the new API

| Old (`mp.solutions`) | New (Tasks API) |
|---|---|
| `mp.solutions.hands.Hands()` | `vision.HandLandmarker.create_from_options()` |
| `results.multi_hand_landmarks` | `results.hand_landmarks` |
| `lm.x / lm.y` | Same — `lm.x / lm.y` still works |
| Built-in model | Requires downloading a `.task` model file |
| `LIVE_STREAM` / `IMAGE` modes | `IMAGE`, `VIDEO`, or `LIVE_STREAM` modes |

**Option 1 is the fastest fix** if you just want things running again. Go with Option 2 if you want to stay on a current, supported version of MediaPipe.

---
claude-conversations-hub mediapipe-solutions-attribute-error-in-hand-tracking

## Tags
#claude-conversations-hub #mediapipe #mediapipe-solutions-attribute-error-in-hand-tracking
