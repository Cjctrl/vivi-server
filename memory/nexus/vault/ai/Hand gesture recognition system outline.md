---
tags: [user, hand_gesture_recognition_system_outline, face-recognition, computer-vision, claude, ai-conversation]
---



# Hand gesture recognition system outline

**Created:** 2026-05-01 22:41  
**Updated:** 2026-05-01 22:42

> Part of [[Claude Conversations Hub]]

---

### 🧑 CJ · 2026-05-01 22:41

build me a full  outline and prompt for how to build it and what to do to build this 

```python
import cv2
import numpy as np


def get_frame(vc: cv2.VideoCapture) -> tuple[bool, np.ndarray | None]:
    """Read one frame from the capture device.

    Returns (True, frame) on success, (False, None) on failure.
    """
    rval, frame = vc.read()
    if not rval:
        return False, None
    return True, frame
```


```python
"""Collect gesture training data.

Controls
--------
Press a mapped key while holding a gesture to save a sample image.
ESC to quit.

Targets: 100–200 samples per gesture for decent accuracy.
"""
import os

import cv2

from hand_tracker import HandTracker

SAVE_DIR = "data"

GESTURE_MAP: dict[int, str] = {
    ord('0'): "fist",
    ord('1'): "one_finger",
    ord('2'): "two_fingers",
    ord('3'): "three_fingers",
    ord('4'): "four_fingers",
    ord('5'): "open_hand",
    ord('t'): "thumbs_up",
    ord('d'): "thumbs_down",
    ord('p'): "gun",
    ord('o'): "ok",
}

# Create one sub-folder per gesture label
for name in GESTURE_MAP.values():
    os.makedirs(os.path.join(SAVE_DIR, name), exist_ok=True)

tracker = HandTracker(max_hands=1, detection_confidence=0.7)

# Pre-count existing samples so numbering continues where it left off
counts: dict[str, int] = {
    name: len([
        f for f in os.listdir(os.path.join(SAVE_DIR, name))
        if f.lower().endswith(('.png', '.jpg'))
    ])
    for name in GESTURE_MAP.values()
}

vc = cv2.VideoCapture(0)
if not vc.isOpened():
    raise RuntimeError("Cannot open camera.")

print("Hold a gesture and press its key to save a sample. ESC to quit.")
print(f"Key map: { {chr(k): v for k, v in GESTURE_MAP.items()} }")
print("Targets: 100–200 samples per gesture.\n")

while True:
    rval, frame = vc.read()
    if not rval:
        continue

    roi, landmarks = tracker.get_hand_roi(frame, padding=20)

    # Draw landmarks on the full-frame preview (not on the saved ROI)
    preview = frame.copy()
    if landmarks is not None:
        tracker.draw_landmarks(preview, landmarks)

    # Overlay sample counts
    for i, (name, count) in enumerate(counts.items()):
        cv2.putText(
            preview, f"{name}: {count}",
            (10, 25 + i * 20),
            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 1,
        )

    cv2.imshow("collector – full frame", preview)
    cv2.imshow("collector – hand ROI",   roi)

    key = cv2.waitKey(1) & 0xFF

    if key == 27:   # ESC
        break

    if key in GESTURE_MAP:
        name  = GESTURE_MAP[key]
        count = counts[name]
        path  = os.path.join(SAVE_DIR, name, f"{count:05d}.png")
        cv2.imwrite(path, roi)
        counts[name] += 1
        print(f"  saved {path}  (total {counts[name]})")

vc.release()
cv2.destroyAllWindows()
print("\nCollection done.")
for name, count in counts.items():
    print(f"  {name}: {count} samples")
```


```python
import cv2
import numpy as np
import torch

TARGET_SIZE = (32, 32)
MIN_DIM     = 4          # ROI smaller than this is meaningless


def process_frame_cnn(frame: np.ndarray) -> torch.Tensor | None:
    """Preprocess an OpenCV BGR frame (or ROI) for GestureNet.

    Steps:
      1. Guard against empty / collapsed ROI.
      2. Resize to TARGET_SIZE.
      3. Convert BGR → greyscale.
      4. Normalise to [0, 1].
      5. Return a (1, 1, 32, 32) float32 tensor.

    Returns None when the frame is unusable.
    """
    if frame is None or frame.size == 0:
        return None

    h, w = frame.shape[:2]
    if h < MIN_DIM or w < MIN_DIM:
        return None

    small = cv2.resize(frame, TARGET_SIZE, interpolation=cv2.INTER_AREA)
    gray  = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    norm  = gray.astype(np.float32) / 255.0

    # shape: (1, 1, 32, 32)  — batch × channel × H × W
    return torch.from_numpy(norm).unsqueeze(0).unsqueeze(0)
```


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


    if cv2.waitKey(1) & 0xFF == 27:
        running = False
        break

cv2.destroyAllWindows()
thread.join()
```


```python
import os

import torch
import torch.nn as nn
import torch.nn.functional as F

os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

WEIGHTS_PATH = "gesture_net.pth"


class GestureNet(nn.Module):
    """Simple CNN for 32×32 greyscale gesture images.

    Input:  (N, 1, 32, 32)
    Output: (N, num_classes)

    Architecture
    ------------
    conv1 (1→16, 3×3)  + BN + ReLU + MaxPool  →  16×16
    conv2 (16→32, 3×3) + BN + ReLU + MaxPool  →   8×8
    Dropout(0.4)
    FC(32×8×8 → 128) + ReLU
    FC(128 → num_classes)
    """

    def __init__(self, num_classes: int = 10):
        super().__init__()
        self.conv1 = nn.Conv2d(1, 16, 3, padding=1)
        self.bn1   = nn.BatchNorm2d(16)
        self.conv2 = nn.Conv2d(16, 32, 3, padding=1)
        self.bn2   = nn.BatchNorm2d(32)
        self.pool  = nn.MaxPool2d(2, 2)
        self.drop  = nn.Dropout(0.4)
        self.fc1   = nn.Linear(32 * 8 * 8, 128)
        self.fc2   = nn.Linear(128, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.pool(F.relu(self.bn1(self.conv1(x))))   # → (N, 16, 16, 16)
        x = self.pool(F.relu(self.bn2(self.conv2(x))))   # → (N, 32,  8,  8)
        x = x.view(x.size(0), -1)                        # → (N, 2048)
        x = self.drop(F.relu(self.fc1(x)))               # → (N, 128)
        return self.fc2(x)                                # → (N, num_classes)

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------

    def save(self, path: str = WEIGHTS_PATH) -> None:
        torch.save(self.state_dict(), path)
        print(f"[GestureNet] weights saved → {path}")

    @classmethod
    def from_pretrained(
        cls,
        path: str = WEIGHTS_PATH,
        num_classes: int = 10,
    ) -> "GestureNet":
        """Create a GestureNet and load weights from *path* if it exists."""
        model = cls(num_classes=num_classes)
        if os.path.exists(path):
            state = torch.load(path, map_location="cpu")
            model.load_state_dict(state)
            print(f"[GestureNet] weights loaded ← {path}")
        else:
            print(f"[GestureNet] no weights at '{path}', using random init")
        return model
```


```python
"""Orchestrates the training and inference process.

This script first runs `train.py` to ensure the model is trained and
the gesture labels are saved. Then, it launches `main_hand_tracking.py`
for live inference.
"""
import subprocess
import sys

print("--- Starting training process (train.py) ---")
train_process = subprocess.run(
    [sys.executable, "train.py"],
    capture_output=False, # Set to True to capture output, False to stream
    text=True
)

if train_process.returncode == 0:
    print("\n--- Training complete. Starting live inference (main_hand_tracking.py) ---")
    subprocess.run([sys.executable, "main_hand_tracking.py"])
else:
    print(f"\n--- Training failed with exit code {train_process.returncode}. Aborting inference. ---")
```


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

### 🤖 Claude · 2026-05-01 22:42

The user wants a full outline and prompt for how to build this gesture recognition system. Let me create a comprehensive guide.
# Gesture Recognition System — Full Build Outline & Prompt

---

## What This System Does

A real-time hand gesture classifier that uses your webcam to:
1. Detect your hand with MediaPipe
2. Crop a tight ROI around it
3. Run a tiny CNN (GestureNet) on the crop
4. Display the predicted gesture + confidence live

---

## File Map

```
project/
├── hand_tracker.py          # MediaPipe wrapper — detects hand, returns ROI crop
├── greyscale.py             # Preprocessing — BGR frame → (1,1,32,32) tensor
├── nn.py                    # GestureNet CNN definition + save/load helpers
├── collect.py               # Data collection script — press keys to save samples
├── train.py                 # Training loop — builds gesture_net.pth
├── main_hand_tracker.py     # Live inference loop (threaded camera)
├── run.py                   # Orchestrator — runs train.py then main_hand_tracker.py
└── camera.py                # Minimal get_frame() helper used by collect.py
```

---

## Build Order (Step by Step)

### Step 1 — Environment Setup
Install dependencies before writing any code:
```bash
pip install mediapipe opencv-python torch torchvision pillow numpy
```
MediaPipe ≥ 0.10 is required for the Tasks API (`HandLandmarker`). The model file (`hand_landmarker.task`) auto-downloads on first run.

---

### Step 2 — `camera.py` (Trivial Helper)
**Purpose:** Wraps `cv2.VideoCapture.read()` into a clean `(bool, frame | None)` return.

**Key points:**
- Takes a `cv2.VideoCapture` object, returns `(True, frame)` or `(False, None)`
- Used by `collect.py` for simple single-threaded reads
- `main_hand_tracker.py` uses a full background thread instead (see Step 6)

---

### Step 3 — `hand_tracker.py` (MediaPipe Wrapper)
**Purpose:** Owns all MediaPipe logic. Nothing else in the project imports mediapipe.

**Key points:**
- Uses `HandLandmarker` in `VIDEO` mode (requires a monotonically increasing ms timestamp — store `time.monotonic()` at init and diff it each call)
- `get_hand_roi(frame, padding)` → computes bounding box from normalized landmarks, pads it, clips to frame bounds, returns `(roi_crop, landmarks)`. Returns `(full_frame, None)` when no hand found so callers always get a valid image
- `draw_landmarks(frame, landmarks)` → draws green dots at each landmark position, modifies in-place
- Constructor auto-downloads `hand_landmarker.task` from Google's CDN if missing

---

### Step 4 — `greyscale.py` (Preprocessing)
**Purpose:** Converts any BGR frame/ROI into the exact tensor GestureNet expects.

**Key points:**
- Guard against `None`, zero-size, or sub-4px frames — return `None` in those cases
- Resize to `(32, 32)` with `INTER_AREA`
- Convert BGR → greyscale → float32 → divide by 255
- Return shape `(1, 1, 32, 32)` via two `unsqueeze(0)` calls

---

### Step 5 — `nn.py` (GestureNet CNN)
**Purpose:** Defines the model architecture and its save/load helpers.

**Architecture:**
```
Input (N, 1, 32, 32)
  → Conv2d(1→16, 3×3, pad=1) + BN + ReLU + MaxPool2d(2)   → (N, 16, 16, 16)
  → Conv2d(16→32, 3×3, pad=1) + BN + ReLU + MaxPool2d(2)  → (N, 32, 8, 8)
  → Dropout(0.4)
  → Linear(2048 → 128) + ReLU
  → Linear(128 → num_classes)
```

**Key points:**
- `save(path)` calls `torch.save(state_dict, path)`
- `from_pretrained(path, num_classes)` is a `@classmethod` — creates model, loads weights if the file exists, otherwise uses random init with a printed warning
- Default `WEIGHTS_PATH = "gesture_net.pth"`

---

### Step 6 — `collect.py` (Data Collection)
**Purpose:** Lets you build a labeled dataset by pressing keys while holding gestures.

**Key points:**
- `GESTURE_MAP: dict[int, str]` maps `ord('key')` → gesture name
- Creates `data/<gesture_name>/` folders automatically
- Pre-counts existing `.png`/`.jpg` files so numbering picks up where it left off
- Shows two windows: full frame with landmarks + the ROI crop
- On a mapped keypress: saves the **ROI** (not the full frame) as `{count:05d}.png`
- Overlay shows live sample counts per gesture
- **Target:** 100–200 samples per gesture

**Default gestures:** fist, one_finger, two_fingers, three_fingers, four_fingers, open_hand, thumbs_up, thumbs_down, gun, ok

---

### Step 7 — `train.py` (Training Loop)
**Purpose:** Trains GestureNet on your collected data and saves weights + label map.

**Key points:**
- `GestureDataset` walks `data/<class>/` folders — folder names become class labels (sorted alphabetically → stable indices)
- Augmentations: `RandomHorizontalFlip`, `RandomRotation(15)`, `ColorJitter(brightness=0.3)`
- 85/15 train/val split via `random_split`
- `Adam(lr=1e-3)` + `StepLR(step_size=10, gamma=0.5)`
- 30 epochs; saves `gesture_net.pth` whenever validation accuracy improves
- After training, writes `gesture_labels.json` — a plain list of class names in index order. **This file must exist for inference to use human-readable labels.**

---

### Step 8 — `main_hand_tracker.py` (Live Inference)
**Purpose:** Combines everything into a real-time display loop.

**Key points:**
- Background thread writes latest frame into `_frame` under a `threading.Lock`; main thread copies it immediately to keep lock time minimal
- Loads `gesture_labels.json` (falls back to numeric strings if missing)
- Calls `tracker.get_hand_roi()` every frame (landmarks must stay fresh)
- Calls `process_frame_cnn()` + model forward pass every `INFER_EVERY_N_FRAMES` frames (set to 2–3 to reduce CPU load)
- Ignores predictions below `CONFIDENCE_THRESHOLD = 0.6`
- Shows two windows: annotated full frame + ROI crop
- ESC to quit; cleanup joins the capture thread with a 2-second timeout

---

### Step 9 — `run.py` (Orchestrator)
**Purpose:** Single entry point — trains first, then launches live inference.

**Key points:**
- Runs `train.py` via `subprocess.run([sys.executable, "train.py"])`
- Checks `returncode == 0` before launching `main_hand_tracker.py`
- Set `capture_output=False` to stream training logs to the terminal live

---

## Full Build Prompt

Use this prompt with any capable coding assistant to generate the complete project:

---

> **Prompt:**
>
> Build a complete real-time hand gesture recognition system in Python. The project consists of exactly these files: `camera.py`, `hand_tracker.py`, `greyscale.py`, `nn.py`, `collect.py`, `train.py`, `main_hand_tracker.py`, and `run.py`. Use the following spec precisely:
>
> **`camera.py`** — Write a single function `get_frame(vc: cv2.VideoCapture) -> tuple[bool, np.ndarray | None]` that calls `vc.read()` and returns `(True, frame)` on success or `(False, None)` on failure.
>
> **`hand_tracker.py`** — Wrap MediaPipe Tasks API (`mediapipe >= 0.10`) `HandLandmarker` in `VIDEO` running mode. The class `HandTracker` takes `max_hands`, `detection_confidence`, and `tracking_confidence` in its constructor. Auto-download `hand_landmarker.task` from `https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task` if it doesn't exist. Store `time.monotonic()` at init and compute a monotonically increasing ms timestamp for each `detect_for_video` call. Implement `get_hand_roi(frame, padding=20) -> (roi, landmarks | None)` which computes bounding box from normalized landmarks, pads and clips to frame bounds, and returns the crop — or the full frame if no hand is detected. Implement `draw_landmarks(frame, landmarks)` that draws green 3px circles at each landmark position in-place.
>
> **`greyscale.py`** — Write `process_frame_cnn(frame: np.ndarray) -> torch.Tensor | None`. Guard against None/empty/sub-4px frames. Resize to `(32, 32)` with `INTER_AREA`. Convert BGR to greyscale, normalize to `[0,1]` as float32, return shape `(1, 1, 32, 32)` tensor.
>
> **`nn.py`** — Define `GestureNet(nn.Module)`. Architecture: `Conv2d(1→16,3×3,pad=1)+BN+ReLU+MaxPool` then `Conv2d(16→32,3×3,pad=1)+BN+ReLU+MaxPool` then `Dropout(0.4)` then `Linear(2048→128)+ReLU` then `Linear(128→num_classes)`. Add `.save(path)` instance method and `@classmethod from_pretrained(path, num_classes)` that loads weights if the file exists else prints a warning and uses random init. Default `WEIGHTS_PATH = "gesture_net.pth"`.
>
> **`collect.py`** — Build a data collection loop. Define `GESTURE_MAP: dict[int, str]` mapping `ord(key)` to gesture names: `{'0':fist, '1':one_finger, '2':two_fingers, '3':three_fingers, '4':four_fingers, '5':open_hand, 't':thumbs_up, 'd':thumbs_down, 'p':gun, 'o':ok}`. Create `data/<gesture>/` folders. Pre-count existing samples. Run camera loop using `HandTracker`. On mapped keypress, save the ROI crop to `data/<gesture>/<count:05d>.png`. Show two windows: full frame with landmarks and the ROI. Overlay live sample counts. ESC to quit.
>
> **`train.py`** — Define `GestureDataset(Dataset)` that walks `data/<class>/` folders, sorts class names for stable indices, and applies transforms: `Grayscale`, `Resize(32,32)`, `RandomHorizontalFlip`, `RandomRotation(15)`, `ColorJitter(brightness=0.3)`, `ToTensor`. 85/15 train/val split. Train `GestureNet` with `Adam(lr=1e-3)`, `CrossEntropyLoss`, `StepLR(step_size=10, gamma=0.5)` for 30 epochs. Save `gesture_net.pth` on new best val accuracy. After training, write class names list to `gesture_labels.json`.
>
> **`main_hand_tracker.py`** — Run a threaded camera loop. Background thread writes to `_frame` under a `threading.Lock`. Main loop copies the frame, calls `tracker.get_hand_roi()` every frame, runs `process_frame_cnn()` + `GestureNet` forward pass every `INFER_EVERY_N_FRAMES=1` frames, ignores predictions below `CONFIDENCE_THRESHOLD=0.6`. Load labels from `gesture_labels.json` (fallback to numeric strings). Annotate display with gesture label+confidence in green or "no gesture" in grey, plus "hand detected"/"no hand" status. Show two windows. Print predictions to stdout. ESC to quit; join capture thread with 2s timeout.
>
> **`run.py`** — Use `subprocess.run([sys.executable, "train.py"], capture_output=False)`. If returncode is 0, run `main_hand_tracker.py` the same way. Otherwise print the error code and abort.
>
> Set `os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'` and `TF_CPP_MIN_LOG_LEVEL = '3'` at the top of any file that imports torch or mediapipe. Use type hints throughout. Add docstrings to all classes and public functions.

---

## Usage Flow

```bash
# 1. Collect data (100–200 samples per gesture)
python collect.py

# 2. Train + launch inference in one command
python run.py

# — OR run steps separately —
python train.py
python main_hand_tracker.py
```

---

## Common Pitfalls to Avoid

| Pitfall | Fix |
|---|---|
| MediaPipe VIDEO mode timestamp not monotonic | Diff from a stored `time.monotonic()` at init — never use wall clock or frame index directly |
| ROI crop is 0×0 when hand is at edge | Always `max(0,...)` / `min(w,...)` clip AND check `x2 > x1 and y2 > y1` before slicing |
| Label indices differ between train and inference | `gesture_labels.json` is written by `train.py` using `sorted()` class names — `main_hand_tracker.py` must load the same file |
| Model loaded with wrong `num_classes` | Always pass `len(GESTURE_LABELS)` from the JSON into `GestureNet.from_pretrained()` |
| Camera thread races with main loop | Copy `_frame` inside the lock immediately; do all processing on the copy |

---
claude-conversations-hub hand-gesture-recognition-system-outline

## Tags
#claude-conversations-hub #hand #hand-gesture-recognition-system-outline
