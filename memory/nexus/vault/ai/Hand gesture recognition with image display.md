---
tags: [user, hand_gesture_recognition_with_image_display, face-recognition, computer-vision, claude, ai-conversation]
---



# Hand gesture recognition with image display

**Created:** 2026-05-04 00:42  
**Updated:** 2026-05-04 00:45

> Part of [[Claude Conversations Hub]]

---

### 🧑 CJ · 2026-05-04 00:42

```python
import handTracking as ht
import cv2
import os
import time
import numpy as np
import tensorflow as tf
from PIL import ImageGrab
img = Image.open("C:/Users/cjpen/Downloads/download.jpg")

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['GLOG_minloglevel'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

MODEL_PATH = "gesture_model.keras"
CLASSES_PATH = "gesture_classes.npy"

if not os.path.exists(MODEL_PATH) or not os.path.exists(CLASSES_PATH):
    print("ERROR: Train the model first.")
    exit()

gesture_model = tf.keras.models.load_model(MODEL_PATH)
gesture_classes = np.load(CLASSES_PATH, allow_pickle=True)

GESTURE_ACTION = {
    "PEAK" : "BOOM"
}

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Cannot open camera.")
    exit()


detector = ht.HandTracker()
prev_time = 0

def get_gesture(landmarks):
        """Run the model on one hand's landmarks. Returns (gesture, confidence)."""
        row = []
        for lm in landmarks:
            row.append(lm.x)
            row.append(lm.y)
        wrist_x, wrist_y = row[0], row[1]
        row = [v - (wrist_x if i % 2 == 0 else wrist_y) for i, v in enumerate(row)]
        features = np.array(row, dtype=np.float32).reshape(1, -1)
        pred = gesture_model.predict(features, verbose=0)[0]
        confidence = float(np.max(pred))
        gesture = gesture_classes[np.argmax(pred)]
        return gesture, confidence
    
def preform_action(action):
    global is_peak
    
    now = time.time()
    
    if action == "BOOM":
        img.show()
```

PS C:\pyhton projects 2026\handsv2> & C:/Python312/python.exe "c:/pyhton projects 2026/handsv2/[meme.py](http://meme.py)"
  File "c:\pyhton projects 2026\handsv2\[meme.py](http://meme.py)", line 8
    img = [ImageGrab.open](http://ImageGrab.open)("C:\Users\cjpen\Downloads\download.jpg")
                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
SyntaxError: (unicode error) 'unicodeescape' codec can't decode bytes in position 2-3: truncated \UXXXXXXXX escape
PS C:\pyhton projects 2026\handsv2> & C:/Python312/python.exe "c:/pyhton projects 2026/handsv2/[meme.py](http://meme.py)"
WARNING: All log messages before absl::InitializeLog() is called are written to STDERR
I0000 00:00:1777855312.517846   29312 port.cc:153] oneDNN custom operations are on. You may see slightly different numerical results due to floating-point round-off errors from different computation orders. To turn them off, set the environment variable `TF_ENABLE_ONEDNN_OPTS=0`.
WARNING: All log messages before absl::InitializeLog() is called are written to STDERR
I0000 00:00:1777855314.237155   29312 port.cc:153] oneDNN custom operations are on. You may see slightly different numerical results due to floating-point round-off errors from different computation orders. To turn them off, set the environment variable `TF_ENABLE_ONEDNN_OPTS=0`.
Traceback (most recent call last):
  File "c:\pyhton projects 2026\handsv2\[meme.py](http://meme.py)", line 8, in <module>
    img = [Image.open](http://Image.open)("C:/Users/cjpen/Downloads/download.jpg")
          ^^^^^
NameError: name 'Image' is not defined
PS C:\pyhton projects 2026\handsv2>

---

### 🤖 Claude · 2026-05-04 00:42

The user has two issues:

1. They imported `from PIL import ImageGrab` but then used `Image.open()` - they need to import `Image` from PIL
2. The path issue with backslashes (unicode escape error) - already fixed by using forward slashes

The fix is simple: change `from PIL import ImageGrab` to `from PIL import Image` (or both).Two bugs here:

**1. Wrong PIL import** — You imported `ImageGrab` but used `Image.open()`. Those are different modules.

**2. Backslash path (first error)** — `"C:\Users\..."` trips Python's unicode escape parser because `\U` looks like a unicode escape. You already fixed this by switching to forward slashes, so just keep that.

Fix the import on line 7:

```python
# Before
from PIL import ImageGrab

# After
from PIL import Image
```

That's it. `Image.open()` will now work since `Image` is actually imported.

---

If you need `ImageGrab` elsewhere (e.g. for screen capture), you can import both at once:

```python
from PIL import Image, ImageGrab
```

---

### 🧑 CJ · 2026-05-04 00:43

PS C:\pyhton projects 2026\handsv2> & C:/Python312/python.exe "c:/pyhton projects 2026/handsv2/[meme.py](http://meme.py)"
WARNING: All log messages before absl::InitializeLog() is called are written to STDERR
I0000 00:00:1777855369.184353   15796 port.cc:153] oneDNN custom operations are on. You may see slightly different numerical results due to floating-point round-off errors from different computation orders. To turn them off, set the environment variable `TF_ENABLE_ONEDNN_OPTS=0`.
WARNING: All log messages before absl::InitializeLog() is called are written to STDERR
I0000 00:00:1777855370.801089   15796 port.cc:153] oneDNN custom operations are on. You may see slightly different numerical results due to floating-point round-off errors from different computation orders. To turn them off, set the environment variable `TF_ENABLE_ONEDNN_OPTS=0`.
I0000 00:00:1777855372.253209   15796 cpu_feature_guard.cc:227] This TensorFlow binary is optimized to use available CPU instructions in performance-critical operations.
To enable the following instructions: SSE3 SSE4.1 SSE4.2 AVX AVX2 AVX512F AVX512_VNNI AVX512_BF16 FMA, in other operations, rebuild TensorFlow with the appropriate compiler flags.
WARNING:tensorflow:TensorFlow GPU support is not available on native Windows for TensorFlow >= 2.11. Even if CUDA/cuDNN are installed, GPU will not be used. Please use WSL2 or the TensorFlow-DirectML plugin.
INFO: Created TensorFlow Lite XNNPACK delegate for CPU.
W0000 00:00:1777855372.787869   24108 inference_feedback_manager.cc:121] Feedback manager requires a model with a single signature inference. Disabling support for feedback tensors.
W0000 00:00:1777855372.797214   25624 inference_feedback_manager.cc:121] Feedback manager requires a model with a single signature inference. Disabling support for feedback tensors.
PS C:\pyhton projects 2026\handsv2> what happened

---

### 🤖 Claude · 2026-05-04 00:43

The program ran and exited cleanly - no errors, no crashes. It just quit immediately because the script loads the model and image but never enters a main loop.**It ran and exited successfully — no errors!** All those lines are just TensorFlow startup warnings, not problems.

Here's what each message means:

- **oneDNN custom operations** — TF telling you it's using Intel math optimizations (fine)
- **SSE3/AVX/etc.** — Suggesting you could get faster performance if you compiled TF yourself (you don't need to)
- **TensorFlow GPU support not available** — You're on native Windows with TF ≥ 2.11, so it's using CPU only (fine unless you need GPU speed)
- **XNNPACK delegate** — TF Lite is using a CPU optimizer (fine)
- **Feedback manager** — MediaPipe warning, harmless

---

The reason it **exits immediately** without doing anything is that your script loads the model and image, then just... stops. You never start the camera loop. You're missing the main loop at the bottom, something like:

```python
while True:
    success, frame = cap.read()
    if not success:
        break

    frame = detector.findHands(frame)
    landmarks = detector.findPosition(frame)

    if landmarks:
        gesture, confidence = get_gesture(landmarks)
        if confidence > 0.8:
            action = GESTURE_ACTION.get(gesture)
            if action:
                preform_action(action)

    curr_time = time.time()
    fps = 1 / (curr_time - prev_time)
    prev_time = curr_time
    cv2.putText(frame, f"FPS: {int(fps)}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.imshow("Gesture Cam", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
```

Add that to the bottom of your file and it should actually run the camera and start detecting gestures.

---

### 🧑 CJ · 2026-05-04 00:44

```python
import handTracking as ht
import cv2
import os
import time
import numpy as np
import tensorflow as tf
from PIL import Image
img = Image.open("C:/Users/cjpen/Downloads/download.jpg")

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['GLOG_minloglevel'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

MODEL_PATH = "gesture_model.keras"
CLASSES_PATH = "gesture_classes.npy"

if not os.path.exists(MODEL_PATH) or not os.path.exists(CLASSES_PATH):
    print("ERROR: Train the model first.")
    exit()

gesture_model = tf.keras.models.load_model(MODEL_PATH)
gesture_classes = np.load(CLASSES_PATH, allow_pickle=True)

GESTURE_ACTION = {
    "PEAK" : "BOOM"
}

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Cannot open camera.")
    exit()


detector = ht.HandTracker()
prev_time = 0

def get_gesture(landmarks):
        """Run the model on one hand's landmarks. Returns (gesture, confidence)."""
        row = []
        for lm in landmarks:
            row.append(lm.x)
            row.append(lm.y)
        wrist_x, wrist_y = row[0], row[1]
        row = [v - (wrist_x if i % 2 == 0 else wrist_y) for i, v in enumerate(row)]
        features = np.array(row, dtype=np.float32).reshape(1, -1)
        pred = gesture_model.predict(features, verbose=0)[0]
        confidence = float(np.max(pred))
        gesture = gesture_classes[np.argmax(pred)]
        return gesture, confidence




    
def preform_action(action):
    global is_peak
    
    now = time.time()
    
    if action == "BOOM":
        img.show()
        
while True:
    success, frame = cap.read()
    if not success:
        break

    frame = detector.findHands(frame)
    landmarks = detector.findPosition(frame)

    if landmarks:
        gesture, confidence = get_gesture(landmarks)
        if confidence > 0.8:
            action = GESTURE_ACTION.get(gesture)
            if action:
                preform_action(action)

    curr_time = time.time()
    fps = 1 / (curr_time - prev_time)
    prev_time = curr_time
    cv2.putText(frame, f"FPS: {int(fps)}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.imshow("Gesture Cam", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
img.close()
        
```

PS C:\pyhton projects 2026\handsv2> & C:/Python312/python.exe "c:/pyhton projects 2026/handsv2/[meme.py](http://meme.py)"
WARNING: All log messages before absl::InitializeLog() is called are written to STDERR
I0000 00:00:1777855477.452609   31860 port.cc:153] oneDNN custom operations are on. You may see slightly different numerical results due to floating-point round-off errors from different computation orders. To turn them off, set the environment variable `TF_ENABLE_ONEDNN_OPTS=0`.
WARNING: All log messages before absl::InitializeLog() is called are written to STDERR
I0000 00:00:1777855479.058708   31860 port.cc:153] oneDNN custom operations are on. You may see slightly different numerical results due to floating-point round-off errors from different computation orders. To turn them off, set the environment variable `TF_ENABLE_ONEDNN_OPTS=0`.
I0000 00:00:1777855480.579376   31860 cpu_feature_guard.cc:227] This TensorFlow binary is optimized to use available CPU instructions in performance-critical operations.
To enable the following instructions: SSE3 SSE4.1 SSE4.2 AVX AVX2 AVX512F AVX512_VNNI AVX512_BF16 FMA, in other operations, rebuild TensorFlow with the appropriate compiler flags.
WARNING:tensorflow:TensorFlow GPU support is not available on native Windows for TensorFlow >= 2.11. Even if CUDA/cuDNN are installed, GPU will not be used. Please use WSL2 or the TensorFlow-DirectML plugin.
INFO: Created TensorFlow Lite XNNPACK delegate for CPU.
W0000 00:00:1777855480.914204   24216 inference_feedback_manager.cc:121] Feedback manager requires a model with a single signature inference. Disabling support for feedback tensors.
W0000 00:00:1777855480.923315   25940 inference_feedback_manager.cc:121] Feedback manager requires a model with a single signature inference. Disabling support for feedback tensors.
W0000 00:00:1777855481.477081   31136 landmark_projection_calculator.cc:81] Using NORM_RECT without IMAGE_DIMENSIONS is only supported for the square ROI. Provide IMAGE_DIMENSIONS or use PROJECTION_MATRIX.
Traceback (most recent call last):
  File "c:\pyhton projects 2026\handsv2\[meme.py](http://meme.py)", line 72, in <module>
    gesture, confidence = get_gesture(landmarks)
                          ~~~~~~~~~~~^^^^^^^^^^^
  File "c:\pyhton projects 2026\handsv2\[meme.py](http://meme.py)", line 41, in get_gesture
    row.append(lm.x)
               ^^^^
AttributeError: 'list' object has no attribute 'x'
PS C:\pyhton projects 2026\handsv2>

---

### 🤖 Claude · 2026-05-04 00:45

The error is that `landmarks` returned by `detector.findPosition(frame)` is a list of lists (like `[id, x, y]`), not objects with `.x` and `.y` attributes.The issue is that `detector.findPosition()` returns landmarks as a **list of `[id, x, y]` lists**, not objects with `.x`/`.y` attributes. Your `get_gesture` function is treating them like MediaPipe landmark objects.

Fix `get_gesture` to unpack the list format:

```python
def get_gesture(landmarks):
    """Run the model on one hand's landmarks. Returns (gesture, confidence)."""
    row = []
    for lm in landmarks:
        row.append(lm[1])  # x  (index 0 is the landmark ID)
        row.append(lm[2])  # y
    wrist_x, wrist_y = row[0], row[1]
    row = [v - (wrist_x if i % 2 == 0 else wrist_y) for i, v in enumerate(row)]
    features = np.array(row, dtype=np.float32).reshape(1, -1)
    pred = gesture_model.predict(features, verbose=0)[0]
    confidence = float(np.max(pred))
    gesture = gesture_classes[np.argmax(pred)]
    return gesture, confidence
```

Each landmark from `findPosition()` comes back as `[id, x, y]`, so:
- `lm[0]` → landmark ID (skip this)
- `lm[1]` → x coordinate
- `lm[2]` → y coordinate

The `NORM_RECT` warning above the traceback is also harmless — just MediaPipe being noisy about ROI calculations.

---
claude-conversations-hub hand-gesture-recognition-with-image-display

## Tags
#claude-conversations-hub #hand #hand-gesture-recognition-with-image-display
