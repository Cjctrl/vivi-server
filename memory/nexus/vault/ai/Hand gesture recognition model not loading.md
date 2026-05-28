---
tags: [user, hand_gesture_recognition_model_not_loading, face-recognition, computer-vision, claude, ai-conversation]
---



# Hand gesture recognition model not loading

**Created:** 2026-05-04 12:03  
**Updated:** 2026-05-04 12:03

> Part of [[Claude Conversations Hub]]

---

### 🧑 CJ · 2026-05-04 12:03

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

PS C:\pyhton projects 2026\handsv2> & C:/Python312/python.exe "c:/pyhton projects 2026/handsv2/[main.py](http://main.py)"
WARNING: All log messages before absl::InitializeLog() is called are written to STDERR
I0000 00:00:1777896189.806451   34668 port.cc:153] oneDNN custom operations are on. You may see slightly different numerical results due to floating-point round-off errors from different computation orders. To turn them off, set the environment variable `TF_ENABLE_ONEDNN_OPTS=0`.
WARNING: All log messages before absl::InitializeLog() is called are written to STDERR
I0000 00:00:1777896191.694415   34668 port.cc:153] oneDNN custom operations are on. You may see slightly different numerical results due to floating-point round-off errors from different computation orders. To turn them off, set the environment variable `TF_ENABLE_ONEDNN_OPTS=0`.
ERROR: Model not trained yet.
  1. Run gesture_[collector.py](http://collector.py) to collect data
  2. Run gesture_[trainer.py](http://trainer.py) to train the model
  3. Then run [main.py](http://main.py) why is it not reading the model

---
claude-conversations-hub hand-gesture-recognition-model-not-loading

## Tags
#claude-conversations-hub #hand #hand-gesture-recognition-model-not-loading
