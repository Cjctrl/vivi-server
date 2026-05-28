---
tags: [user, gesture_recognition_pipeline_with_hand_tracking, face-recognition, computer-vision, claude, ai-conversation]
---



# Gesture recognition pipeline with hand tracking

**Created:** 2026-05-01 15:51  
**Updated:** 2026-05-01 16:30

> Part of [[Claude Conversations Hub]]

---

### 🧑 CJ · 2026-05-01 15:51

i have a pipeline camera to greyscale to hand tracker to hand tracker main 

```python
import cv2

def get_frame(vc):
    rval, frame = vc.read()
    return rval, frame
```


```python
import cv2
import numpy as np
import torch

def process_frame_cnn(frame):
    small = cv2.resize(frame, (32, 32))
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    norm = gray / 255.0

    # shape: (1, 1, 32, 32)
    tensor = torch.tensor(norm, dtype=torch.float32).unsqueeze(0).unsqueeze(0)
    return tensor
```


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
    def __init__(self, max_hands=2, detection_confidence=0.7, tracking_confidence=0.5):
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


```python
"""Main loop with hand-tracking ROI (faster, more robust)."""
import cv2
import threading
import torch
from nn import GestureNet
from greyscale import process_frame_cnn
from hand_tracker import HandTracker
import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
frame = None
lock = threading.Lock()
running = True

# ---- LOAD MODEL & TRACKER ----
model = GestureNet()
model.eval()
tracker = HandTracker(max_hands=1, detection_confidence=0.7)

# ---- CAMERA THREAD ----
def capture():
    global frame, running
    vc = cv2.VideoCapture(0)

    while running:
        rval, img = vc.read()
        if rval:
            with lock:
                frame = img.copy()

    vc.release()

# ---- START THREAD ----
thread = threading.Thread(target=capture)
thread.start()

# ---- MAIN LOOP ----
while True:
    if frame is not None:
        with lock:
            current_frame = frame.copy()

        cv2.imshow("full_frame", current_frame)

        # Extract hand ROI (huge performance boost)
        roi, landmarks = tracker.get_hand_roi(current_frame, padding=20)

        # Show ROI for debugging
        cv2.imshow("hand_roi", roi)

        # Preprocess ROI for CNN
        tensor = process_frame_cnn(roi)

        # Run model
        with torch.no_grad():
            output = model(tensor)

        prediction = torch.argmax(output, dim=1).item()
        confidence = torch.softmax(output, dim=1)[0, prediction].item()
        print(f"Gesture: {prediction}, Confidence: {confidence:.2f}, Hand detected: {landmarks is not None}")

    if cv2.waitKey(1) & 0xFF == 27:
        running = False
        break

cv2.destroyAllWindows()
thread.join()

```

then i have seaprate main 

```python
import cv2
import threading
import torch
from nn import GestureNet
from greyscale import process_frame_cnn

frame = None
lock = threading.Lock()
running = True

# ---- LOAD MODEL ----
model = GestureNet()
model.eval()

# ---- CAMERA THREAD ----
def capture():
    global frame, running
    vc = cv2.VideoCapture(0)

    while running:
        rval, img = vc.read()
        if rval:
            with lock:
                frame = img.copy()

    vc.release()

# ---- START THREAD ----
thread = threading.Thread(target=capture)
thread.start()

# ---- MAIN LOOP ----
while True:
    if frame is not None:
        with lock:
            current_frame = frame.copy()

        cv2.imshow("preview", current_frame)

        # Preprocess for CNN (returns tensor shape (1,1,32,32))
        tensor = process_frame_cnn(current_frame)

        # Run model
        with torch.no_grad():
            output = model(tensor)

        prediction = torch.argmax(output, dim=1).item()
        print(prediction)

    if cv2.waitKey(1) & 0xFF == 27:
        running = False
        break

cv2.destroyAllWindows()
thread.join()
```

then the nural netwoek nn 

```python
import torch
import torch.nn as nn
import torch.nn.functional as F
import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
class GestureNet(nn.Module):
    """Simple CNN for 32x32 grayscale gesture input.

    Input shape: (N, 1, 32, 32)
    """
    def __init__(self, num_classes=10):
        super().__init__()
        self.conv1 = nn.Conv2d(1, 16, 3, padding=1)
        self.conv2 = nn.Conv2d(16, 32, 3, padding=1)
        self.pool = nn.MaxPool2d(2, 2)

        self.fc1 = nn.Linear(32 * 8 * 8, 128)
        self.fc2 = nn.Linear(128, num_classes)

    def forward(self, x):
        x = self.pool(F.relu(self.conv1(x)))  # 32x32 → 16x16
        x = self.pool(F.relu(self.conv2(x)))  # 16x16 → 8x8
        x = x.view(x.size(0), -1)
        x = F.relu(self.fc1(x))
        return self.fc2(x)
```

can you go through and improve my code

---

### 🤖 Claude · 2026-05-01 15:52

Let me review the code and suggest improvements across all files.

Key issues I see:

1. **camera.py** (`get_frame`): Minimal, no error handling, doesn't manage VideoCapture lifecycle
2. **greyscale.py** (`process_frame_cnn`): Fine but could handle edge cases
3. **hand_tracker.py**: Good but timestamp increment is hardcoded (33ms), could use actual time
4. **hand_tracker_main.py**: Good overall, but has global mutable state issues, no confidence display on frame
5. **main.py**: Similar to hand_tracker_main but simpler
6. **nn.py**: Dropout missing, no model loading, basic

Let me think about concrete improvements:

**nn.py:**
- Add dropout for regularization
- Add a `load_weights` classmethod
- The architecture is fine for a simple demo

**greyscale.py:**
- Handle edge case where roi might be empty (0 size)
- The function name `process_frame_cnn` is fine

**hand_tracker.py:**
- Use actual timestamps instead of incrementing by 33ms
- Add a method to draw landmarks on frame
- Return bounding box coords too

**camera.py:**
- This is barely used as a module - the main files don't import it
- Could make it a class

**main.py / hand_tracker_main.py:**
- These are very similar - could be unified
- Thread safety: `running` flag should be used with an Event
- No model weight loading (model is random)
- No display of prediction on frame
- The lock acquisition in the main loop is held while doing heavy processing - should copy under lock then release

Let me provide a comprehensive review with specific improvements.

Main improvements:
1. `nn.py`: Add dropout, batch norm, save/load weights
2. `greyscale.py`: Guard against empty frames
3. `hand_tracker.py`: Use `time.monotonic()` for real timestamps, add `draw_landmarks` helper
4. `hand_tracker_main.py`: Fix the lock (don't hold it during processing), use threading.Event, display prediction on frame, add model weight loading
5. `main.py`: Same threading fixes, merge with hand_tracker_main or keep separate but fix

Let me write the improved versions.Here's a thorough review with concrete improvements across all files:

**Key issues found:**
- Lock held during heavy processing (blocks camera thread)
- `running` flag isn't thread-safe (should be `threading.Event`)
- Hardcoded 33ms timestamp in hand tracker (drifts from real time)
- No guard against empty/invalid ROI frames
- `GestureNet` has no dropout/batchnorm (will overfit), no weight save/load
- Prediction never rendered onto the frame
- `camera.py` is unused by both mains — redundant module
- No confidence threshold gating the prediction display

---

**`nn.py`** — add dropout, batch norm, and weight I/O:

```python
import torch
import torch.nn as nn
import torch.nn.functional as F
import os

os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

WEIGHTS_PATH = "gesture_net.pth"

class GestureNet(nn.Module):
    """Simple CNN for 32x32 grayscale gesture input.

    Input shape:  (N, 1, 32, 32)
    Output shape: (N, num_classes)
    """
    def __init__(self, num_classes: int = 10):
        super().__init__()
        self.conv1 = nn.Conv2d(1, 16, 3, padding=1)
        self.bn1   = nn.BatchNorm2d(16)
        self.conv2 = nn.Conv2d(16, 32, 3, padding=1)
        self.bn2   = nn.BatchNorm2d(32)
        self.pool  = nn.MaxPool2d(2, 2)
        self.drop  = nn.Dropout(0.4)

        self.fc1 = nn.Linear(32 * 8 * 8, 128)
        self.fc2 = nn.Linear(128, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.pool(F.relu(self.bn1(self.conv1(x))))  # → 16×16
        x = self.pool(F.relu(self.bn2(self.conv2(x))))  # →  8×8
        x = x.view(x.size(0), -1)
        x = self.drop(F.relu(self.fc1(x)))
        return self.fc2(x)

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------
    def save(self, path: str = WEIGHTS_PATH) -> None:
        torch.save(self.state_dict(), path)
        print(f"[GestureNet] weights saved → {path}")

    @classmethod
    def load(cls, path: str = WEIGHTS_PATH, **kwargs) -> "GestureNet":
        model = cls(**kwargs)
        if os.path.exists(path):
            model.load_state_dict(torch.load(path, map_location="cpu"))
            print(f"[GestureNet] weights loaded ← {path}")
        else:
            print(f"[GestureNet] no weights at '{path}', using random init")
        return model
```

---

**`greyscale.py`** — guard against degenerate ROI:

```python
import cv2
import numpy as np
import torch

TARGET_SIZE = (32, 32)

def process_frame_cnn(frame: np.ndarray) -> torch.Tensor | None:
    """Preprocess an OpenCV BGR frame (or ROI) for GestureNet.

    Returns a (1, 1, 32, 32) float32 tensor, or None if the frame is
    too small to be meaningful.
    """
    if frame is None or frame.size == 0:
        return None

    h, w = frame.shape[:2]
    if h < 4 or w < 4:          # ROI collapsed to almost nothing
        return None

    small = cv2.resize(frame, TARGET_SIZE)
    gray  = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    norm  = gray.astype(np.float32) / 255.0

    # (1, 1, 32, 32)
    return torch.from_numpy(norm).unsqueeze(0).unsqueeze(0)
```

---

**`hand_tracker.py`** — real timestamps + draw helper:

```python
"""Hand tracking utility using MediaPipe Tasks API (mediapipe >= 0.10)."""
import os
import time
import urllib.request

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

MODEL_PATH = "hand_landmarker.task"
MODEL_URL  = (
    "https://storage.googleapis.com/mediapipe-models/"
    "hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
)

class HandTracker:
    def __init__(
        self,
        max_hands: int = 2,
        detection_confidence: float = 0.7,
        tracking_confidence: float  = 0.5,
    ):
        if not os.path.exists(MODEL_PATH):
            print("[HandTracker] downloading model …")
            urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)

        base_options = python.BaseOptions(model_asset_path=MODEL_PATH)
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_hands=max_hands,
            min_hand_detection_confidence=detection_confidence,
            min_tracking_confidence=tracking_confidence,
        )
        self.detector   = vision.HandLandmarker.create_from_options(options)
        self._start_ts  = time.monotonic()   # wall-clock anchor

    def _timestamp_ms(self) -> int:
        """Monotonically increasing millisecond timestamp."""
        return int((time.monotonic() - self._start_ts) * 1000)

    def get_hand_roi(
        self,
        frame: np.ndarray,
        padding: int = 20,
    ) -> tuple[np.ndarray, list | None]:
        """Return (roi, landmarks) for the first detected hand.

        Falls back to the full frame when no hand is found.
        """
        h, w = frame.shape[:2]
        rgb      = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

        results = self.detector.detect_for_video(mp_image, self._timestamp_ms())

        if results.hand_landmarks:
            lms = results.hand_landmarks[0]
            xs  = [lm.x for lm in lms]
            ys  = [lm.y for lm in lms]

            x1 = max(0, int(min(xs) * w) - padding)
            x2 = min(w, int(max(xs) * w) + padding)
            y1 = max(0, int(min(ys) * h) - padding)
            y2 = min(h, int(max(ys) * h) + padding)

            # Guard: bounding box must have positive area
            if x2 > x1 and y2 > y1:
                return frame[y1:y2, x1:x2], lms

        return frame, None

    # ------------------------------------------------------------------
    # Optional: overlay landmarks on a debug frame
    # ------------------------------------------------------------------
    def draw_landmarks(self, frame: np.ndarray, landmarks: list) -> np.ndarray:
        """Draw landmark dots on *frame* (in-place). Returns the frame."""
        h, w = frame.shape[:2]
        for lm in landmarks:
            cx, cy = int(lm.x * w), int(lm.y * h)
            cv2.circle(frame, (cx, cy), 3, (0, 255, 0), -1)
        return frame
```

---

**`hand_tracker_main.py`** — thread-safe, prediction on-screen, confidence gate:

```python
"""Main loop: hand-tracking ROI → GestureNet inference."""
import os
import threading

import cv2
import torch

from greyscale import process_frame_cnn
from hand_tracker import HandTracker
from nn import GestureNet

os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

CONFIDENCE_THRESHOLD = 0.6
GESTURE_LABELS = [str(i) for i in range(10)]   # replace with real names

# ── shared state ──────────────────────────────────────────────────────
frame      = None
lock       = threading.Lock()
stop_event = threading.Event()          # thread-safe stop signal

# ── model + tracker ───────────────────────────────────────────────────
model   = GestureNet.load()             # loads weights if available
model.eval()
tracker = HandTracker(max_hands=1, detection_confidence=0.7)

# ── camera thread ─────────────────────────────────────────────────────
def capture() -> None:
    global frame
    vc = cv2.VideoCapture(0)
    if not vc.isOpened():
        print("[capture] could not open camera")
        stop_event.set()
        return

    while not stop_event.is_set():
        rval, img = vc.read()
        if rval:
            with lock:
                frame = img          # no copy needed — main thread copies it

    vc.release()

thread = threading.Thread(target=capture, daemon=True)
thread.start()

# ── main loop ─────────────────────────────────────────────────────────
while not stop_event.is_set():
    # --- grab frame quickly, then release the lock ---
    with lock:
        if frame is None:
            current_frame = None
        else:
            current_frame = frame.copy()

    if current_frame is None:
        if cv2.waitKey(1) & 0xFF == 27:
            break
        continue

    # --- hand detection (outside lock) ---
    roi, landmarks = tracker.get_hand_roi(current_frame, padding=20)

    # --- CNN inference ---
    tensor = process_frame_cnn(roi)
    prediction, confidence = None, 0.0

    if tensor is not None:
        with torch.no_grad():
            output     = model(tensor)
            probs      = torch.softmax(output, dim=1)[0]
            pred_idx   = probs.argmax().item()
            confidence = probs[pred_idx].item()

        if confidence >= CONFIDENCE_THRESHOLD:
            prediction = pred_idx

    # --- annotate & display ---
    display = current_frame.copy()

    if landmarks is not None:
        tracker.draw_landmarks(display, landmarks)

    label = (
        f"{GESTURE_LABELS[prediction]}  {confidence:.0%}"
        if prediction is not None
        else "no gesture"
    )
    hand_status = "hand" if landmarks else "no hand"
    cv2.putText(display, label,       (10, 30),  cv2.FONT_HERSHEY_SIMPLEX, 1,   (0, 255, 0), 2)
    cv2.putText(display, hand_status, (10, 65),  cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 0), 1)

    cv2.imshow("gesture", display)
    cv2.imshow("hand_roi", roi)

    if prediction is not None:
        print(f"gesture={GESTURE_LABELS[prediction]}  conf={confidence:.2f}  hand={landmarks is not None}")

    if cv2.waitKey(1) & 0xFF == 27:
        break

stop_event.set()
cv2.destroyAllWindows()
thread.join(timeout=2)
```

---

**Summary of every change and why:**

| File | Change | Reason |
|---|---|---|
| `nn.py` | `BatchNorm2d` after each conv | Stabilises training, faster convergence |
| `nn.py` | `Dropout(0.4)` before fc2 | Reduces overfitting |
| `nn.py` | `save()` / `load()` classmethods | You need to persist trained weights |
| `greyscale.py` | Early return `None` on empty/tiny frame | Prevents crash when ROI collapses |
| `greyscale.py` | `np.float32` cast before division | Avoids silent integer truncation |
| `hand_tracker.py` | `time.monotonic()` timestamps | Hardcoded 33ms drifts badly; real wall-clock is correct |
| `hand_tracker.py` | Positive-area guard on bounding box | Prevents zero-size ROI slice |
| `hand_tracker.py` | `draw_landmarks()` helper | Keeps display logic out of main |
| `main / ht_main` | `threading.Event` instead of `bool` | `bool` writes aren't guaranteed visible across threads in Python |
| `main / ht_main` | Lock released before inference | Holding the lock during MediaPipe + CNN starves the camera thread |
| `main / ht_main` | `daemon=True` on thread | Ensures clean exit if main crashes |
| `main / ht_main` | Confidence threshold gate | Suppresses noisy low-confidence predictions |
| `main / ht_main` | `cv2.putText` overlay | Prediction is visible without reading the terminal |

---

### 🧑 CJ · 2026-05-01 16:24

how  can i add custom gestures

---

### 🤖 Claude · 2026-05-01 16:25

The user wants to know how to add custom gestures to their pipeline. I'll explain the full workflow: collecting training data, labeling it, training the model, and using it.The pipeline is already set up for it — you just need to **collect data, train, and update the label map**. Here's the full workflow:

---

## 1. Data Collector Script

Create `collect_data.py` — press a key to save ROI frames as training samples:

```python
"""Collect gesture training data. Press 0-9 (or any mapped key) to save a sample."""
import cv2
import os
from hand_tracker import HandTracker

SAVE_DIR = "data"
tracker  = HandTracker(max_hands=1, detection_confidence=0.7)

# ── define your gestures here ─────────────────────────────────────────
GESTURE_MAP = {
    ord('0'): "fist",
    ord('1'): "one_finger",
    ord('2'): "two_fingers",
    ord('3'): "three_fingers",
    ord('4'): "four_fingers",
    ord('5'): "open_hand",
    ord('t'): "thumbs_up",
    ord('d'): "thumbs_down",
    ord('p'): "peace",
    ord('o'): "ok",
}

# create folders
for name in GESTURE_MAP.values():
    os.makedirs(os.path.join(SAVE_DIR, name), exist_ok=True)

vc = cv2.VideoCapture(0)
print("Hold a gesture and press its key to save a sample. ESC to quit.")
print("Targets: 100-200 samples per gesture for decent accuracy.")

counts = {name: len(os.listdir(os.path.join(SAVE_DIR, name)))
          for name in GESTURE_MAP.values()}

while True:
    rval, frame = vc.read()
    if not rval:
        continue

    roi, landmarks = tracker.get_hand_roi(frame, padding=20)

    # overlay counts
    for i, (name, count) in enumerate(counts.items()):
        cv2.putText(frame, f"{name}: {count}", (10, 25 + i * 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 1)

    cv2.imshow("collector - full", frame)
    cv2.imshow("collector - roi", roi)

    key = cv2.waitKey(1) & 0xFF

    if key == 27:
        break

    if key in GESTURE_MAP:
        name = GESTURE_MAP[key]
        count = counts[name]
        path  = os.path.join(SAVE_DIR, name, f"{count:05d}.png")
        cv2.imwrite(path, roi)
        counts[name] += 1
        print(f"  saved {path}")

vc.release()
cv2.destroyAllWindows()
```

---

## 2. Trainer Script

Create `train.py` — reads your `data/` folder and trains `GestureNet`:

```python
"""Train GestureNet on collected gesture data."""
import os
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset, random_split
from torchvision import transforms
from PIL import Image
from nn import GestureNet, WEIGHTS_PATH

DATA_DIR    = "data"
EPOCHS      = 30
BATCH_SIZE  = 32
LR          = 1e-3
VAL_SPLIT   = 0.15

# ── dataset ───────────────────────────────────────────────────────────
class GestureDataset(Dataset):
    def __init__(self, root: str):
        self.samples: list[tuple[str, int]] = []
        self.classes  = sorted(os.listdir(root))   # folder names = class names
        self.class_to_idx = {c: i for i, c in enumerate(self.classes)}

        for cls in self.classes:
            folder = os.path.join(root, cls)
            for fname in os.listdir(folder):
                if fname.lower().endswith(('.png', '.jpg')):
                    self.samples.append((os.path.join(folder, fname), self.class_to_idx[cls]))

        self.transform = transforms.Compose([
            transforms.Grayscale(),
            transforms.Resize((32, 32)),
            transforms.RandomHorizontalFlip(),          # augmentation
            transforms.RandomRotation(15),              # augmentation
            transforms.ColorJitter(brightness=0.3),     # augmentation
            transforms.ToTensor(),                      # → [0, 1]
        ])

    def __len__(self)  -> int:
        return len(self.samples)

    def __getitem__(self, idx: int):
        path, label = self.samples[idx]
        img = Image.open(path).convert("RGB")
        return self.transform(img), label

# ── setup ─────────────────────────────────────────────────────────────
dataset  = GestureDataset(DATA_DIR)
n_val    = max(1, int(len(dataset) * VAL_SPLIT))
n_train  = len(dataset) - n_val
train_ds, val_ds = random_split(dataset, [n_train, n_val])

train_dl = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)
val_dl   = DataLoader(val_ds,   batch_size=BATCH_SIZE)

num_classes = len(dataset.classes)
print(f"Classes ({num_classes}): {dataset.classes}")
print(f"Train: {n_train}  Val: {n_val}")

model     = GestureNet(num_classes=num_classes)
optimiser = torch.optim.Adam(model.parameters(), lr=LR)
criterion = nn.CrossEntropyLoss()
scheduler = torch.optim.lr_scheduler.StepLR(optimiser, step_size=10, gamma=0.5)

# ── training loop ─────────────────────────────────────────────────────
best_val_acc = 0.0

for epoch in range(1, EPOCHS + 1):
    model.train()
    total_loss = 0.0
    for imgs, labels in train_dl:
        optimiser.zero_grad()
        loss = criterion(model(imgs), labels)
        loss.backward()
        optimiser.step()
        total_loss += loss.item()

    # validation
    model.eval()
    correct = total = 0
    with torch.no_grad():
        for imgs, labels in val_dl:
            preds    = model(imgs).argmax(dim=1)
            correct += (preds == labels).sum().item()
            total   += labels.size(0)

    val_acc = correct / total
    scheduler.step()
    print(f"epoch {epoch:>3}/{EPOCHS}  loss={total_loss/len(train_dl):.4f}  val_acc={val_acc:.1%}")

    if val_acc > best_val_acc:
        best_val_acc = val_acc
        model.save()   # saves gesture_net.pth
        print(f"           ↑ new best — saved")

print(f"\nDone. Best val accuracy: {best_val_acc:.1%}")

# save the label map alongside the weights so inference always matches
import json
with open("gesture_labels.json", "w") as f:
    json.dump(dataset.classes, f, indent=2)
print("Label map saved → gesture_labels.json")
```

---

## 3. Update `hand_tracker_main.py` to load labels dynamically

Replace the hardcoded label list with:

```python
import json

# load labels saved by trainer (falls back to indices if file missing)
try:
    with open("gesture_labels.json") as f:
        GESTURE_LABELS = json.load(f)
except FileNotFoundError:
    GESTURE_LABELS = [str(i) for i in range(10)]

num_classes = len(GESTURE_LABELS)
model = GestureNet.load(num_classes=num_classes)
```

---

## Workflow summary

```
1. python collect_data.py    ← hold gesture, press key, repeat ~150× per gesture
2. python train.py           ← trains & saves gesture_net.pth + gesture_labels.json  
3. python hand_tracker_main.py  ← picks up new weights automatically
```

**Tips for good accuracy:**
- **150–200 samples minimum** per gesture
- Vary your **hand distance, angle, and lighting** while collecting
- Keep a **separate test session** — don't train and test in the same lighting/position
- If a gesture is confusing the model, collect more samples of just that one and retrain
- The augmentations in the trainer (flip, rotate, jitter) help a lot with small datasets

---

### 🧑 CJ · 2026-05-01 16:30

```python
"""Hand tracking utility using MediaPipe Tasks API (mediapipe >= 0.10)."""
import os
import time
import urllib.request

import json

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

from nn import GestureNet

from nn import GestureNet

os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

MODEL_PATH = "hand_landmarker.task"
MODEL_URL  = (
    "https://storage.googleapis.com/mediapipe-models/"
    "hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
)

try:
    with open("gesture_labels.json") as f:
        GESTURE_LABELS = json.load(f)
except FileNotFoundError:
    GESTURE_LABELS = [str(i) for i in range(10)]

num_classes = len(GESTURE_LABELS)
model = GestureNet.load(num_classes=num_classes)

class HandTracker:
    
    
    def __init__(
        self,
        max_hands: int = 2,
        detection_confidence: float = 0.7,
        tracking_confidence: float  = 0.5,
    ):
        if not os.path.exists(MODEL_PATH):
            print("[HandTracker] downloading model …")
            urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)

        base_options = python.BaseOptions(model_asset_path=MODEL_PATH)
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_hands=max_hands,
            min_hand_detection_confidence=detection_confidence,
            min_tracking_confidence=tracking_confidence,
        )
        self.detector   = vision.HandLandmarker.create_from_options(options)
        self._start_ts  = time.monotonic()   # wall-clock anchor

    def _timestamp_ms(self) -> int:
        """Monotonically increasing millisecond timestamp."""
        return int((time.monotonic() - self._start_ts) * 1000)

    def get_hand_roi(
        self,
        frame: np.ndarray,
        padding: int = 20,
    ) -> tuple[np.ndarray, list | None]:
        """Return (roi, landmarks) for the first detected hand.

        Falls back to the full frame when no hand is found.
        """
        h, w = frame.shape[:2]
        rgb      = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

        results = self.detector.detect_for_video(mp_image, self._timestamp_ms())

        if results.hand_landmarks:
            lms = results.hand_landmarks[0]
            xs  = [lm.x for lm in lms]
            ys  = [lm.y for lm in lms]

            x1 = max(0, int(min(xs) * w) - padding)
            x2 = min(w, int(max(xs) * w) + padding)
            y1 = max(0, int(min(ys) * h) - padding)
            y2 = min(h, int(max(ys) * h) + padding)

            # Guard: bounding box must have positive area
            if x2 > x1 and y2 > y1:
                return frame[y1:y2, x1:x2], lms

        return frame, None

    # ------------------------------------------------------------------
    # Optional: overlay landmarks on a debug frame
    # ------------------------------------------------------------------
    def draw_landmarks(self, frame: np.ndarray, landmarks: list) -> np.ndarray:
        """Draw landmark dots on *frame* (in-place). Returns the frame."""
        h, w = frame.shape[:2]
        for lm in landmarks:
            cx, cy = int(lm.x * w), int(lm.y * h)
            cv2.circle(frame, (cx, cy), 3, (0, 255, 0), -1)
        return frame
```

i added the others can you add the code needed for hadn

---

### 🤖 Claude · 2026-05-01 16:30

The user wants to add the gesture inference code to hand_tracker.py. Currently the file loads the model and labels at module level but never uses them. I need to add a method to HandTracker that runs inference on the ROI.You've loaded the model and labels at module level but never wired them into the class. Here's the updated file:

```python
"""Hand tracking utility using MediaPipe Tasks API (mediapipe >= 0.10)."""
import os
import time
import urllib.request
import json

import cv2
import mediapipe as mp
import numpy as np
import torch
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

from nn import GestureNet
from greyscale import process_frame_cnn

os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

MODEL_PATH = "hand_landmarker.task"
MODEL_URL  = (
    "https://storage.googleapis.com/mediapipe-models/"
    "hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
)

try:
    with open("gesture_labels.json") as f:
        GESTURE_LABELS = json.load(f)
except FileNotFoundError:
    GESTURE_LABELS = [str(i) for i in range(10)]

CONFIDENCE_THRESHOLD = 0.6

class HandTracker:
    def __init__(
        self,
        max_hands: int = 2,
        detection_confidence: float = 0.7,
        tracking_confidence: float = 0.5,
        confidence_threshold: float = CONFIDENCE_THRESHOLD,
    ):
        if not os.path.exists(MODEL_PATH):
            print("[HandTracker] downloading model …")
            urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)

        base_options = python.BaseOptions(model_asset_path=MODEL_PATH)
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_hands=max_hands,
            min_hand_detection_confidence=detection_confidence,
            min_tracking_confidence=tracking_confidence,
        )
        self.detector             = vision.HandLandmarker.create_from_options(options)
        self._start_ts            = time.monotonic()
        self.confidence_threshold = confidence_threshold

        # load gesture model once per tracker instance
        self.labels = GESTURE_LABELS
        self.model  = GestureNet.load(num_classes=len(self.labels))
        self.model.eval()

    def _timestamp_ms(self) -> int:
        return int((time.monotonic() - self._start_ts) * 1000)

    def get_hand_roi(
        self,
        frame: np.ndarray,
        padding: int = 20,
    ) -> tuple[np.ndarray, list | None]:
        """Return (roi, landmarks) for the first detected hand.
        Falls back to the full frame when no hand is found.
        """
        h, w = frame.shape[:2]
        rgb      = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

        results = self.detector.detect_for_video(mp_image, self._timestamp_ms())

        if results.hand_landmarks:
            lms = results.hand_landmarks[0]
            xs  = [lm.x for lm in lms]
            ys  = [lm.y for lm in lms]

            x1 = max(0, int(min(xs) * w) - padding)
            x2 = min(w, int(max(xs) * w) + padding)
            y1 = max(0, int(min(ys) * h) - padding)
            y2 = min(h, int(max(ys) * h) + padding)

            if x2 > x1 and y2 > y1:
                return frame[y1:y2, x1:x2], lms

        return frame, None

    def predict_gesture(
        self,
        roi: np.ndarray,
    ) -> tuple[str | None, float]:
        """Run GestureNet on a hand ROI.

        Returns:
            (label, confidence) if confidence >= threshold, else (None, confidence)
        """
        tensor = process_frame_cnn(roi)
        if tensor is None:
            return None, 0.0

        with torch.no_grad():
            probs      = torch.softmax(self.model(tensor), dim=1)[0]
            idx        = probs.argmax().item()
            confidence = probs[idx].item()

        if confidence < self.confidence_threshold:
            return None, confidence

        label = self.labels[idx] if idx < len(self.labels) else str(idx)
        return label, confidence

    def annotate_frame(
        self,
        frame: np.ndarray,
        landmarks: list | None,
        label: str | None,
        confidence: float,
    ) -> np.ndarray:
        """Draw landmarks + gesture label onto a copy of frame."""
        out = frame.copy()

        if landmarks is not None:
            self.draw_landmarks(out, landmarks)

        text  = f"{label}  {confidence:.0%}" if label else "no gesture"
        color = (0, 255, 0)                  if label else (100, 100, 100)
        cv2.putText(out, text, (10, 35), cv2.FONT_HERSHEY_SIMPLEX, 1.1, color, 2)

        hand_status = "hand detected" if landmarks else "no hand"
        cv2.putText(out, hand_status, (10, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 0), 1)

        return out

    def draw_landmarks(self, frame: np.ndarray, landmarks: list) -> np.ndarray:
        """Draw landmark dots on frame (in-place). Returns the frame."""
        h, w = frame.shape[:2]
        for lm in landmarks:
            cx, cy = int(lm.x * w), int(lm.y * h)
            cv2.circle(frame, (cx, cy), 3, (0, 255, 0), -1)
        return frame
```

Then your main loop becomes very clean since all the logic lives in the tracker:

```python
roi, landmarks          = tracker.get_hand_roi(current_frame, padding=20)
label, confidence       = tracker.predict_gesture(roi)
display                 = tracker.annotate_frame(current_frame, landmarks, label, confidence)

cv2.imshow("gesture", display)
cv2.imshow("hand_roi", roi)
```

**What changed and why:**

- Removed the module-level `model` variable — it was loaded but never called anywhere, so it was dead code. It now lives on `self.model` inside the class where it belongs
- `predict_gesture()` encapsulates the tensor prep → inference → threshold → label lookup in one call
- `annotate_frame()` moves all `cv2.putText` and landmark drawing out of main, keeping that loop to 4 lines
- Removed the duplicate `from nn import GestureNet` import at the top

---

### 🧑 CJ · 2026-05-01 16:30

"""Main loop: hand-tracking ROI → GestureNet inference."""
import os
import threading

import cv2
import torch

from greyscale import process_frame_cnn
from hand_tracker import HandTracker
from nn import GestureNet

os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

CONFIDENCE_THRESHOLD = 0.6
GESTURE_LABELS = [str(i) for i in range(10)]   # replace with real names

# ── shared state ──────────────────────────────────────────────────────
frame      = None
lock       = threading.Lock()
stop_event = threading.Event()          # thread-safe stop signal

# ── model + tracker ───────────────────────────────────────────────────
model   = GestureNet.from_pretrained()             # loads weights if available
model.eval()
tracker = HandTracker(max_hands=1, detection_confidence=0.7)

# ── camera thread ─────────────────────────────────────────────────────
def capture() -> None:
    global frame
    vc = cv2.VideoCapture(0)
    if not vc.isOpened():
        print("[capture] could not open camera")
        stop_event.set()
        return

    while not stop_event.is_set():
        rval, img = vc.read()
        if rval:
            with lock:
                frame = img          # no copy needed — main thread copies it

    vc.release()

thread = threading.Thread(target=capture, daemon=True)
thread.start()

# ── main loop ─────────────────────────────────────────────────────────
while not stop_event.is_set():
    # --- grab frame quickly, then release the lock ---
    with lock:
        if frame is None:
            current_frame = None
        else:
            current_frame = frame.copy()

    if current_frame is None:
        if cv2.waitKey(1) & 0xFF == 27:
            break
        continue

    # --- hand detection (outside lock) ---
    roi, landmarks = tracker.get_hand_roi(current_frame, padding=20)

    # --- CNN inference ---
    tensor = process_frame_cnn(roi)
    prediction, confidence = None, 0.0

    if tensor is not None:
        with torch.no_grad():
            output     = model(tensor)
            probs      = torch.softmax(output, dim=1)[0]
            pred_idx   = probs.argmax().item()
            confidence = probs[pred_idx].item()

        if confidence >= CONFIDENCE_THRESHOLD:
            prediction = pred_idx

    # --- annotate & display ---
    display = current_frame.copy()

    if landmarks is not None:
        tracker.draw_landmarks(display, landmarks)

    label = (
        f"{GESTURE_LABELS[prediction]}  {confidence:.0%}"
        if prediction is not None
        else "no gesture"
    )
    hand_status = "hand" if landmarks else "no hand"
    cv2.putText(display, label,       (10, 30),  cv2.FONT_HERSHEY_SIMPLEX, 1,   (0, 255, 0), 2)
    cv2.putText(display, hand_status, (10, 65),  cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 0), 1)

    cv2.imshow("gesture", display)
    cv2.imshow("hand_roi", roi)

    if prediction is not None:
        print(f"gesture={GESTURE_LABELS[prediction]}  conf={confidence:.2f}  hand={landmarks is not None}")

    if cv2.waitKey(1) & 0xFF == 27:
        break

stop_event.set()
cv2.destroyAllWindows()
thread.join(timeout=2)

---

### 🤖 Claude · 2026-05-01 16:30

The user is showing me their current `hand_tracker_main.py` and it has `GestureNet.from_pretrained()` but in the improved `nn.py` I wrote, the classmethod is called `load()`. They also have the hardcoded `GESTURE_LABELS`. Let me fix these issues and integrate the dynamic label loading from `gesture_labels.json`.

Key fixes needed:
1. `GestureNet.from_pretrained()` → `GestureNet.load()` (or add `from_pretrained` as an alias)
2. Load labels from `gesture_labels.json` dynamically
3. Pass `num_classes` to `GestureNet.load()`

Let me provide a clean corrected version.Two bugs in this file relative to the code from earlier, plus the labels aren't wired up yet:

1. **`GestureNet.from_pretrained()`** — the classmethod is called `load()`, not `from_pretrained()`. This will crash on startup.
2. **`GESTURE_LABELS` is hardcoded** — it needs to load from `gesture_labels.json` so it stays in sync with whatever you trained, and its length needs to be passed to `GestureNet.load()` as `num_classes`.

Here's the corrected file:

```python
"""Main loop: hand-tracking ROI → GestureNet inference."""
import os
import json
import threading

import cv2
import torch

from greyscale import process_frame_cnn
from hand_tracker import HandTracker
from nn import GestureNet

os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

CONFIDENCE_THRESHOLD = 0.6

# ── load label map saved by train.py ─────────────────────────────────
try:
    with open("gesture_labels.json") as f:
        GESTURE_LABELS = json.load(f)
    print(f"[main] loaded {len(GESTURE_LABELS)} gesture labels: {GESTURE_LABELS}")
except FileNotFoundError:
    print("[main] gesture_labels.json not found — falling back to numeric labels")
    GESTURE_LABELS = [str(i) for i in range(10)]

# ── shared state ──────────────────────────────────────────────────────
frame      = None
lock       = threading.Lock()
stop_event = threading.Event()

# ── model + tracker ───────────────────────────────────────────────────
model = GestureNet.load(num_classes=len(GESTURE_LABELS))  # ← was from_pretrained()
model.eval()
tracker = HandTracker(max_hands=1, detection_confidence=0.7)

# ── camera thread ─────────────────────────────────────────────────────
def capture() -> None:
    global frame
    vc = cv2.VideoCapture(0)
    if not vc.isOpened():
        print("[capture] could not open camera")
        stop_event.set()
        return

    while not stop_event.is_set():
        rval, img = vc.read()
        if rval:
            with lock:
                frame = img

    vc.release()

thread = threading.Thread(target=capture, daemon=True)
thread.start()

# ── main loop ─────────────────────────────────────────────────────────
while not stop_event.is_set():
    with lock:
        current_frame = frame.copy() if frame is not None else None

    if current_frame is None:
        if cv2.waitKey(1) & 0xFF == 27:
            break
        continue

    roi, landmarks = tracker.get_hand_roi(current_frame, padding=20)

    tensor = process_frame_cnn(roi)
    prediction, confidence = None, 0.0

    if tensor is not None:
        with torch.no_grad():
            output     = model(tensor)
            probs      = torch.softmax(output, dim=1)[0]
            pred_idx   = probs.argmax().item()
            confidence = probs[pred_idx].item()

        if confidence >= CONFIDENCE_THRESHOLD:
            prediction = pred_idx

    display = current_frame.copy()

    if landmarks is not None:
        tracker.draw_landmarks(display, landmarks)

    label = (
        f"{GESTURE_LABELS[prediction]}  {confidence:.0%}"
        if prediction is not None
        else "no gesture"
    )
    hand_status = "hand" if landmarks else "no hand"
    cv2.putText(display, label,       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1,   (0, 255, 0), 2)
    cv2.putText(display, hand_status, (10, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 0), 1)

    cv2.imshow("gesture", display)
    cv2.imshow("hand_roi", roi)

    if prediction is not None:
        print(f"gesture={GESTURE_LABELS[prediction]}  conf={confidence:.2f}  hand={landmarks is not None}")

    if cv2.waitKey(1) & 0xFF == 27:
        break

stop_event.set()
cv2.destroyAllWindows()
thread.join(timeout=2)
```

The only meaningful changes:

| Line | Before | After | Why |
|---|---|---|---|
| labels | hardcoded `[str(i)...]` | loaded from `gesture_labels.json` | stays in sync with training |
| `GestureNet` init | `.from_pretrained()` | `.load(num_classes=len(GESTURE_LABELS))` | correct method name; num_classes must match the saved weights |

Everything else was already correct. Once you run `collect_data.py` → `train.py`, both the weights and the label file will exist and this will pick them up automatically.

---
claude-conversations-hub gesture-recognition-pipeline-with-hand-tracking

## Tags
#claude-conversations-hub #gesture #gesture-recognition-pipeline-with-hand-tracking
