---
tags: [user, neural_network_weights_becoming_nan, machine-learning, artificial-intelligence, claude, ai-conversation]
---



# Neural network weights becoming NaN

**Created:** 2026-04-24 14:23  
**Updated:** 2026-04-24 14:24

> Part of [[Claude Conversations Hub]]

---

### 🧑 CJ · 2026-04-24 14:23

i dont know much about json diles but im getting a NaN after a while

```json
{
  "mazzed_solvd": 260,
  "iterations": 36000,
  "W1": [
    [
      NaN,
      NaN,
      NaN,
      NaN,
      NaN,
      NaN,
      NaN,
      NaN,
      NaN,
      NaN,
      NaN,
      NaN
    ],
    [
      NaN,
      NaN,
      NaN,
      NaN,
      NaN,
      NaN,
      NaN,
      NaN,
      NaN,
      NaN,
      NaN,
      NaN
    ],
    [
      NaN,
      NaN,
      NaN,
      NaN,
      NaN,
      NaN,
      NaN,
      NaN,
      NaN,
      NaN,
      NaN,
      NaN
    ],
    [
      NaN,
      NaN,
      NaN,
      NaN,
      NaN,
      NaN,
      NaN,
      NaN,
      NaN,
      NaN,
      NaN,
      NaN
    ],
    [
      NaN,
      NaN,
      NaN,
      NaN,
      NaN,
      NaN,
      NaN,
      NaN,
      NaN,
      NaN,
      NaN,
      NaN
    ],
    [
      NaN,
      NaN,
      NaN,
      NaN,
      NaN,
      NaN,
      NaN,
      NaN,
      NaN,
      NaN,
      NaN,
      NaN
    ],
    [
      NaN,
      NaN,
      NaN,
      NaN,
      NaN,
      NaN,
      NaN,
      NaN,
      NaN,
      NaN,
      NaN,
      NaN
    ],
    [
      NaN,
      NaN,
      NaN,
      NaN,
      NaN,
      NaN,
      NaN,
      NaN,
      NaN,
      NaN,
      NaN,
      NaN
    ]
  ],
  "W2": [
    [
      NaN,
      NaN,
      NaN,
      NaN
    ],
    [
      NaN,
      NaN,
      NaN,
      NaN
    ],
    [
      NaN,
      NaN,
      NaN,
      NaN
    ],
    [
      NaN,
      NaN,
      NaN,
      NaN
    ],
    [
      NaN,
      NaN,
      NaN,
      NaN
    ],
    [
      NaN,
      NaN,
      NaN,
      NaN
    ],
    [
      NaN,
      NaN,
      NaN,
      NaN
    ],
    [
      NaN,
      NaN,
      NaN,
      NaN
    ],
    [
      NaN,
      NaN,
      NaN,
      NaN
    ],
    [
      NaN,
      NaN,
      NaN,
      NaN
    ],
    [
      NaN,
      NaN,
      NaN,
      NaN
    ],
    [
      NaN,
      NaN,
      NaN,
      NaN
    ]
  ]
}
```

---

### 🤖 Claude · 2026-04-24 14:24

The user is getting NaN in their neural network weights. This is a classic "exploding gradients" problem. Let me analyze the code.

The issue is in `update_weights`:

```python
def update_weights(inputs, reward, chosen_index):
    global W1, W2
    hidden = relu(inputs @ W1)
    delta2 = -forward(inputs)            # push all scores down
    delta2[chosen_index] += reward       # reward the action taken
    W2 += learning_rate * np.outer(hidden, delta2)
    delta1 = (delta2 @ W2.T) * (hidden > 0)
    W1 += learning_rate * np.outer(inputs, delta1)
```

Problems:
1. `delta2 = -forward(inputs)` — this uses the current output scores as the gradient signal. As weights grow, scores grow, making delta2 larger, which makes weight updates larger... exploding gradients.
2. The reward can be called multiple times — once normally and again with `update_weights(inputs, 10.0, chosen_index)` when target is reached. Also `mazzed_solvd` is incremented twice when target is reached.
3. No gradient clipping.

The fix:
1. Add gradient clipping in `update_weights`
2. Use a simpler, more stable gradient formulation
3. Fix the double-increment of mazzed_solvd

The main cause of NaN is exploding gradients. The `delta2 = -forward(inputs)` line uses the raw output scores which grow unboundedly, creating a feedback loop.

Simple fixes:
1. Clip gradients: `np.clip(delta2, -1, 1)` and similar
2. Or use a simpler policy gradient: just set `delta2 = np.zeros(4); delta2[chosen_index] = reward`
3. Add weight clipping/normalization

Also there's a bug: `mazzed_solvd` is incremented twice (once in the `if new_dist < 20` block, then again in the second `if new_dist < 20` block).

Let me explain this clearly and give the fixes.The NaN values mean your weights have **exploded** — they grew so large they overflowed to infinity, and `inf - inf = NaN`. Once one weight hits NaN, it spreads to everything like a virus through the matrix math.

There are two causes in your code:

**Cause 1 — Unstable gradient in `update_weights`**

```python
delta2 = -forward(inputs)   # ← THIS is the problem
```

`forward(inputs)` returns the raw output scores. As weights grow, scores grow, making `delta2` bigger, which makes weight updates bigger, which makes scores bigger... it's a feedback loop that eventually explodes. The fix is to just describe what you *want* directly instead:

```python
# Replace the whole delta2 block with this:
delta2 = np.zeros(4)
delta2[chosen_index] = reward   # only nudge the action you actually took
```

**Cause 2 — No gradient clipping**

Even with the above fix, a lucky string of large rewards can still push weights too hard. Add a clip:

```python
def update_weights(inputs, reward, chosen_index):
    global W1, W2

    hidden = relu(inputs @ W1)

    delta2 = np.zeros(4)
    delta2[chosen_index] = np.clip(reward, -2.0, 2.0)  # clamp reward too

    W2 += learning_rate * np.outer(hidden, delta2)

    delta1 = (delta2 @ W2.T) * (hidden > 0)
    W1 += learning_rate * np.outer(inputs, delta1)

    # Clip weights so they can never explode
    W1 = np.clip(W1, -5.0, 5.0)
    W2 = np.clip(W2, -5.0, 5.0)
```

**Bonus bug — `mazzed_solvd` increments twice**

You have two separate `if new_dist < 20` blocks back to back, so every solve counts double:

```python
# FIRST block — keep this one (has the reset logic)
if new_dist < 20:
    mazzed_solvd += 1
    last_solved_time = time.time()
    steps_since_solve = 0
    head.goto(0, 0)
    target.goto(
        random.randrange(-260, 260, 20),
        random.randrange(-260, 260, 20)
    )
    update_weights(inputs, 10.0, chosen_index)  # move the bonus here

# DELETE the second `if new_dist < 20` block entirely
```

**Also — delete your `game_data.json` before restarting**, since it currently has all-NaN weights. Your `load_game_data` loads W1/W2 if they exist in the file, so it'll immediately poison your fresh weights on startup.

---
claude-conversations-hub neural-network-weights-becoming-nan

## Tags
#claude-conversations-hub #neural #neural-network-weights-becoming-nan
