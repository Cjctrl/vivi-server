---
tags: [user, updating_random_objects_in_loop, claude, ai-conversation]
---



# Updating random objects in loop

**Created:** 2026-04-23 22:25  
**Updated:** 2026-04-23 22:30

> Part of [[Claude Conversations Hub]]

---

### 🧑 CJ · 2026-04-23 22:25

what should i do im trying to get my random object to update evrytime import time
import numpy as np
import random
import turtle
delay = 0.1
wn = turtle.Screen()
wn.title("Single Output Neural Network")
wn.bgcolor("white")
wn.setup(width=600, height=600)
wn.tracer(0)
#chacter
head=turtle.Turtle()
head.speed(0)
head.shape("square")
head.color("black")
head.penup()
head.goto(0, 0)
head.direction = "stop"
#this will run a for loop to generate a random num 0-4 for each obj
 
obj1 = random.randint(0, 4)
obj2 = random.randint(0, 4)
obj3 = random.randint(0, 4)
def check_equality(obj1, obj2, obj3):
    if(obj1 ==obj2 == obj3):
        bool1 = True
        bool2 = True
        bool3 = True
    elif (obj1 == obj2 != obj3):
        bool1 = True
        bool2 = True
        bool3 = False
    elif (obj1 == obj3 != obj2):
        
        bool1 = True
        bool2 = False
        bool3 = True
    elif (obj2 == obj3 != obj1):
   
        bool1 = False
        bool2 = True
        bool3 = True
    else:
        bool1 = bool (obj1)
        bool2 = bool (obj2) 
        bool3 = bool (obj3)
    return bool1, bool2, bool3
bool1, bool2, bool3 = check_equality(obj1, obj2, obj3)
#sprint([bool1, bool2, bool3])
def choice(bool1, bool2, bool3):
    #this will be kinda like a basic neural network with 3 inputs and 1 output
    for i in range(1):
        if bool1 and bool2 and bool3:
            return 1
        elif bool1 and bool2 and not bool3:
            return 2
        elif bool1 and not bool2 and bool3:
            return 3
        elif not bool1 and bool2 and bool3:
            return 4
        else:
            return 5
result = choice(bool1, bool2, bool3)
print(result)
#for loop for the character to move based on the result
for i in range(1):
    
    if result == 1:
        head.setheading(90)
        head.forward(100)
    elif result == 2:
        head.setheading(180)
        head.forward(100)
    elif result == 3:
        head.setheading(270)
        head.forward(100)
    elif result == 4:
        head.setheading(0)
        head.forward(100)
    else:
        head.setheading(360)
        head.forward(100)
time.sleep(delay)
wn.update()
wn.mainloop()

---

### 🤖 Claude · 2026-04-23 22:25

The user wants their random objects (obj1, obj2, obj3) to update every time in a loop. Currently the values are generated once outside any loop. They need a game loop that regenerates the random values each iteration.The issue is that `obj1`, `obj2`, `obj3` are only generated **once** before the loop, and your movement code runs just once too. You need a **game loop** that regenerates the random values and moves the character on each iteration.

Here's the fixed version:

```python
import time
import numpy as np
import random
import turtle

delay = 0.1

wn = turtle.Screen()
wn.title("Single Output Neural Network")
wn.bgcolor("white")
wn.setup(width=600, height=600)
wn.tracer(0)

# Character
head = turtle.Turtle()
head.speed(0)
head.shape("square")
head.color("black")
head.penup()
head.goto(0, 0)
head.direction = "stop"


def check_equality(obj1, obj2, obj3):
    if obj1 == obj2 == obj3:
        return True, True, True
    elif obj1 == obj2 != obj3:
        return True, True, False
    elif obj1 == obj3 != obj2:
        return True, False, True
    elif obj2 == obj3 != obj1:
        return False, True, True
    else:
        return bool(obj1), bool(obj2), bool(obj3)


def choice(bool1, bool2, bool3):
    if bool1 and bool2 and bool3:
        return 1
    elif bool1 and bool2 and not bool3:
        return 2
    elif bool1 and not bool2 and bool3:
        return 3
    elif not bool1 and bool2 and bool3:
        return 4
    else:
        return 5


# ✅ Game loop — regenerates objects every iteration
while True:
    # Generate new random objects each frame
    obj1 = random.randint(0, 4)
    obj2 = random.randint(0, 4)
    obj3 = random.randint(0, 4)

    bool1, bool2, bool3 = check_equality(obj1, obj2, obj3)
    result = choice(bool1, bool2, bool3)

    print(f"obj1={obj1}, obj2={obj2}, obj3={obj3} → result={result}")

    # Move character based on result
    if result == 1:
        head.setheading(90)
    elif result == 2:
        head.setheading(180)
    elif result == 3:
        head.setheading(270)
    elif result == 4:
        head.setheading(0)
    else:
        head.setheading(360)

    head.forward(20)  # Smaller step so it doesn't fly off screen instantly

    wn.update()
    time.sleep(delay)
```

**Key changes made:**

1. **Moved `obj1/obj2/obj3` inside a `while True:` loop** — this is the main fix. Now they regenerate every frame instead of being set once.

2. **Replaced the `for i in range(1):` blocks with the `while True:` loop** — `for i in range(1)` only runs once, which is the same as no loop at all.

3. **Reduced `head.forward()` from `100` to `20`** — with 10 updates per second your turtle would zoom off screen very quickly at 100 pixels per step.

4. **Removed `wn.mainloop()`** — it conflicts with a manual `while True:` loop. The window stays open as long as the loop runs.

---

### 🧑 CJ · 2026-04-23 22:29

```python

import time

import numpy as np
import random
import turtle

delay = 0.1
wn = turtle.Screen()
wn.title("Single Output Neural Network")
wn.bgcolor("white")
wn.setup(width=600, height=600)
wn.tracer(0)

#chacter
head=turtle.Turtle()
head.speed(0)
head.shape("square")
head.color("black")
head.penup()
head.goto(0, 0)
head.direction = "stop"

#this will run a for loop to generate a random num 0-4 for each obj



def check_equality(obj1, obj2, obj3):

    if(obj1 ==obj2 == obj3):
        bool1 = True
        bool2 = True
        bool3 = True
    elif (obj1 == obj2 != obj3):
        bool1 = True
        bool2 = True
        bool3 = False
    elif (obj1 == obj3 != obj2):
        
        bool1 = True
        bool2 = False
        bool3 = True
    elif (obj2 == obj3 != obj1):
   
        bool1 = False
        bool2 = True
        bool3 = True
    else:
        bool1 = bool (obj1)
        bool2 = bool (obj2) 
        bool3 = bool (obj3)

    return bool1(obj1), bool2(obj2), bool3(obj3)
#bool1, bool2, bool3 = check_equality(obj1, obj2, obj3)
#sprint([bool1, bool2, bool3])

def choice(bool1, bool2, bool3):
    #this will be kinda like a basic neural network with 3 inputs and 1 output
    for i in range(1):
        if bool1 and bool2 and bool3:
            return 1
        elif bool1 and bool2 and not bool3:
            return 2
        elif bool1 and not bool2 and bool3:
            return 3
        elif not bool1 and bool2 and bool3:
            return 4
        else:
            return 5

while True:
    obj1 = random.randint(0, 4)
    obj2 = random.randint(0, 4)
    obj3 = random.randint(0, 4)

    bool1, bool2, bool3 = check_equality(obj1, obj2, obj3)
    result = choice(bool1, bool2, bool3)

    print(f"obj1={obj1}, obj2={obj2}, obj3={obj3} → result={result}")

  

#for loop for the character to move based on the result

   # Move character based on result
    if result == 1:
        head.setheading(90)
    elif result == 2:
        head.setheading(180)
    elif result == 3:
        head.setheading(270)
    elif result == 4:
        head.setheading(0)
    else:
        head.setheading(360)

    head.forward(20)  # Smaller step so it doesn't fly off screen instantly

    time.sleep(delay)
    wn.update()





```

---

### 🤖 Claude · 2026-04-23 22:30

The user has a bug in their `check_equality` function. The return statement is wrong:

```python
return bool1(obj1), bool2(obj2), bool3(obj3)
```

`bool1`, `bool2`, `bool3` are boolean variables, not functions, so you can't call them like `bool1(obj1)`. It should just be:

```python
return bool1, bool2, bool3
```

Also there's an indentation issue in the while loop - the comment and some code seem misaligned.You have a bug in your `check_equality` return statement. You're trying to **call** the booleans like functions, which will crash:

```python
# ❌ Wrong — bool1 is a True/False value, not a function
return bool1(obj1), bool2(obj2), bool3(obj3)

# ✅ Correct — just return the variables directly
return bool1, bool2, bool3
```

Also you have an **indentation error** in your `while` loop — the movement code got accidentally un-indented. Here's the fully corrected file:

```python
import time
import numpy as np
import random
import turtle

delay = 0.1
wn = turtle.Screen()
wn.title("Single Output Neural Network")
wn.bgcolor("white")
wn.setup(width=600, height=600)
wn.tracer(0)

# Character
head = turtle.Turtle()
head.speed(0)
head.shape("square")
head.color("black")
head.penup()
head.goto(0, 0)
head.direction = "stop"


def check_equality(obj1, obj2, obj3):
    if obj1 == obj2 == obj3:
        bool1 = True
        bool2 = True
        bool3 = True
    elif obj1 == obj2 != obj3:
        bool1 = True
        bool2 = True
        bool3 = False
    elif obj1 == obj3 != obj2:
        bool1 = True
        bool2 = False
        bool3 = True
    elif obj2 == obj3 != obj1:
        bool1 = False
        bool2 = True
        bool3 = True
    else:
        bool1 = bool(obj1)
        bool2 = bool(obj2)
        bool3 = bool(obj3)

    return bool1, bool2, bool3  # ✅ Fixed — no (obj) calls


def choice(bool1, bool2, bool3):
    if bool1 and bool2 and bool3:
        return 1
    elif bool1 and bool2 and not bool3:
        return 2
    elif bool1 and not bool2 and bool3:
        return 3
    elif not bool1 and bool2 and bool3:
        return 4
    else:
        return 5


while True:
    obj1 = random.randint(0, 4)
    obj2 = random.randint(0, 4)
    obj3 = random.randint(0, 4)

    bool1, bool2, bool3 = check_equality(obj1, obj2, obj3)
    result = choice(bool1, bool2, bool3)

    print(f"obj1={obj1}, obj2={obj2}, obj3={obj3} → result={result}")

    # ✅ Fixed indentation — all inside the while loop
    if result == 1:
        head.setheading(90)
    elif result == 2:
        head.setheading(180)
    elif result == 3:
        head.setheading(270)
    elif result == 4:
        head.setheading(0)
    else:
        head.setheading(360)

    head.forward(20)

    wn.update()
    time.sleep(delay)
```

**Two bugs fixed:**

| Bug | Problem | Fix |
|-----|---------|-----|
| `return bool1(obj1)` | Tried to call a boolean like a function → `TypeError` | `return bool1, bool2, bool3` |
| Movement block indentation | Code was outside the `while` loop, running only once | Indented everything back inside the loop |

---
claude-conversations-hub updating-random-objects-in-loop

## Tags
#bool1 #chacter #claude-conversations-hub #for #sprint #this #updating #updating-random-objects-in-loop
