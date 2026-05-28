---
tags: [user, maze_solver_crashing_on_target_contact, claude, ai-conversation]
---



# Maze solver crashing on target contact

**Created:** 2026-04-24 16:57  
**Updated:** 2026-04-24 16:57

> Part of [[Claude Conversations Hub]]

---

### 🧑 CJ · 2026-04-24 16:57

```python
    if new_dist < 20:
        mazzed_solvd += 1
        last_solved_time = time.time()
        steps_since_solve = 0
        head.goto(0, 0)
        while True:
             tx = random.randrange(-260, 260, 20)
             ty = random.randrange(-260, 260, 20)
    update_weights(inputs, 10.0, chosen_index)
    ...


#its crashing on contact with target
```

---

### 🤖 Claude · 2026-04-24 16:57

Looking at the code, the issue is clear. When the target is reached, there's a `while True` loop that generates random coordinates but never breaks or sets the target position, causing an infinite loop. Also, the code after the `while True` is misindented.

Here's the fix:

```python
if new_dist < 20:
    mazzed_solvd += 1
    last_solved_time = time.time()
    steps_since_solve = 0
    update_weights(inputs, 10.0, chosen_index)  # reward before reset
    head.goto(0, 0)
    while True:
        tx = random.randrange(-260, 260, 20)
        ty = random.randrange(-260, 260, 20)
        if abs(tx) > 20 or abs(ty) > 20:  # don't place on player
            break
    target.goto(tx, ty)
```

Two issues:
1. `while True` never breaks - infinite loop
2. `update_weights` and `target.goto` are never called (indentation/placement issues)There are two bugs in that block:

1. **The `while True` never `break`s** — it spins forever generating `tx`/`ty` but never escaping, freezing the program.
2. **`target.goto(tx, ty)` is missing entirely** — even if it did exit, the target would never actually move.

`update_weights` and the `...` are also dangling outside the `if` block, which looks unintentional.

Here's the fixed section:

```python
if new_dist < 20:
    mazzed_solvd += 1
    steps_since_solve = 0
    update_weights(inputs, 10.0, chosen_index)  # reward the solve

    head.goto(0, 0)
    head.direction = "stop"

    # Pick a new target position that isn't on top of the player
    while True:
        tx = random.randrange(-260, 260, 20)
        ty = random.randrange(-260, 260, 20)
        if abs(tx) > 20 or abs(ty) > 20:   # far enough from centre
            break

    target.goto(tx, ty)
    last_solved_time = time.time()
```

**What changed:**
- Added `break` so the loop actually exits once valid coordinates are found
- Added `target.goto(tx, ty)` so the target relocates
- Moved `update_weights` *inside* the `if` block and removed the stray `...`
- Reset `head.direction = "stop"` so the player doesn't keep drifting after teleporting
- Moved `last_solved_time` reset to after the new target is placed (cleaner ordering)

---
claude-conversations-hub maze-solver-crashing-on-target-contact

## Tags
#claude-conversations-hub #its #maze #maze-solver-crashing-on-target-contact
