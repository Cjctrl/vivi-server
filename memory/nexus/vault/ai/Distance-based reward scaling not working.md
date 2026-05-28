---
tags: [user, distance_based_reward_scaling_not_working, claude, ai-conversation]
---



# Distance-based reward scaling not working

**Created:** 2026-04-23 15:15  
**Updated:** 2026-04-23 15:36

> Part of [[Claude Conversations Hub]]

---

### 🧑 CJ · 2026-04-23 15:15

im trying to make it so the further away from food the less reward im confuesed about why its not working

---

### 🤖 Claude · 2026-04-23 15:16

Looking at the code, I can see the bug. In the main game loop, the `calculate_reward` call has the arguments in the wrong order.

In `neural_network.py`, the signature is:
```python
def calculate_reward(food_farness, ate_food, is_moving, time_score_increment=0.1)
```

But in the game loop:
```python
reward = SnakeNN.calculate_reward(ate_food, is_moving, time_increment, food_farness)
```

The arguments are passed in the wrong order! `ate_food` is being passed as `food_farness`, and `food_farness` is being passed as `time_score_increment`.

Also, `food_farness` is defined as `dist_to_food > 20` which is basically always True since the snake needs to be within 20 to eat food. It should probably be a comparison to previous distance to check if the snake is getting farther.There are two bugs here.

**Bug 1: Wrong argument order in the `calculate_reward` call** (main game file, line ~step 6)

The function signature is:
```python
def calculate_reward(food_farness, ate_food, is_moving, time_score_increment)
```

But you're calling it as:
```python
reward = SnakeNN.calculate_reward(ate_food, is_moving, time_increment, food_farness)
```

So `food_farness` is being silently passed as `time_score_increment` and never actually used. Fix:
```python
reward = SnakeNN.calculate_reward(food_farness, ate_food, is_moving, time_increment)
```

---

**Bug 2: `food_farness` is almost always `True`**

```python
food_farness = dist_to_food > 20
```

Since the snake only eats food when `dist_to_food < 20`, this flag is `True` on basically every single frame, meaning the penalty fires constantly regardless of whether the snake is actually moving *away* from food.

What you actually want is to compare the distance to the *previous* frame's distance:

```python
# Before move(), save the old distance
prev_dist_to_food = ((head.xcor() - food.xcor())**2 + (head.ycor() - food.ycor())**2)**0.5

# ...then after move():
dist_to_food  = ((head.xcor() - food.xcor())**2 + (head.ycor() - food.ycor())**2)**0.5
ate_food      = dist_to_food < 20
food_farness  = dist_to_food > prev_dist_to_food  # True only when snake moved AWAY
```

This way `food_farness` correctly penalises steps where the snake increased its distance from food, and rewards steps where it got closer.

---

### 🧑 CJ · 2026-04-23 15:23

could you see how i weight the models rewards to ins\centivise to goto food more

---

### 🤖 Claude · 2026-04-23 15:23

Looking at the reward function:

```python
@staticmethod
def calculate_reward(
    food_farness: bool,
    ate_food: bool,
    is_moving: bool,
    time_score_increment: float = 0.1,
) -> float:
    reward = 0.0
    if ate_food:
        reward += 1.0
    if is_moving:
        reward += time_score_increment * 0.45   # proportional time bonus
        reward += 0.3                          
        if food_farness:
            reward -= 0.8     # small punishment for getting farther from food
    else:
        reward -= 1.0                          # inactivity penalty
    return reward
```

Issues I see:
1. There's no positive reward for getting *closer* to food - only a penalty for moving away. Asymmetric.
2. The moving reward (+0.3 flat + 0.045 from time) = ~0.345 per frame just for moving, but the farness penalty is only -0.8. So moving away still gives net +0.3 + 0.045 - 0.8 = -0.455, while moving closer gives +0.345. The asymmetry might be okay but the base moving reward is quite high.
3. The food reward of +1.0 is quite low relative to the per-frame survival rewards. If the snake lives 100 frames, it gets ~34.5 just for moving, but only +1.0 for eating. So survival is incentivized more than food-seeking.

Suggestions:
- Increase food reward significantly (e.g., +5.0 or +10.0)
- Add a positive reward for getting closer to food (mirror the farness penalty)
- Remove or reduce the flat moving reward (+0.3) since it incentivizes survival over food-seekingLooking at your reward function, there are a few weighting issues working against food-seeking:

```python
if is_moving:
    reward += time_score_increment * 0.45   # ~+0.045
    reward += 0.3                           # flat survival bonus
    if food_farness:
        reward -= 0.8                       # penalty for moving away
```

**Problem 1: Survival reward drowns out food incentive**
Every moving frame gives `+0.345` just for being alive, but eating food only gives `+1.0`. Over a 50-frame game the snake earns `~17` points just surviving vs `+1.0` for food — so it learns to survive, not eat.

**Problem 2: Asymmetric food distance signal**
You punish moving *away* (`-0.8`) but give nothing for moving *closer*. The signal is one-sided and weak.

**Problem 3: No "closer = good" reward**
The snake has no positive pull toward food, only a negative push away from it.

Here's a rebalanced version:

```python
@staticmethod
def calculate_reward(food_farness, ate_food, is_moving, time_score_increment=0.1):
    reward = 0.0

    if ate_food:
        reward += 10.0          # much stronger food incentive

    if is_moving:
        reward += 0.01          # tiny survival bonus (not competing with food)
        if food_farness:
            reward -= 0.5       # penalty for moving away
        else:
            reward += 0.3       # positive pull for moving toward food
    else:
        reward -= 1.0

    return reward
```

The key changes are: **eating is now 10x more valuable**, the **survival bonus is nearly eliminated** so it stops competing, and moving *closer* to food now gives a **positive reward** rather than just punishing moving away.

---

### 🧑 CJ · 2026-04-23 15:31

i added that element but now its giving me AttributeError: 'SnakeNN' object has no attribute 'load'
PS C:\pyhton projects 2026\ai snakeV2> & C:/Users/cjpen/AppData/Local/Microsoft/WindowsApps/python3.12.exe "c:/pyhton projects 2026/ai snakeV2/snakeGame.py"
Traceback (most recent call last):
  File "c:\pyhton projects 2026\ai snakeV2\snakeGame.py", line 39, in <module>
    nn.load()   # load previous weights if they exist
    ^^^^^^^
AttributeError: 'SnakeNN' object has no attribute 'load'
PS C:\pyhton projects 2026\ai snakeV2>  but all i replaced was the reward function

---

### 🤖 Claude · 2026-04-23 15:32

The error is about `load` method not found, but the user says they only changed the reward function. The issue is likely a syntax error in the reward function that's causing the class to not fully load, which would make methods defined after it unavailable.

Looking at the class, `load` is defined after `calculate_reward`. If there's a syntax error in `calculate_reward`, Python won't finish parsing the class, so `load` won't exist.

The user should check for a syntax error in their updated `calculate_reward` method.The `load` method definitely exists in your original code — this error means Python **failed to fully parse the class**, so it stopped before reaching `load`. A syntax error in your updated reward function would cause exactly this.

Check your new `calculate_reward` for common mistakes:

**Indentation issues:**
```python
# Wrong - mixed tabs/spaces or wrong indent level
@staticmethod
def calculate_reward(food_farness, ate_food, is_moving, time_score_increment=0.1):
reward = 0.0  # ← not indented!
```

**Missing colon or mismatched brackets:**
```python
def calculate_reward(food_farness, ate_food, is_moving, time_score_increment=0.1)  # ← missing colon
```

To get the exact line, run this in your terminal:
```
python -c "import py_compile; py_compile.compile('nerualnetwork.py', doraise=True)"
```

That will tell you precisely which line the syntax error is on. Paste the output here and I can fix it directly.

Also worth noting — your import in `snakeGame.py` is:
```python
from nerualnetwork import SnakeNN
```
Make sure the filename is still `nerualnetwork.py` (with the typo) and hasn't been accidentally renamed.

---

### 🧑 CJ · 2026-04-23 15:35

PS C:\pyhton projects 2026\ai snakeV2> & C:/Users/cjpen/AppData/Local/Microsoft/WindowsApps/python3.12.exe "c:/pyhton projects 2026/ai snakeV2/snakeGame.py"
Traceback (most recent call last):
  File "c:\pyhton projects 2026\ai snakeV2\snakeGame.py", line 39, in <module>
    nn.load()   # load previous weights if they exist
    ^^^^^^^
AttributeError: 'SnakeNN' object has no attribute 'load'
PS C:\pyhton projects 2026\ai snakeV2> python -c "import py_compile; py_compile.compile('nerualnetwork.py', doraise=True)"
PS C:\pyhton projects 2026\ai snakeV2>

---

### 🤖 Claude · 2026-04-23 15:35

The compile check passed with no errors, so it's not a syntax issue. The problem must be that Python is importing an old cached version of the file, or there are two files and it's loading the wrong one.

Most likely cause: there's a `nerualnetwork.pyc` cached file or `__pycache__` that's stale, OR there are two copies of the file and one doesn't have the `load` method.The syntax check passed clean, so it's a **stale cache** issue. Python is importing a cached `.pyc` file that predates your changes.

Fix it by deleting the cache:

```
Remove-Item -Recurse -Force __pycache__
```

Then run the game again. That forces Python to re-read the actual `.py` file.

If it still fails after that, there's likely a **second copy** of the file somewhere. Check with:

```
Get-ChildItem -Recurse -Filter "nerualnetwork.py" C:\
```

If two copies show up, the wrong one is being imported — make sure your edits are in the one sitting in `C:\pyhton projects 2026\ai snakeV2\`.

---

### 🤖 Claude · 2026-04-23 15:36

The search found two copies:
- `C:\pyhton projects 2026\ai snake\nerualnetwork.py` (old, 5775 bytes)
- `C:\pyhton projects 2026\ai snakeV2\nerualnetwork.py` (new, 12885 bytes)

The snakeGame.py is in `ai snakeV2` but Python might be picking up the one from `ai snake`. Wait, but the import is a relative import - it should pick up the one in the same directory. 

Actually the issue is likely that Python's working directory when running the script might be different, or there's a `nerualnetwork.pyc` somewhere.

Actually wait - looking more carefully. The script is run as:
`& C:/Users/cjpen/AppData/Local/Microsoft/WindowsApps/python3.12.exe "c:/pyhton projects 2026/ai snakeV2/snakeGame.py"`

When Python runs a script, it adds the script's directory to `sys.path`. So it should find `ai snakeV2\nerualnetwork.py`. But there's also `ai snake\nerualnetwork.py`.

Hmm, but the `ai snake` folder wouldn't be on sys.path unless the user navigated there. The terminal is in `ai snakeV2` so that's on sys.path too.

Actually - the most likely explanation is that `snakeGame.py` is importing from the OLD `ai snake` folder somehow, OR the `nerualnetwork.py` in `ai snakeV2` doesn't have the `load` method because the user's edits somehow removed it.

Wait - the file sizes: old one is 5775 bytes, new one is 12885 bytes. The new one should have everything. 

But actually - could it be that the user accidentally saved their edits to the wrong file? Or could there be an issue where the `snakeGame.py` is somehow resolving to the `ai snake` directory?

The most direct fix: tell them to add a debug print to verify which file is being imported.

Actually the simplest thing - run:
`python -c "import nerualnetwork; print(nerualnetwork.__file__)"`

from the `ai snakeV2` directory to see which file is actually being loaded.There are two copies of the file found — that's the problem. Python might be loading the old one from `ai snake` instead of `ai snakeV2`. Let's confirm exactly which file is being imported:

Run this from your terminal (while in the `ai snakeV2` directory):

```
python -c "import nerualnetwork; print(nerualnetwork.__file__)"
```

If it prints the `ai snake` path instead of `ai snakeV2`, that's your culprit — the old folder is somehow on Python's path.

The quickest fix either way is to **add this at the top of `snakeGame.py`**, before the import:

```python
import sys
sys.path.insert(0, r"C:\pyhton projects 2026\ai snakeV2")
```

This forces Python to look in your V2 folder first, regardless of what else is on the path. Once the game is running correctly you can remove it, or just leave it in — it won't cause any harm.

---
claude-conversations-hub distance-based-reward-scaling-not-working

## Tags
#claude-conversations-hub #distance #distance-based-reward-scaling-not-working
