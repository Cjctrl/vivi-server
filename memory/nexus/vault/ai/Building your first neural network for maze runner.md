---
tags: [user, building_your_first_neural_network_for_maze_runner, machine-learning, artificial-intelligence, claude, ai-conversation]
---



# Building your first neural network for maze runner

**Created:** 2026-04-23 23:30  
**Updated:** 2026-04-24 00:22

> Part of [[Claude Conversations Hub]]

---

### 🧑 CJ · 2026-04-23 23:30

ok so im trying to build a really simple nureal network that will go to object its gonna be a mazz runner and itll this is my first NN take me step by step

---

### 🤖 Claude · 2026-04-23 23:31

The user wants to build a simple neural network for a maze runner that navigates to an object. Let me look at their code and guide them step by step. They're a beginner with NNs.

Let me analyze their current code:
1. They have a turtle graphics setup with a "head" (agent) and a "red object" (target)
2. Their "neural network" is really just a decision tree based on boolean logic
3. The inputs are: distance to object, and two random numbers - this is not useful
4. There's no actual learning happening

Let me think about what a real simple NN maze runner would look like for a beginner:

A proper simple approach would be:
1. Define useful inputs (direction to target, wall proximity)
2. Have actual weights
3. Have a way to update weights (backprop or even simpler - genetic/reward-based)

Let me plan a step-by-step guide:

**Step 1: Fix your inputs** - The inputs should be meaningful:
- dx = object.xcor() - head.xcor() (horizontal distance)
- dy = object.ycor() - head.ycor() (vertical distance)
- Maybe wall distances

**Step 2: Build a real (simple) NN structure** - weights, forward pass

**Step 3: Add learning** - since this is reinforcement-style, we can use a simple reward signal

For a true beginner NN, I'd suggest:
- 4 inputs: normalized dx, dy, and maybe 2 more (wall distances or random noise removed)
- 4 outputs: one per direction (up/down/left/right)
- softmax or argmax to pick direction
- Simple weight update based on reward (did we get closer?)

Let me outline this clearly and help them rewrite step by step.

I'll walk through:
1. What's wrong with current code (not a real NN, inputs are random/useless)
2. What a real simple NN looks like
3. Step-by-step rebuild

I should be encouraging since it's their first NN attempt.Great first attempt! You've got the turtle framework and the general idea down. Let me walk you through what needs to change to make this an *actual* neural network, step by step.

---

## What's happening in your current code (and the problems)

**Your "inputs" aren't useful:**
```python
obj1 = at_object        # distance — ok!
obj2 = random.randint(0, 4)  # ❌ pure noise
obj3 = random.randint(0, 4)  # ❌ pure noise
```
A NN can't learn from random inputs. You need inputs that *describe the situation*.

**Your `choice()` function is just an `if/else` tree** — no weights, no math, no learning. A real NN multiplies inputs by weights and learns by adjusting those weights.

**There's no learning loop** — the agent never gets better because nothing updates.

---

## The Plan (4 steps)

### Step 1 — Fix your inputs

Replace the 3 random values with 4 *meaningful* numbers:

| Input | Meaning |
|---|---|
| `dx` | How far right/left is the target? |
| `dy` | How far up/down is the target? |
| `wall_x` | How close is the nearest left/right wall? |
| `wall_y` | How close is the nearest top/bottom wall? |

```python
def get_inputs():
    dx = (object.xcor() - head.xcor()) / 290   # normalized -1 to 1
    dy = (object.ycor() - head.ycor()) / 290
    wall_x = head.xcor() / 290                  # how close to left/right wall
    wall_y = head.ycor() / 290                  # how close to top/bottom wall
    return np.array([dx, dy, wall_x, wall_y])
```

---

### Step 2 — Build a real (tiny) NN

4 inputs → hidden layer (6 neurons) → 4 outputs (up/down/left/right)

```python
# Random starting weights
W1 = np.random.randn(4, 6) * 0.5   # input → hidden
W2 = np.random.randn(6, 4) * 0.5   # hidden → output

def relu(x):
    return np.maximum(0, x)

def forward(inputs):
    hidden = relu(inputs @ W1)       # (4,) → (6,)
    output = hidden @ W2             # (6,) → (4,)
    return output                    # raw scores for [up, down, left, right]

def pick_direction(output_scores):
    directions = ["up", "down", "left", "right"]
    return directions[np.argmax(output_scores)]  # pick highest score
```

---

### Step 3 — Add a reward signal

After each move, ask: *did we get closer to the target?*

```python
prev_dist = at_object
move()
new_dist = ((head.xcor() - object.xcor())**2 + (head.ycor() - object.ycor())**2)**0.5

reward = 1.0 if new_dist < prev_dist else -1.0  # got closer = good
```

---

### Step 4 — Update weights (the actual "learning")

This is the simplest possible weight update — nudge the weights in the direction that improved the reward:

```python
learning_rate = 0.01

def update_weights(inputs, reward, chosen_index):
    global W1, W2
    hidden = relu(inputs @ W1)
    
    # nudge W2: reward the output neuron we chose
    delta2 = np.zeros(4)
    delta2[chosen_index] = reward
    W2 += learning_rate * np.outer(hidden, delta2)
    
    # nudge W1 too (backprop simplified)
    delta1 = (delta2 @ W2.T) * (hidden > 0)
    W1 += learning_rate * np.outer(inputs, delta1)
```

---

## What your main loop should look like

```python
while True:
    inputs = get_inputs()
    scores = forward(inputs)
    new_dir = pick_direction(scores)
    chosen_index = ["up","down","left","right"].index(new_dir)

    prev_dist = ((head.xcor()-object.xcor())**2 + (head.ycor()-object.ycor())**2)**0.5
    
    if is_safe(new_dir):
        head.direction = new_dir
    else:
        safe = [d for d in ["up","down","left","right"] if is_safe(d)]
        head.direction = random.choice(safe) if safe else head.direction

    move()

    new_dist = ((head.xcor()-object.xcor())**2 + (head.ycor()-object.ycor())**2)**0.5
    reward = 1.0 if new_dist < prev_dist else -1.0

    update_weights(inputs, reward, chosen_index)

    if new_dist < 20:
        mazzed_solvd += 1
        # reset head position
        head.goto(0, 0)

    iterations += 1
    refresh_hud()
    wn.update()
    time.sleep(delay)
```

---

## Summary of what you'll see

- Early on: the agent wanders randomly (weights are garbage)
- After ~100–500 iterations: it starts drifting toward the target more often
- The `Best:` counter goes up as it learns

Want me to write the full clean version of the file putting all of this together?

---

### 🤖 Claude · 2026-04-24 00:20

The user has tried to implement the suggestions but has several bugs. Let me identify them all and provide a clean, corrected version.

Key issues:
1. `W1` and `W2` are re-initialized inside the while loop every iteration — they reset every step, so no learning happens
2. Functions defined inside the while loop (bad practice)
3. `output_score` typo (should be `output_scores`) in `pick_direction`
4. `new_dist` formula has `-` instead of `+` for the y component, and `head.cyor()` typo
5. `update_weights` is defined outside/after the while loop with wrong indentation
6. `np.zeror` typo (should be `np.zeros`)
7. `hiden` typo (should be `hidden`)
8. `W2.t` should be `W2.T`
9. `input` instead of `inputs` in W1 update
10. `delta` instead of `delta1`
11. The old result-based direction code is still there
12. The main loop doesn't call `get_input()`, `forward()`, `pick_direction()`, or `update_weights()` properly
13. `chosen_index` is never computed in the main loop

Let me write the clean corrected version.You're on the right track, but there are several bugs to fix. Let me go through each one clearly, then give you the clean working version.

---

## Bugs Found

**🔴 Critical — breaks everything:**

| Bug | Where | Problem |
|---|---|---|
| `W1 = np.random.randn(...)` inside `while True` | line ~43 | Weights **reset every single step** — the NN can never learn |
| Functions defined inside `while True` | `get_input`, `relu`, `forward`, etc. | Redefines them every loop — move outside |
| `head.cyor()` | `new_dist` line | Typo — crashes immediately |
| `new_dist` uses `-` instead of `+` | `new_dist` line | Wrong math, would produce `NaN` |
| `update_weights` never called in the loop | — | The learning never actually runs |
| `result == 1/2/3/4` logic still in loop | bottom | Leftover old code, `result` doesn't exist anymore |

**🟡 Typos — silent bugs:**

- `output_score` → should be `output_scores`
- `np.zeror` → `np.zeros`
- `hiden` → `hidden`
- `W2.t` → `W2.T`
- `input` → `inputs`
- `delta` → `delta1`

---

## Clean Working Version
```
This block is not supported on your current device yet.
```

Now let me create a clean, corrected version of the code with all bugs fixed. I'll write it as a file and also show a diagram of the NN architecture.Here's the fully corrected file with every bug fixed and annotated:
```
This block is not supported on your current device yet.
```

Now let me present the file and also show a diagram of the NN architecture.
```
This block is not supported on your current device yet.
```

Here's a summary of every fix made and what it means:

---

**The #1 bug** — `W1` and `W2` were inside `while True`. Every step threw away all learning and started over with random weights. Nothing could ever improve. Moving them outside the loop is what makes the NN actually learn.

**The other critical fixes:**

| Bug | Was | Now | Why it matters |
|---|---|---|---|
| `head.cyor()` | typo | `head.ycor()` | Would crash immediately |
| `new_dist` y-term | `(y)**2 - ...` used `-` | `+ (y)**2` | Wrong math gives `NaN`, kills training |
| `output_score` | missing `s` | `output_scores` | `NameError` crash |
| `np.zeror` | typo | `np.zeros` | `AttributeError` crash |
| `hiden` | typo | `hidden` | `NameError` crash |
| `W2.t` | lowercase `.t` | `.T` | `.t` doesn't exist on numpy arrays |
| `input` / `delta` | wrong variable names | `inputs` / `delta1` | Used wrong variables in backprop |
| `update_weights` never called | — | called in loop | Without this, zero learning happened |
| Functions defined inside loop | — | moved outside | Were being redefined 10+ times/sec |

Now when you run it, you should see the `Solved:` counter start climbing as the NN figures out which directions get it closer to the red square.

---

### 🧑 CJ · 2026-04-24 00:22

so as this model trains will it remeber between boots?

---

### 🤖 Claude · 2026-04-24 00:22

The user is asking if the neural network weights persist between runs of the program.**Right now — no.** The weights `W1` and `W2` are just `np.random.randn(...)` every time the script starts, so all learning is lost on reboot.

The `game_data.json` only saves the score and step count, not the weights.

---

## The fix is simple — save and load the weights just like you do the score

Add this to your save/load functions:

```python
def load_game_data():
    global W1, W2
    try:
        with open("game_data.json", "r") as f:
            data = json.load(f)
        # Load weights if they were saved before
        if "W1" in data and "W2" in data:
            W1 = np.array(data["W1"])
            W2 = np.array(data["W2"])
        return data
    except FileNotFoundError:
        return {"mazzed_solvd": 0, "iterations": 0}

def save_game_data(mazzed_solvd, iterations):
    with open("game_data.json", "w") as f:
        json.dump({
            "mazzed_solvd": mazzed_solvd,
            "iterations":   iterations,
            "W1": W1.tolist(),   # numpy → plain list so JSON can store it
            "W2": W2.tolist()
        }, f, indent=2)
```

The key detail is `.tolist()` — JSON can't store numpy arrays directly, so you convert them to plain Python lists on save, and wrap them back with `np.array()` on load.

---

## One ordering issue to watch

In your current file, `W1` and `W2` are created *before* `load_game_data()` is called. You need to flip that so the load can overwrite the random starting weights:

```python
# Create random weights first (used if no save file exists)
W1 = np.random.randn(4, 6) * 0.5
W2 = np.random.randn(6, 4) * 0.5

# Then immediately try to load saved weights (overwrites the random ones)
game_data    = load_game_data()
mazzed_solvd = game_data["mazzed_solvd"]
iterations   = game_data["iterations"]
```

With that in place, every 100 steps it saves the weights, and next boot it picks up exactly where it left off.

---
building-your-first-neural-network-for-maze-runner claude-conversations-hub

## Tags
#1 #building #building-your-first-neural-network-for-maze-runner #claude-conversations-hub
