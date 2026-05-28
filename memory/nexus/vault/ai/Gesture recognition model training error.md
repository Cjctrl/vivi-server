---
tags: [user, gesture_recognition_model_training_error, machine-learning, artificial-intelligence, face-recognition, computer-vision, claude, ai-conversation]
---



# Gesture recognition model training error

**Created:** 2026-05-04 11:40  
**Updated:** 2026-05-04 11:52

> Part of [[Claude Conversations Hub]]

---

### 🧑 CJ · 2026-05-04 11:40

```python
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import tensorflow as tf
import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['GLOG_minloglevel'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'



# --- Load data ---
df = pd.read_csv("1gesture_data.csv")
X = df.drop("label", axis=1).values.astype(np.float32)  # shape: (N, 42)
y = df["label"].values

# --- Encode labels to integers ---
# e.g. "thumbs_up" → 0, "peace" → 1, etc.
encoder = LabelEncoder()
y_encoded = encoder.fit_transform(y)
num_classes = len(encoder.classes_)
print(f"Classes: {encoder.classes_}")

# Save the class names so the predictor knows the order
np.save("gesture_classes.npy", encoder.classes_)

# --- One-hot encode for softmax output ---
y_onehot = tf.keras.utils.to_categorical(y_encoded, num_classes)

# --- Train/test split ---
X_train, X_test, y_train, y_test = train_test_split(X, y_onehot, test_size=0.3, random_state=42)

# --- Build the network ---
model = tf.keras.Sequential([
    tf.keras.layers.Input(shape=(42,)),           # 42 landmark features
    tf.keras.layers.Dense(80, activation="relu"), # hidden layer 1
    tf.keras.layers.Dropout(0.3),                 # prevents overfitting
    tf.keras.layers.Dense(40, activation="relu"), # hidden layer 2
    tf.keras.layers.Dense(num_classes, activation="softmax")  # output: one per gesture
])

model.summary()

model.compile(
    optimizer="adam",
    loss="categorical_crossentropy",
    metrics=["accuracy"]
)

# --- Train ---
model.fit(
    X_train, y_train,
    epochs=100,
    batch_size=8,
    validation_data=(X_test, y_test)
)

# --- Evaluate ---
loss, acc = model.evaluate(X_test, y_test)
print(f"\nTest accuracy: {acc:.2%}")

# --- Save the model ---
model.save("gesture_model.keras")
print("Model saved to gesture_model.keras")
```

PS C:\pyhton projects 2026\handsv2> & C:/Python312/python.exe "c:/pyhton projects 2026/handsv2/[train1gesture.py](http://train1gesture.py)"
WARNING: All log messages before absl::InitializeLog() is called are written to STDERR
I0000 00:00:1777894785.324182   21776 port.cc:153] oneDNN custom operations are on. You may see slightly different numerical results due to floating-point round-off errors from different computation orders. To turn them off, set the environment variable `TF_ENABLE_ONEDNN_OPTS=0`.
WARNING: All log messages before absl::InitializeLog() is called are written to STDERR
I0000 00:00:1777894786.702487   21776 port.cc:153] oneDNN custom operations are on. You may see slightly different numerical results due to floating-point round-off errors from different computation orders. To turn them off, set the environment variable `TF_ENABLE_ONEDNN_OPTS=0`.
Traceback (most recent call last):
  File "c:\pyhton projects 2026\handsv2\[train1gesture.py](http://train1gesture.py)", line 16, in <module>
    X = df.drop("label", axis=1).values.astype(np.float32)  # shape: (N, 42)
ValueError: could not convert string to float: 'fist'
PS C:\pyhton projects 2026\handsv2>

---

### 🤖 Claude · 2026-05-04 11:40

The error is clear: some rows in the CSV have the string 'fist' in a column that should be numeric. The "label" column isn't being dropped properly, or there's another string column in the data.

The issue is likely that the CSV has a column other than "label" that contains string values, or the label column name doesn't match exactly.

Most likely cause: the CSV might have the label in a different column, or there are multiple non-numeric columns. The fix is to ensure only numeric columns are used for X, or to check what columns exist.

A simple fix: after dropping "label", select only numeric columns, or use `pd.to_numeric` with `errors='coerce'`.

Actually, the most likely issue is that there's another non-numeric column in the dataframe besides "label". The fix would be to select only numeric columns or to explicitly select the feature columns.

Let me suggest: use `df.select_dtypes(include=[np.number])` to get X, or investigate what columns are present.The error means there's at least one non-numeric column left in `X` after dropping `"label"` — likely a second string column in your CSV (maybe `"gesture"`, `"class"`, or a duplicate label column).

**Quick fix** — replace your `X =` line to explicitly keep only numeric columns:

```python
# --- Load data ---
df = pd.read_csv("1gesture_data.csv")

# Drop the label AND any other non-numeric columns automatically
X = df.drop("label", axis=1).select_dtypes(include=[np.number]).values.astype(np.float32)
y = df["label"].values
```

---

**To diagnose exactly what's in your CSV**, add this right after loading:

```python
df = pd.read_csv("1gesture_data.csv")
print(df.dtypes)          # shows every column's type
print(df.head(2))         # shows first 2 rows
```

That will tell you which column(s) contain strings. Common culprits:

| Scenario | Fix |
|---|---|
| A second label/name column (e.g. `"gesture"`) | `df.drop(["label", "gesture"], axis=1)` |
| A stray index/ID column saved as text | `df.drop(["label", "id"], axis=1)` |
| Landmark column has a header like `"fist"` shifted into data | Check CSV structure — headers may be misaligned |

The `select_dtypes` fix handles all of these automatically, but knowing which column it is helps you confirm your feature count is still 42 before training.

---

### 🧑 CJ · 2026-05-04 11:52

```python
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import tensorflow as tf
import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['GLOG_minloglevel'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'



# --- Load data ---
df = pd.read_csv("1gesture_data.csv")

# Drop the label AND any other non-numeric columns automatically
X = df.drop("label", axis=1).select_dtypes(include=[np.number]).values.astype(np.float32)
y = df["label"].values   

# --- Encode labels to integers ---
# e.g. "thumbs_up" → 0, "peace" → 1, etc.
encoder = LabelEncoder()
y_encoded = encoder.fit_transform(y)
num_classes = len(encoder.classes_)
print(f"Classes: {encoder.classes_}")

# Save the class names so the predictor knows the order
np.save("gesture_classes.npy", encoder.classes_)

# --- One-hot encode for softmax output ---
y_onehot = tf.keras.utils.to_categorical(y_encoded, num_classes)

# --- Train/test split ---
X_train, X_test, y_train, y_test = train_test_split(X, y_onehot, test_size=0.3, random_state=42)

# --- Build the network ---
model = tf.keras.Sequential([
    tf.keras.layers.Input(shape=(42,)),           # 42 landmark features
    tf.keras.layers.Dense(80, activation="relu"), # hidden layer 1
    tf.keras.layers.Dropout(0.3),                 # prevents overfitting
    tf.keras.layers.Dense(40, activation="relu"), # hidden layer 2
    tf.keras.layers.Dense(num_classes, activation="softmax")  # output: one per gesture
])

model.summary()

model.compile(
    optimizer="adam",
    loss="categorical_crossentropy",
    metrics=["accuracy"]
)

# --- Train ---
model.fit(
    X_train, y_train,
    epochs=100,
    batch_size=8,
    validation_data=(X_test, y_test)
)

# --- Evaluate ---
loss, acc = model.evaluate(X_test, y_test)
print(f"\nTest accuracy: {acc:.2%}")

# --- Save the model ---
model.save("gesture_model.keras")
print("Model saved to gesture_model.keras")
```

---

### 🤖 Claude · 2026-05-04 11:52

Two issues are clear from the output:

1. `Classes: [nan]` — the "label" column isn't being found, so `y` is all NaN. The CSV likely has a different column name or the label column is named differently.

2. `expected axis -1 of input shape to have value 42, but received input with shape (None, 83)` — X has 83 columns, not 42. The CSV has more columns than expected.

The root cause is likely that the CSV's label column isn't named "label" — it might be the first column or named something else. When `df.drop("label", axis=1)` fails silently (or the label column doesn't exist), all columns including the actual label column remain in X.

Actually wait - if `df.drop("label", axis=1)` raised an error it would crash. But it didn't crash, which means there IS a column called "label" but it contains NaN values, and the actual gesture labels are in a different column.

So the CSV probably has:
- A column with gesture names (like "gesture" or the first column)
- A column called "label" that's empty/NaN
- 83 numeric columns (not 42)

The fix: they need to inspect their CSV to find the right label column name, and also figure out why there are 83 features instead of 42.

Let me suggest adding a print of the columns to diagnose, then fix accordingly.You have two distinct problems revealed by the output:

**Problem 1: `Classes: [nan]`** — The label column isn't named `"label"` in your CSV. `df.drop("label", ...)` silently failed (or dropped an empty column), so `y` is full of NaN values.

**Problem 2: shape `(None, 83)` instead of `(None, 42)`** — Your CSV has 83 numeric columns, not 42. You likely have data for **two hands** (21 landmarks × 2 × 2 coords = 84, minus the label = 83), or extra columns you didn't expect.

---

**Step 1 — Diagnose your CSV first.** Add this and run it:

```python
df = pd.read_csv("1gesture_data.csv")
print("Shape:", df.shape)
print("Columns:", df.columns.tolist())
print(df.head(2))
```

---

**Step 2 — Fix based on what you find.** Here's the corrected script with dynamic shape detection so it adapts to whatever your CSV actually contains:

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

model.save("gesture_model.keras")
print("Model saved to gesture_model.keras")
```

The key changes are:
- `LABEL_COL` — change this string to match your actual column name once you see the output of `df.columns`
- `Input(shape=(num_features,))` — reads the real feature count from the data instead of assuming 42

---
claude-conversations-hub gesture-recognition-model-training-error

## Tags
#claude-conversations-hub #gesture #gesture-recognition-model-training-error
