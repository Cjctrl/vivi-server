---
tags: [user, numpy_float64_xcor_attribute_error, claude, ai-conversation]
---



# Numpy float64 xcor attribute error

**Created:** 2026-04-24 16:32  
**Updated:** 2026-04-24 16:48

> Part of [[Claude Conversations Hub]]

---

### 🧑 CJ · 2026-04-24 16:32

File "c:\pyhton projects 2026\neuralnetwork\singleoutputNN.py", line 130, in get_inputs
    dx     = (target.xcor() - head.xcor()) / 290
              ^^^^^^^^^^^
AttributeError: 'numpy.float64' object has no attribute 'xcor'

---

### 🤖 Claude · 2026-04-24 16:32

The error is because `target` (the turtle object) is being overwritten by this line in the main loop:

```python
target = reward + gamma * future_values
```

The variable name `target` is used both for the turtle object and as a variable for the TD target value in the weight update. This shadows the turtle object.## The Bug: Variable Name Collision

On line 130, `target` is expected to be your turtle object, but it's being overwritten in the main loop here:

```python
# This line clobbers your turtle!
target = reward + gamma * future_values
update_weights(inputs, target, chosen_index)
```

You used `target` for both the **turtle sprite** and the **TD learning target value**. After the first iteration, `target` becomes a `numpy.float64`, so `target.xcor()` fails.

**Fix:** Rename the TD target variable to something distinct, like `td_target`:

```python
# Before (broken)
target = reward + gamma * future_values
update_weights(inputs, target, chosen_index)

# After (fixed)
td_target = reward + gamma * future_values
update_weights(inputs, td_target, chosen_index)
```

And the same rename applies inside `update_weights` — there's also a stray reference to `target` and `scores` in the second half of that function (which looks like leftover dead code after the early `return`-style clip):

```python
def update_weights(inputs, reward, chosen_index):
    global W1, W2

    hidden = relu(inputs @ W1)

    delta2 = np.zeros(4)
    delta2[chosen_index] = np.clip(reward, -2.0, 2.0)

    W2 += alpha * np.outer(hidden, delta2)

    delta1 = (delta2 @ W2.T) * (hidden > 0)
    W1 += alpha * np.outer(inputs, delta1)

    W1 = np.clip(W1, -5.0, 5.0)
    W2 = np.clip(W2, -5.0, 5.0)

    # ↓ DELETE everything below here — it's dead code that also references
    #   the now-undefined 'target' and 'scores' variables
    # delta2 = np.zeros(4)
    # delta2[chosen_index] = target - scores[chosen_index]
    # ...
```

The second block inside `update_weights` (after the clip) references `target` and `scores` which aren't parameters — that's a second bug hiding in the same function. Just delete those lines since the first block already does the correct update.

---

### 🧑 CJ · 2026-04-24 16:44

the behavoir seems worst than the prevoise version

---

### 🤖 Claude · 2026-04-24 16:44

The user is saying the behavior is worse than before. Let me analyze the code carefully for issues affecting learning quality.

Key issues I can spot:

1. **`steps_since_solve` logic is wrong** - It only increments when the reset timeout fires, but the comment says "increment every step". Also, `steps_since_solve` is used to penalize every 151 steps, but it's only incremented on timeout resets, not every step. The condition `if steps_since_solve > 0 and steps_since_solve % 151 == 0` will basically never fire usefully.

2. **The "wall penalty" is applied to unsafe moves that were already overridden** - When `new_dir` is unsafe, the code picks a random safe direction instead. But then `if not is_safe(new_dir): reward -= 2` still penalizes based on the original `new_dir`, even though the agent actually moved somewhere safe. This means the agent gets punished for moves it didn't make, corrupting learning.

3. **`update_weights` clips the reward to `[-2.0, 2.0]` but the solve bonus is `10.0`** - The big reward for solving gets clipped down to 2.0, diminishing the positive reinforcement signal for actually reaching the target.

4. **W1/W2 not loaded from saved game data** - `load_game_data()` loads the JSON but the weights `W1` and `W2` are always re-randomized. The saved weights are never restored.

5. **`gamma = 0.3`** - This was changed from `0.9` to `0.3`, which significantly reduces how much the agent values future rewards. This could make it more myopic/greedy.

6. **`epsilon = 0.20`** - Changed from `0.55`, so less exploration now, which might cause it to get stuck in local optima early.

These are the main issues. Let me focus on the most impactful ones:

1. Wall penalty bug (penalizing overridden moves)
2. Solve reward being clipped to 2.0
3. W1/W2 not loaded from save file
4. gamma change (0.9→0.3 makes it shortsighted)

The wall penalty bug and the clipped solve reward are probably the biggest behavioral issues.Looking at the updated code, there are a few things likely causing the regression:

## 1. Wall Penalty Fires on Overridden Moves (Biggest Issue)

The agent picks an unsafe direction, gets overridden to a safe one, but still gets punished for the original choice:

```python
# Agent wanted to go unsafe, so we redirected it...
if is_safe(new_dir):
    head.direction = new_dir
else:
    safe = [d for d in DIRECTIONS if is_safe(d)]
    if safe:
        head.direction = random.choice(safe)  # moved somewhere SAFE

# ...but this still punishes based on new_dir (the original unsafe pick)
if not is_safe(new_dir):
    reward -= 2   # ← penalising a move that never happened!
```

Fix — only penalize if the agent actually hit a wall:

```python
actually_moved = head.direction  # whatever direction was actually used
if not is_safe(actually_moved):
    reward -= 2
```

## 2. Solve Reward Gets Clipped to 2.0

Inside `update_weights`, the reward is clipped to `[-2.0, 2.0]`, which destroys the `10.0` bonus you pass on solve:

```python
delta2[chosen_index] = np.clip(reward, -2.0, 2.0)  # 10.0 → 2.0, same as a normal step
```

Fix — either raise the clip ceiling or pass the solve bonus through a separate path:

```python
delta2[chosen_index] = np.clip(reward, -10.0, 10.0)
```

## 3. Saved Weights Are Never Restored

`load_game_data()` loads the JSON, but W1/W2 are always re-randomized after:

```python
game_data = load_game_data()   # loads W1/W2 lists from JSON...
# ...
W1 = np.random.randn(8, 12) * 0.5   # ← immediately overwrites them!
W2 = np.random.randn(12, 4) * 0.5
```

Fix:

```python
game_data = load_game_data()
mazzed_solvd = game_data["mazzed_solvd"]
iterations   = game_data["iterations"]

if "W1" in game_data and "W2" in game_data:
    W1 = np.array(game_data["W1"])
    W2 = np.array(game_data["W2"])
else:
    W1 = np.random.randn(8, 12) * 0.5
    W2 = np.random.randn(12, 4) * 0.5
```

## 4. Hyperparameter Changes Hurt Learning

| Parameter | Old | New | Effect |
|-----------|-----|-----|--------|
| `gamma` | 0.9 | 0.3 | Agent now ignores future rewards — very shortsighted |
| `epsilon` | 0.55 | 0.20 | Much less exploration early on, gets stuck in bad habits faster |

Revert `gamma` back to `0.9` especially — a value of `0.3` means the agent barely considers what happens two steps ahead.

---

### 🧑 CJ · 2026-04-24 16:48

doesnt move anymore

---

### 🤖 Claude · 2026-04-24 16:48

Looking at the code, I can see several issues:

1. The weights are loaded from JSON but then immediately overwritten by random initialization:

```python
if "W1" in game_data and "W2" in game_data:
    W1 = np.array(game_data["W1"])
    W2 = np.array(game_data["W2"])
else:
    W1 = np.random.randn(8, 12) * 0.5
    W2 = np.random.randn(12, 4) * 0.5
```

Then later:
```python
W1 = np.random.randn(8, 12) * 0.5   # overwrites the loaded weights!
W2 = np.random.randn(12, 4) * 0.5
```

2. The wall penalty and direction setting logic is broken. The original fix I suggested was to set `actually_moved` after setting `head.direction`, but in the current code:

```python
# 4. Pick a safe direction (wall avoidance)
actually_moved = head.direction  # this is BEFORE setting direction!
if not is_safe(actually_moved):
    reward -= 2
```

But `reward` hasn't been defined yet at this point! The reward is calculated AFTER moving. So this penalty fires before reward is even set, and then `reward` gets overwritten by `improvement / 20` anyway.

Also, the direction-setting code is MISSING entirely! The code that was:
```python
if is_safe(new_dir):
    head.direction = new_dir
else:
    safe = [d for d in DIRECTIONS if is_safe(d)]
    if safe:
        head.direction = random.choice(safe)
```
...has been replaced by just the penalty check, so `head.direction` never gets updated from `new_dir`. That's why it doesn't move - the direction never gets set!

3. The old wall penalty `if not is_safe(new_dir): reward -= 2` is still there after the reward calculation.

Let me write a clean fixed version.The agent stopped moving because the direction-setting code got accidentally deleted when you reorganized the wall penalty. Here are all the issues:

## 1. Direction Is Never Set (Why It Doesn't Move)

This block that sets `head.direction` is completely missing:

```python
# This is GONE from your code — add it back!
if is_safe(new_dir):
    head.direction = new_dir
else:
    safe = [d for d in DIRECTIONS if is_safe(d)]
    if safe:
        head.direction = random.choice(safe)
```

## 2. Wall Penalty Runs Before `reward` Is Defined

Your early penalty block fires before `reward` is ever assigned, then gets overwritten anyway:

```python
actually_moved = head.direction
if not is_safe(actually_moved):
    reward -= 2   # ← 'reward' doesn't exist yet here!

move()
# ...
reward = improvement / 20  # ← overwrites the penalty above
# ...
if not is_safe(new_dir):   # ← old penalty still here too
    reward -= 2
```

## 3. Weights Still Get Overwritten

The loaded weights are still being clobbered by the random init below them:

```python
# This block correctly loads saved weights...
if "W1" in game_data:
    W1 = np.array(game_data["W1"])
# ...
# Then these lines immediately overwrite them:
W1 = np.random.randn(8, 12) * 0.5   # ← DELETE these two lines
W2 = np.random.randn(12, 4) * 0.5   # ← DELETE these two lines
```

## Clean Main Loop (Fixed)

Here's the corrected loop section:

```python
while True:
    inputs = get_inputs()
    scores = forward(inputs)

    if random.random() < epsilon:
        new_dir = random.choice(DIRECTIONS)
    else:
        new_dir = pick_direction(scores)

    chosen_index = DIRECTIONS.index(new_dir)
    epsilon = max(epsilon_min, epsilon * epsilon_decay)

    prev_dist = ((head.xcor() - target.xcor())**2 +
                 (head.ycor() - target.ycor())**2) ** 0.5

    # Set direction (safe override)
    if is_safe(new_dir):
        head.direction = new_dir
        actually_moved = new_dir
    else:
        safe = [d for d in DIRECTIONS if is_safe(d)]
        if safe:
            actually_moved = random.choice(safe)
            head.direction = actually_moved
        else:
            actually_moved = new_dir  # stuck — no safe moves

    move()

    next_input = get_inputs()
    future_values = np.max(forward(next_input))

    new_dist = ((head.xcor() - target.xcor())**2 +
                (head.ycor() - target.ycor())**2) ** 0.5

    improvement = prev_dist - new_dist
    reward = improvement / 20

    if not is_safe(actually_moved):
        reward -= 2

    if steps_since_solve > 0 and steps_since_solve % 151 == 0:
        reward -= 0.4

    td_target = reward + gamma * future_values
    update_weights(inputs, td_target, chosen_index)

    if new_dist < 20:
        mazzed_solvd += 1
        last_solved_time = time.time()
        steps_since_solve = 0
        head.goto(0, 0)
        while True:
            tx = random.randrange(-260, 260, 20)
            ty = random.randrange(-260, 260, 20)
            if not (abs(tx - barrier.xcor()) < 280 and abs(ty - barrier.ycor()) < 20):
                target.goto(tx, ty)
                break
        update_weights(inputs, 10.0, chosen_index)

    if time.time() - last_solved_time > RESET_TIMEOUT:
        head.goto(0, 0)
        head.direction = "stop"
        last_solved_time = time.time()
        steps_since_solve += 1

    iterations += 1
    refresh_hud()
    wn.update()

    if iterations % 100 == 0:
        save_game_data(mazzed_solvd, iterations)

    time.sleep(delay)
```

---
claude-conversations-hub numpy-float64-xcor-attribute-error

## Tags
#claude-conversations-hub #numpy #numpy-float64-xcor-attribute-error
