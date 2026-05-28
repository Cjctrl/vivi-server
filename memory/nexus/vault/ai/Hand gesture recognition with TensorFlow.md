---
tags: [user, hand_gesture_recognition_with_tensorflow, face-recognition, computer-vision, claude, ai-conversation]
---



# Hand gesture recognition with TensorFlow

**Created:** 2026-05-04 12:03  
**Updated:** 2026-05-04 12:15

> Part of [[Claude Conversations Hub]]

---

### 🧑 CJ · 2026-05-04 12:03

```python
import handTracking as ht
import cv2
import os
import time
import numpy as np
import tensorflow as tf

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['GLOG_minloglevel'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

# --- Load model (with guard) ---
MODEL_PATH = "1gesture_model.keras"
CLASSES_PATH = "1gesture_classes.npy"

if not os.path.exists(MODEL_PATH) or not os.path.exists(CLASSES_PATH):
    print("ERROR: Model not trained yet.")
    print("  1. Run gesture_collector.py to collect data")
    print("  2. Run gesture_trainer.py to train the model")
    print("  3. Then run main.py")
    exit()

gesture_model = tf.keras.models.load_model(MODEL_PATH)
gesture_classes = np.load(CLASSES_PATH, allow_pickle=True)

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Cannot open camera.")
    exit()

detector = ht.HandTracker()
prev_time = 0

try:
    while True:
        success, img = cap.read()
        if not success or img is None:
            continue

        img = cv2.flip(img, 1)
        img = detector.findHands(img)

        curr_time = time.time()
        fps = 1 / (curr_time - prev_time + 1e-9)
        prev_time = curr_time
        cv2.putText(img, f"FPS: {int(fps)}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        results = detector.last_results
        if results and results.hand_landmarks:
            h, w, _ = img.shape
            handedness_list = results.handedness if results.handedness else []

            for i, landmarks in enumerate(results.hand_landmarks):

                # --- Bounding box ---
                x_coords = [int(lm.x * w) for lm in landmarks]
                y_coords = [int(lm.y * h) for lm in landmarks]
                x_min = max(0, min(x_coords))
                x_max = min(w, max(x_coords))
                y_min = max(0, min(y_coords))
                y_max = min(h, max(y_coords))
                cv2.rectangle(img, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)

                # --- Hand label (Left/Right) ---
                if i < len(handedness_list):
                    side = detector.getHandedness(i)
                    cv2.putText(img, side, (x_min, y_min - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

                # --- Fingertip dots ---
                for tip_idx in [4, 8, 12, 16, 20]:
                    lm = landmarks[tip_idx]
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    cv2.circle(img, (cx, cy), 8, (255, 0, 255), cv2.FILLED)

                # --- Gesture prediction ---
                # Build the same feature vector the trainer used
                row = []
                for lm in landmarks:
                    row.append(lm.x)   # already 0-1, no need to divide by w/h
                    row.append(lm.y)

                # Normalize relative to wrist (landmark 0)
                wrist_x, wrist_y = row[0], row[1]
                row = [v - (wrist_x if i % 2 == 0 else wrist_y)
                       for i, v in enumerate(row)]

                features = np.array(row, dtype=np.float32).reshape(1, -1)
                prediction = gesture_model.predict(features, verbose=0)[0]
                confidence = float(np.max(prediction))
                gesture = gesture_classes[np.argmax(prediction)]

                # Only show label if confidence is high enough
                if confidence > 0.75:
                    text = f"{gesture} {confidence:.0%}"
                    color = (0, 255, 255)
                else:
                    text = f"? ({confidence:.0%})"
                    color = (0, 100, 255)

                cv2.putText(img, text, (x_min, y_max + 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

        cv2.imshow("Hand Tracker", img)
        if cv2.waitKey(1) & 0xFF == 27:
            break

finally:
    cap.release()
    cv2.destroyAllWindows()
```


```python
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import tensorflow as tf
import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

# --- Load data ---
df = pd.read_csv("1gesture_data.csv")
print("Shape:", df.shape)
print("Columns:", df.columns.tolist())
print(df.head(2))

# !! Change "label" below to whatever your actual label column is called !!
LABEL_COL = "label"   # e.g. "gesture", "class", "hand_gesture", etc.

# --- Split features and labels ---
X = df.drop(LABEL_COL, axis=1).select_dtypes(include=[np.number]).values.astype(np.float32)
y = df[LABEL_COL].values

num_features = X.shape[1]   # dynamically detected — no more shape mismatch
print(f"Feature count: {num_features}")
print(f"Sample labels: {y[:5]}")

# --- Encode labels ---
encoder = LabelEncoder()
y_encoded = encoder.fit_transform(y)
num_classes = len(encoder.classes_)
print(f"Classes ({num_classes}): {encoder.classes_}")

np.save("gesture_classes.npy", encoder.classes_)

# --- One-hot encode ---
y_onehot = tf.keras.utils.to_categorical(y_encoded, num_classes)

# --- Train/test split ---
X_train, X_test, y_train, y_test = train_test_split(
    X, y_onehot, test_size=0.3, random_state=42
)

# --- Build model with correct input shape ---
model = tf.keras.Sequential([
    tf.keras.layers.Input(shape=(num_features,)),  # ← dynamic, not hardcoded 42
    tf.keras.layers.Dense(80, activation="relu"),
    tf.keras.layers.Dropout(0.3),
    tf.keras.layers.Dense(40, activation="relu"),
    tf.keras.layers.Dense(num_classes, activation="softmax")
])

model.summary()
model.compile(optimizer="adam", loss="categorical_crossentropy", metrics=["accuracy"])

# --- Train ---
model.fit(X_train, y_train, epochs=100, batch_size=8, validation_data=(X_test, y_test))

# --- Evaluate ---
loss, acc = model.evaluate(X_test, y_test)
print(f"\nTest accuracy: {acc:.2%}")

model.save("1gesture_model.keras")
print("Model saved to 1gesture_model.keras")
```

---

### 🤖 Claude · 2026-05-04 12:04

The user has shared two Python scripts - one for hand gesture recognition (main.py) and one for training a gesture model (gesture_trainer.py). They haven't asked a specific question yet. Let me look at the code and wait to see what they need, or maybe they want a review/analysis.

Actually, they just pasted the code without asking anything. I should ask what they need help with.

Wait, let me re-read - they just posted the code. I should ask what they'd like help with.I can see you've shared two scripts — a real-time hand gesture recognizer and a model trainer. What would you like help with?

Some things I could do:

- **Review / critique** the code for bugs, edge cases, or performance issues
- **Explain** how any part of it works
- **Improve** something specific (accuracy, speed, structure, etc.)
- **Add a feature** (e.g. gesture history, multi-hand prediction, action triggers)
- **Debug** an error you're hitting

What are you trying to accomplish?

---

### 🧑 CJ · 2026-05-04 12:04

in the main file its not reading the trained data

---

### 🤖 Claude · 2026-05-04 12:04

The user says the main file isn't reading the trained data. Let me look at the code carefully.

In the trainer, the model is saved as `"1gesture_model.keras"` and classes as `"gesture_classes.npy"` (no "1" prefix).

But in main.py:
```python
MODEL_PATH = "1gesture_model.keras"
CLASSES_PATH = "1gesture_classes.npy"
```

The model path matches, but the classes path has a "1" prefix (`1gesture_classes.npy`), while the trainer saves it as `gesture_classes.npy` (no "1" prefix).

That's the bug — mismatched filename.Found it. There's a **filename mismatch** between the trainer and main.py.

**Trainer saves:**
```python
np.save("gesture_classes.npy", encoder.classes_)   # no "1" prefix
```

**Main expects:**
```python
CLASSES_PATH = "1gesture_classes.npy"              # has "1" prefix
```

So the `os.path.exists()` check fails and the script exits early with *"Model not trained yet."*

**Fix — pick one of these:**

Option A — fix `main.py` to match what the trainer actually saved:
```python
CLASSES_PATH = "gesture_classes.npy"   # remove the "1"
```

Option B — fix the trainer to match what main expects:
```python
np.save("1gesture_classes.npy", encoder.classes_)  # add the "1"
```

Option A is the least disruptive since the trainer file already ran and saved `gesture_classes.npy` to disk. Just update the path constant in `main.py` and you're good.

---

### 🧑 CJ · 2026-05-04 12:11

PS C:\pyhton projects 2026\handsv2> & C:/Python312/python.exe "c:/pyhton projects 2026/handsv2/[main.py](http://main.py)"
WARNING: All log messages before absl::InitializeLog() is called are written to STDERR
I0000 00:00:1777896677.242721   35964 port.cc:153] oneDNN custom operations are on. You may see slightly different numerical results due to floating-point round-off errors from different computation orders. To turn them off, set the environment variable `TF_ENABLE_ONEDNN_OPTS=0`.
WARNING: All log messages before absl::InitializeLog() is called are written to STDERR
I0000 00:00:1777896679.055140   35964 port.cc:153] oneDNN custom operations are on. You may see slightly different numerical results due to floating-point round-off errors from different computation orders. To turn them off, set the environment variable `TF_ENABLE_ONEDNN_OPTS=0`.
I0000 00:00:1777896680.769633   35964 cpu_feature_guard.cc:227] This TensorFlow binary is optimized to use available CPU instructions in performance-critical operations.
To enable the following instructions: SSE3 SSE4.1 SSE4.2 AVX AVX2 AVX512F AVX512_VNNI AVX512_BF16 FMA, in other operations, rebuild TensorFlow with the appropriate compiler flags.
WARNING:tensorflow:TensorFlow GPU support is not available on native Windows for TensorFlow >= 2.11. Even if CUDA/cuDNN are installed, GPU will not be used. Please use WSL2 or the TensorFlow-DirectML plugin.
INFO: Created TensorFlow Lite XNNPACK delegate for CPU.
W0000 00:00:1777896681.453806   30596 inference_feedback_manager.cc:121] Feedback manager requires a model with a single signature inference. Disabling support for feedback tensors.
W0000 00:00:1777896681.465186   30596 inference_feedback_manager.cc:121] Feedback manager requires a model with a single signature inference. Disabling support for feedback tensors.
W0000 00:00:1777896682.091266   36712 landmark_projection_calculator.cc:81] Using NORM_RECT without IMAGE_DIMENSIONS is only supported for the square ROI. Provide IMAGE_DIMENSIONS or use PROJECTION_MATRIX.
Traceback (most recent call last):
  File "c:\pyhton projects 2026\handsv2\[main.py](http://main.py)", line 90, in <module>
    prediction = gesture_model.predict(features, verbose=0)[0]
                 ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
  File "C:\Python312\Lib\site-packages\keras\src\utils\traceback_[utils.py](http://utils.py)", line 122, in error_handler
    raise e.with_traceback(filtered_tb) from None
  File "C:\Python312\Lib\site-packages\keras\src\layers\input_[spec.py](http://spec.py)", line 228, in assert_input_compatibility
    raise ValueError(
    ...<4 lines>...
    )
ValueError: Exception encountered when calling [Sequential.call](http://Sequential.call)().
Input 0 with name 'None' of layer 'dense' is incompatible with the layer: expected axis -1 of input shape to have value 83, but received input with shape (1, 42)
Arguments received by [Sequential.call](http://Sequential.call)():
  • inputs=tf.Tensor(shape=(1, 42), dtype=float32)
  • training=False
  • mask=None
  • kwargs=<class 'inspect._empty'>
PS C:\pyhton projects 2026\handsv2>

---

### 🤖 Claude · 2026-05-04 12:11

The error is clear: the model expects 83 features but main.py is sending 42. 

The trainer uses `X = df.drop(LABEL_COL, axis=1).select_dtypes(include=[np.number]).values` - so whatever columns are in the CSV determines the feature count. The model was trained on 83 features, but main.py only builds 42 features (21 landmarks × 2 coordinates x,y).

83 features vs 42 - the difference is 41. So the CSV likely has x, y, AND z coordinates (21 × 3 = 63... no that's not 83 either). 

Wait - 83 features. Maybe the CSV has additional features beyond just x,y,z. Let me think... 21 landmarks × 4 = 84, no. Maybe it includes x, y, z, visibility = 21*4 = 84, minus 1 for something? Or maybe 21*3 = 63 + some extra features.

Actually, the most likely scenario: the gesture_collector.py saved x, y, AND z coordinates for each landmark. 21 × 3 = 63. Still not 83.

Hmm, or maybe the collector saved additional features. Without seeing gesture_collector.py, I can't know for sure. But the fix is clear: main.py needs to build the same feature vector as the collector did.

The simplest fix: main.py should also include `lm.z` in the feature vector, and potentially other features that the collector used. But we don't know exactly.

The real answer: main.py builds 42 features (x, y for 21 landmarks) but the model needs 83. The user needs to check what gesture_collector.py saved. 

I should tell them: the feature vector in main.py doesn't match what the model was trained on. They need to look at gesture_collector.py to see what features were saved, then replicate that in main.py.

But I can give a likely fix: add `lm.z` to the row. 21*3 = 63, still not 83. 

83 could be 21*3 + 20 (distances between consecutive joints?) or something else.

Actually wait - maybe the CSV has other engineered features. Without seeing the collector, I can only say: match the feature vector. But I should point them to check the collector.

The most actionable advice: check gesture_collector.py for what features it saves, then replicate in main.py. Also, they could just look at the CSV headers.

Let me just tell them the root cause and ask them to share gesture_collector.py or the CSV headers.The error is clear:

```
expected axis -1 of input shape to have value 83, but received input with shape (1, 42)
```

**Root cause:** Your model was trained on **83 features**, but `main.py` only builds **42** (21 landmarks × x, y only).

Your `gesture_collector.py` saved extra features that `main.py` isn't replicating. The most likely culprit is that the collector also saved **`lm.z`** (depth) and possibly other engineered features.

**Quick check** — run this to see exactly what the model expects:
```python
print(gesture_model.input_shape)  # should show (None, 83)
```

And check your CSV headers:
```python
import pandas as pd
df = pd.read_csv("1gesture_data.csv")
print(df.columns.tolist())
print(df.shape)
```

**Most likely fix** — add `lm.z` to your feature row in `main.py`:

```python
# --- Gesture prediction ---
row = []
for lm in landmarks:
    row.append(lm.x)
    row.append(lm.y)
    row.append(lm.z)  # ← add this
```

That gives you 63 features (21 × 3), which still isn't 83. So there are **20 more features** somewhere — likely engineered ones like inter-landmark distances or angles in your collector.

Can you share your **`gesture_collector.py`** or paste the output of `df.columns.tolist()`? That'll show exactly what features to replicate.

---

### 🧑 CJ · 2026-05-04 12:12

```python
import handTracking as ht
import cv2
import os
import time
import numpy as np
import tensorflow as tf

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['GLOG_minloglevel'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

# --- Load model (with guard) ---
MODEL_PATH = "1gesture_model.keras"
CLASSES_PATH = "1gesture_classes.npy"

if not os.path.exists(MODEL_PATH) or not os.path.exists(CLASSES_PATH):
    print("ERROR: Model not trained yet.")
    print("  1. Run gesture_collector.py to collect data")
    print("  2. Run gesture_trainer.py to train the model")
    print("  3. Then run main.py")
    exit()

gesture_model = tf.keras.models.load_model(MODEL_PATH)
gesture_classes = np.load(CLASSES_PATH, allow_pickle=True)

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Cannot open camera.")
    exit()

detector = ht.HandTracker()
prev_time = 0

try:
    while True:
        success, img = cap.read()
        if not success or img is None:
            continue

        img = cv2.flip(img, 1)
        img = detector.findHands(img)

        curr_time = time.time()
        fps = 1 / (curr_time - prev_time + 1e-9)
        prev_time = curr_time
        cv2.putText(img, f"FPS: {int(fps)}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        results = detector.last_results
        if results and results.hand_landmarks:
            h, w, _ = img.shape
            handedness_list = results.handedness if results.handedness else []

            for i, landmarks in enumerate(results.hand_landmarks):

                # --- Bounding box ---
                x_coords = [int(lm.x * w) for lm in landmarks]
                y_coords = [int(lm.y * h) for lm in landmarks]
                x_min = max(0, min(x_coords))
                x_max = min(w, max(x_coords))
                y_min = max(0, min(y_coords))
                y_max = min(h, max(y_coords))
                cv2.rectangle(img, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)

                # --- Hand label (Left/Right) ---
                if i < len(handedness_list):
                    side = detector.getHandedness(i)
                    cv2.putText(img, side, (x_min, y_min - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

                # --- Fingertip dots ---
                for tip_idx in [4, 8, 12, 16, 20]:
                    lm = landmarks[tip_idx]
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    cv2.circle(img, (cx, cy), 8, (255, 0, 255), cv2.FILLED)

                # --- Gesture prediction ---
                # Build the same feature vector the trainer used
                row = []
                for lm in landmarks:
                    row.append(lm.x)   # already 0-1, no need to divide by w/h
                    row.append(lm.y)

                # Normalize relative to wrist (landmark 0)
                wrist_x, wrist_y = row[0], row[1]
                row = [v - (wrist_x if i % 2 == 0 else wrist_y)
                       for i, v in enumerate(row)]

                features = np.array(row, dtype=np.float32).reshape(1, -1)
                prediction = gesture_model.predict(features, verbose=0)[0]
                confidence = float(np.max(prediction))
                gesture = gesture_classes[np.argmax(prediction)]

                # Only show label if confidence is high enough
                if confidence > 0.75:
                    text = f"{gesture} {confidence:.0%}"
                    color = (0, 255, 255)
                else:
                    text = f"? ({confidence:.0%})"
                    color = (0, 100, 255)

                cv2.putText(img, text, (x_min, y_max + 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

        cv2.imshow("Hand Tracker", img)
        if cv2.waitKey(1) & 0xFF == 27:
            break

finally:
    cap.release()
    cv2.destroyAllWindows()
```

just rewrite this to work for a 1,42 input

---

### 🤖 Claude · 2026-05-04 12:12

The user wants to retrain/fix so that the model accepts (1, 42) input. But they just want main.py rewritten to work with 42 features. The issue is the model expects 83 features. 

The simplest fix is to retrain the model with 42 features, OR rewrite main.py to match what the model expects (83 features).

But the user says "rewrite this to work for a 1,42 input" - meaning they want to retrain with 42 features. But wait, they can't change the already-trained model's input shape without retraining.

Actually, I think they want main.py rewritten so it only uses 42 features AND they'll retrain the model. OR they want me to rewrite main.py to produce 42 features and also fix the trainer to use 42 features.

The simplest interpretation: rewrite main.py so the feature vector is 42 (21 × x,y only, no z), and they'll retrain. The current main.py already tries to do 42 features but the model was trained on 83. So just rewrite main.py cleanly for 42 features - which it already does, but they need to retrain the model too.

Wait, re-reading - the current main.py builds 42 features. The model expects 83. The user wants to "rewrite this to work for a 1,42 input" - meaning they want the model to be 42. So they need to retrain. But the trainer script uses the CSV data which has 83 columns.

Actually the simplest fix is: rewrite main.py to match 42 features AND fix the trainer to only use 42 features (x, y only, no z or engineered features), then retrain.

But the user just asked to rewrite main.py. Maybe they want me to just clean up main.py so the feature building is clearly 42 features (x,y for 21 landmarks). The current code already does that - 42 features. The problem is the saved model expects 83.

I think the user wants:
1. Rewrite main.py to use 42 features (it already does this correctly)
2. They'll also need to retrain with the trainer using only 42 features

Let me just rewrite main.py cleanly with 42-feature extraction and add a note that they need to retrain the model with the trainer also set to 42 features.

Actually, looking more carefully - the current main.py already builds 42 features. The issue is the model was trained on 83. So I should just rewrite main.py (it's basically already correct for 42) and tell them they need to retrain.

Let me just provide a clean rewrite of main.py with the feature extraction clearly doing 42 features, and note they need to retrain the model.The current `main.py` already builds 42 features correctly — the mismatch is that the **saved model was trained on 83**. So the fix is two steps:

**1. Retrain** — update the trainer to drop `z` and any extra columns before fitting:

```python
# In gesture_trainer.py, change this line:
X = df.drop(LABEL_COL, axis=1).select_dtypes(include=[np.number]).values.astype(np.float32)

# To this (keep only first 42 columns):
X = df.drop(LABEL_COL, axis=1).select_dtypes(include=[np.number]).iloc[:, :42].values.astype(np.float32)
```

Then re-run `gesture_trainer.py` to produce a fresh `1gesture_model.keras` with input shape `(None, 42)`.

**2. Clean up `main.py`** — the feature builder has a subtle bug in the wrist normalization loop. Here's the fixed version:

```python
# --- Gesture prediction ---
row = []
for lm in landmarks:
    row.append(lm.x)
    row.append(lm.y)

# Normalize relative to wrist (landmark 0)
wrist_x = row[0]
wrist_y = row[1]
for j in range(len(row)):
    if j % 2 == 0:
        row[j] -= wrist_x   # x coords
    else:
        row[j] -= wrist_y   # y coords

features = np.array(row, dtype=np.float32).reshape(1, -1)  # shape (1, 42)
```

The bug in the original was using `i` for the loop index, but `i` was already taken by the outer `enumerate(results.hand_landmarks)` loop — so normalization was applying incorrectly depending on which hand index you were on.

After retraining, this will work cleanly with `(1, 42)`.

---

### 🧑 CJ · 2026-05-04 12:14

```python
import cv2
import csv
import os
import handTracking as ht

GESTURES = ["fist", "one finger", "two fingers", "three fingers",
            "four fingers", "palm", "thumbs up", "thumbs down", ]

KEY_MAP = {
    "1": 0, "2": 1, "3": 2, "4": 3,
    "f": 4, "p": 5, "u": 6, "d": 7
}

SAVE_FILE = "1gesture_data.csv"

cap = cv2.VideoCapture(0)
detector = ht.HandTracker()

# 84 features: 42 per hand (x0,y0...x20,y20) for left then right
if not os.path.exists(SAVE_FILE):
    with open(SAVE_FILE, "w", newline="") as f:
        header = [f"{axis}{i}_{hand}" for hand in ("L", "R") for i in range(21) for axis in ("x", "y")] + ["label"]
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
    cv2.rectangle(img, (panel_x - 10, 0), (w, len(GESTURES) * 32 + 20), (0, 0, 0), -1)
    for i, gesture in enumerate(GESTURES):
        count = counts[gesture]
        y = 28 + i * 32
        color = (0, 255, 255) if gesture == active_label else (200, 200, 200)
        bar_width = min(int((count / 150) * 160), 160)
        bar_color = (0, 180, 80) if gesture == active_label else (60, 60, 60)
        cv2.rectangle(img, (panel_x, y - 16), (panel_x + bar_width, y + 4), bar_color, -1)
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
    img = detector.findHands(img)

    lm_list_0 = detector.findPosition(img, hand_no=0)

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
    hand_count = detector.getHandCount()
    cv2.putText(img, f"Hands: {hand_count}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    img = draw_counts(img, counts, active_label)
    cv2.imshow("Gesture Collector", img)

cap.release()
cv2.destroyAllWindows()
```

---

### 🤖 Claude · 2026-05-04 12:15

The user shared the gesture_collector.py. Let me analyze the issue.

The CSV header is set up for 84 features (42 for left hand + 42 for right hand), but the collector only saves 42 features (one hand) + label. So the CSV has 85 columns in the header but only 43 values per data row.

When the trainer reads it, it gets 84 numeric columns (dropping label), but the actual data only has 42 filled values per row (the rest are either empty/NaN or misaligned).

Wait, let me re-read. The header is:
```python
header = [f"{axis}{i}_{hand}" for hand in ("L", "R") for i in range(21) for axis in ("x", "y")] + ["label"]
```
That's 84 feature columns + 1 label = 85 total.

But the data rows only have 42 features + 1 label = 43 values.

So when pandas reads this CSV, it will have 84 numeric columns but only 42 will have data, and the rest will be NaN or misaligned. Actually, since CSV rows are shorter than the header, pandas will fill with NaN. But wait - the trainer does `select_dtypes(include=[np.number])` which would include all 84 columns, giving 84 features. But NaN values... hmm.

Actually wait - the row only has 42 floats + label. But the header has 84 feature columns + label. So pandas will read 42 values into the first 42 columns, and the label will go into column 43 (which is `y20_L`), and columns 43-84 will be NaN, and the actual "label" column will be empty/NaN.

That's a mess. Actually no - CSV rows that are shorter than the header get NaN filled for missing columns. So:
- Columns x0_L through y20_L (42 cols): have data
- Columns x0_R through y20_R (42 cols): NaN
- label column: has the label

Wait, 42 data values + 1 label = 43 values per row. The header has 85 columns. So pandas would put:
- First 42 columns: landmark data
- Column 43 (x0_R): the label string
- Columns 44-85: NaN

That would be very broken. The trainer would see `select_dtypes(include=[np.number])` dropping the label-as-string in column 43, but NaN values everywhere else...

Hmm, actually let me reconsider. The `extract` function returns 42 floats, then `row.append(active_label)` makes it 43 items. The header has 85 columns. So when written to CSV, only 43 of the 85 columns get filled. Pandas reads it and fills remaining with NaN.

The trainer does:
```python
X = df.drop(LABEL_COL, axis=1).select_dtypes(include=[np.number]).values
```

Since the label column is correctly named "label" and is column 85, it gets dropped. Then `select_dtypes(include=[np.number])` keeps all 84 numeric columns (42 real + 42 NaN). NaN values in training would cause issues.

Actually wait - if the row only has 43 values and header has 85 columns, pandas puts the 43rd value (the label) in the 43rd column which is `x0_R`, not `label`. The actual `label` column would be NaN. This means `df[LABEL_COL]` would be all NaN!

That explains the 83 feature problem too. Let me think again...

If the label ends up in column `x0_R` (index 42, 0-based), that's a string. When doing `select_dtypes(include=[np.number])`, that column would be excluded (it's a string). So we'd have 83 numeric columns: columns 0-41 (real data) + columns 43-83 (NaN from R hand) = 83 columns. That's exactly 83! That explains the error.

So the real problems are:
1. CSV header has 84 features (for two hands) but data only writes 42 (one hand)
2. The label gets written into column 43 (x0_R) instead of the label column
3. Trainer reads 83 numeric columns (42 real + 41 NaN, excluding the string-label-in-wrong-column)

The fix: the collector header and data writing should match. Since data only uses one hand (42 features), either:
- Fix the header to only have 42 features + label
- Or properly save two hands

The simplest fix is to match the header to what's actually being saved (42 features).

So the recommendation:
1. Fix the CSV header in gesture_collector.py to only have 42 features
2. Delete the old CSV and recollect data
3. Retrain

Let me write the fix clearly.Found the real root cause. The CSV header declares **84 feature columns** (42 L + 42 R), but each data row only writes **42 values + label = 43 items**. So when pandas reads it:

- Columns 0–41 → real landmark data ✅
- Column 42 (`x0_R`) → gets the **label string** (misplaced!)
- Columns 43–83 → NaN
- Actual `label` column → NaN/empty

When the trainer does `select_dtypes(include=[np.number])`, it drops the string in column 42, leaving **83 numeric columns** — exactly the error you got.

**Fix the header in `gesture_collector.py`:**

```python
# BEFORE (wrong - declares 84 features for two hands):
header = [f"{axis}{i}_{hand}" for hand in ("L", "R") for i in range(21) for axis in ("x", "y")] + ["label"]

# AFTER (correct - 42 features for one hand):
header = [f"{axis}{i}" for i in range(21) for axis in ("x", "y")] + ["label"]
```

Then:
1. **Delete `1gesture_data.csv`** — the existing data is corrupted (label in wrong column)
2. **Re-run `gesture_collector.py`** to recollect
3. **Re-run `gesture_trainer.py`** to retrain — model will now have input shape `(None, 42)`
4. **Run `main.py`** — feature vector matches ✅

The rest of your collector logic is fine — it's purely a header mismatch that cascaded into everything else.

---
claude-conversations-hub hand-gesture-recognition-with-tensorflow

## Tags
#claude-conversations-hub #hand #hand-gesture-recognition-with-tensorflow
