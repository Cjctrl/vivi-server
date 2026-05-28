---
tags: [user, feedforward_neural_network_reward_system_design, machine-learning, artificial-intelligence, claude, ai-conversation]
---



# Feedforward neural network reward system design

**Created:** 2026-04-23 00:48  
**Updated:** 2026-04-23 13:19

> Part of [[Claude Conversations Hub]]

---

### 🧑 CJ · 2026-04-23 00:48

ok so for a project im devolping i want to build a feedforward neual network that will be trained on the inputs head_to_fruit that will give +=1  score that will give the nerual network a proposernal output i.e score increase 1 += 0.5 as score always increse for time and finaly a penelty for not moving -=0.7

---

### 🤖 Claude · 2026-04-23 00:51

The user wants to build a feedforward neural network for their snake game. Let me understand what they want:

1. **Inputs**: head_to_fruit (distance from head to food), and likely other spatial inputs like wall distances
2. **Rewards/Outputs**:
   - +1 for eating fruit
   - +0.5 proportional score increase (time-based score increases)
   - -0.7 penalty for not moving

This sounds like they want a reinforcement learning setup with a feedforward neural network. Let me think about the architecture:

- **Inputs**: The normalized values they already computed:
  - head_to_right_wall/300
  - head_to_left_wall/300
  - head_to_top_wall/300
  - head_to_bottom_wall/300
  - Head_to_food/300
  - head position (x, y)
  - current direction (one-hot encoded?)
  
- **Output**: 4 actions (up, down, left, right) or a reward signal

Wait, re-reading: they want a neural network that takes `head_to_fruit` as input and outputs a proportional reward. This seems like they want a reward shaping network, not a policy network. Or maybe they want a simple feedforward NN that learns to play the game.

Actually, I think they want:
- A feedforward NN that takes game state inputs
- Gets rewarded with:
  - +1 when eating fruit
  - +0.5 for time-based score increases  
  - -0.7 penalty for not moving (staying still)
- The NN outputs actions (directions)

This is essentially a simple reinforcement learning setup. Let me design:

**Architecture**:
- Input layer: game state (distances to walls, distance to food, direction, etc.)
- Hidden layers: 1-2 hidden layers
- Output layer: 4 neurons (one per direction - up/down/left/right)

**Training approach**: Since they're new to this, I'll suggest a simple approach - maybe collect training data and use supervised learning, or implement a basic Q-learning style approach.

But given their code style (beginner-intermediate), I think they want something relatively simple. Let me design a feedforward NN using numpy (no PyTorch/TensorFlow complexity).

Let me think about what they're actually asking. They want:
1. Input: head_to_fruit (and probably other inputs)
2. Reward signal:
   - +1 for eating fruit
   - +0.5 proportional (time score)
   - -0.7 for not moving

This is a reinforcement learning reward function. The neural network would be a policy network that takes state inputs and outputs an action.

Let me design a complete system:

**Inputs (normalized 0-1)**:
- head_to_right_wall/300
- head_to_left_wall/300  
- head_to_top_wall/300
- head_to_bottom_wall/300
- head_to_food_x (signed, normalized)
- head_to_food_y (signed, normalized)
- current_direction (one-hot: 4 values)

**Architecture**: 10 inputs → 16 hidden → 8 hidden → 4 outputs (softmax)

**Reward**:
- +1.0 on food eaten
- +0.5 * (time_score_increment) on each step
- -0.7 if direction == "stop" (not moving)

I'll write this as a separate Python module that integrates with their existing game. I'll use numpy for the neural network and implement basic backpropagation or even a genetic/evolutionary approach since RL with backprop can be complex.

Actually, for a feedforward NN trained on these inputs, the simplest approach is probably:
1. Collect game state + reward data
2. Train the NN to predict actions that maximize reward

But for true RL, they'd need Q-learning or policy gradients.

Let me keep it simple and implement:
1. A feedforward NN class with numpy
2. Integration points for the snake game
3. The reward function they specified

I'll write the neural network code cleanly. Let me think about the architecture more carefully.

For a snake game NN, common inputs are:
- Direction to food (angle or x/y components)
- Distances to walls in 4 directions
- Distances to body segments

Output: 4 direction probabilities

Let me write clean, well-commented code. I'll use a simple feedforward NN with:
- Input: ~10 features
- Hidden: 16 neurons
- Output: 4 actions

And implement a simple training loop using the reward signal they described. Since pure RL with backprop is complex, I'll implement a simplified version that collects (state, action, reward) tuples and does supervised updates.

Actually, let me think about this more carefully. They want to train the NN on the game. The most sensible approach for a beginner would be:

**Option A**: Genetic Algorithm / Neuroevolution (simple, no gradient needed)
**Option B**: Q-learning (reward-based, standard RL)
**Option C**: Simple supervised learning on collected data

Given they mentioned specific reward values (+1, +0.5, -0.7), this sounds like they want reinforcement learning with a reward function.

I'll implement a simple Q-learning style approach with a feedforward NN, keeping it in numpy so they don't need external ML libraries.

Let me write the neural_network.py file and also show how to integrate it into their snake game.

```python
import numpy as np
import json

class FeedforwardNN:
    def __init__(self, input_size=10, hidden_sizes=[16, 8], output_size=4):
        self.layers = []
        sizes = [input_size] + hidden_sizes + [output_size]
        for i in range(len(sizes)-1):
            W = np.random.randn(sizes[i], sizes[i+1]) * 0.1
            b = np.zeros(sizes[i+1])
            self.layers.append({'W': W, 'b': b})
    
    def relu(self, x):
        return np.maximum(0, x)
    
    def softmax(self, x):
        e = np.exp(x - np.max(x))
        return e / e.sum()
    
    def forward(self, x):
        self.activations = [x]
        for i, layer in enumerate(self.layers):
            x = x @ layer['W'] + layer['b']
            if i < len(self.layers) - 1:
                x = self.relu(x)
            else:
                x = self.softmax(x)
            self.activations.append(x)
        return x
    
    def predict_action(self, state):
        probs = self.forward(state)
        return np.argmax(probs)  # or sample from distribution
    
    def save(self, filename="nn_weights.json"):
        data = [{'W': l['W'].tolist(), 'b': l['b'].tolist()} for l in self.layers]
        with open(filename, 'w') as f:
            json.dump(data, f)
    
    def load(self, filename="nn_weights.json"):
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            self.layers = [{'W': np.array(l['W']), 'b': np.array(l['b'])} for l in data]
        except FileNotFoundError:
            pass
```

For the reward and training, I'll implement a simple experience replay buffer and policy gradient or Q-learning update.

Let me write a complete, well-structured solution. I'll create a neural_network.py module.

The inputs I'll use:
1. head_to_right_wall / 300
2. head_to_left_wall / 300
3. head_to_top_wall / 300
4. head_to_bottom_wall / 300
5. food_dx / 600 (signed x distance to food)
6. food_dy / 600 (signed y distance to food)
7. head_to_food / 600 (euclidean)
8-11. current_direction one-hot (up, down, left, right)

That's 11 inputs total.

Output: 4 values for (up, down, left, right) directions

Reward function:
- +1.0 when food eaten
- +0.5 * time_step_bonus (each frame the snake is alive and moving)
- -0.7 when direction == "stop" (not moving)

For training, I'll use a simple policy gradient (REINFORCE) or Q-learning. Let me go with Q-learning as it's more standard for this type of game.

Actually, let me think about what the user literally asked: "a feedforward neural network that will be trained on the inputs head_to_fruit that will give +=1 score that will give the neural network a proportional output"

I think they want:
- Input: game state
- Output: action to take (or action probabilities)
- Training: using the reward signal they described

Let me write a clean implementation. I'll use a simple approach where I implement:
1. The NN class
2. A reward calculator
3. Training loop integration

For simplicity, I'll implement a basic REINFORCE (policy gradient) algorithm since it's the most intuitive for "take actions, get rewards, train the network."

Let me write this up properly.

```python
# neural_network.py
import numpy as np
import json

class SnakeNN:
    """
    Feedforward Neural Network for Snake Game
    Input: 11 normalized game state features
    Output: 4 action probabilities (up, down, left, right)
    """
    
    def __init__(self, input_size=11, hidden_sizes=[24, 12], output_size=4, lr=0.001):
        self.lr = lr
        self.layers = []
        sizes = [input_size] + hidden_sizes + [output_size]
        
        for i in range(len(sizes) - 1):
            self.layers.append({
                'W': np.random.randn(sizes[i], sizes[i+1]) * np.sqrt(2.0/sizes[i]),  # He init
                'b': np.zeros(sizes[i+1])
            })
        
        # Experience buffer for training
        self.states = []
        self.actions = []
        self.rewards = []
        
        # Action mapping
        self.action_map = {0: "up", 1: "down", 2: "left", 3: "right"}
        self.direction_map = {"up": 0, "down": 1, "left": 2, "right": 3, "stop": -1}
    
    # --- Activation Functions ---
    def relu(self, x):
        return np.maximum(0, x)
    
    def relu_deriv(self, x):
        return (x > 0).astype(float)
    
    def softmax(self, x):
        e = np.exp(x - np.max(x))  # numerical stability
        return e / e.sum()
    
    # --- Forward Pass ---
    def forward(self, x):
        self.cache = {'a': [x]}  # store activations for backprop
        current = x
        for i, layer in enumerate(self.layers):
            z = current @ layer['W'] + layer['b']
            if i < len(self.layers) - 1:
                current = self.relu(z)
            else:
                current = self.softmax(z)
            self.cache['a'].append(current)
        return current
    
    # --- Action Selection ---
    def choose_action(self, state, epsilon=0.1):
        """Epsilon-greedy action selection"""
        if np.random.random() < epsilon:
            return np.random.randint(4)  # explore
        probs = self.forward(state)
        return np.argmax(probs)  # exploit
    
    # --- Reward Calculation ---
    @staticmethod
    def calculate_reward(ate_food, is_moving, time_score_increment=0.1):
        """
        Reward function:
        +1.0  for eating food
        +0.5  proportional time-based reward (scaled)
        -0.7  penalty for not moving
        """
        reward = 0.0
        if ate_food:
            reward += 1.0
        if is_moving:
            reward += time_score_increment * 0.5  # proportional to time score
        else:
            reward -= 0.7
        return reward
    
    # --- Store Experience ---
    def remember(self, state, action, reward):
        self.states.append(state.copy())
        self.actions.append(action)
        self.rewards.append(reward)
    
    # --- Compute Discounted Returns ---
    def discounted_returns(self, gamma=0.95):
        G = np.zeros(len(self.rewards))
        running = 0
        for t in reversed(range(len(self.rewards))):
            running = self.rewards[t] + gamma * running
            G[t] = running
        # Normalize
        if G.std() > 1e-8:
            G = (G - G.mean()) / G.std()
        return G
    
    # --- REINFORCE Policy Gradient Update ---
    def train_episode(self, gamma=0.95):
        if len(self.states) == 0:
            return 0.0
        
        returns = self.discounted_returns(gamma)
        total_loss = 0.0
        
        for t, (state, action, G) in enumerate(zip(self.states, self.actions, returns)):
            probs = self.forward(state)
            
            # Log probability of taken action
            log_prob = np.log(probs[action] + 1e-8)
            loss = -log_prob * G
            total_loss += loss
            
            # Backpropagation
            self._backprop(state, action, G)
        
        # Clear episode memory
        self.states.clear()
        self.actions.clear()
        self.rewards.clear()
        
        return total_loss / len(self.states) if len(self.states) > 0 else total_loss
    
    def _backprop(self, state, action, G):
        """Compute gradients and update weights via policy gradient"""
        probs = self.forward(state)
        
        # Output gradient: d(loss)/d(logits) = probs - one_hot(action), scaled by return G
        one_hot = np.zeros(4)
        one_hot[action] = 1.0
        delta = (probs - one_hot) * G  # policy gradient loss gradient
        
        # Backprop through layers
        for i in reversed(range(len(self.layers))):
            a_prev = self.cache['a'][i]
            
            dW = np.outer(a_prev, delta)
            db = delta.copy()
            
            if i > 0:  # not input layer
                delta = delta @ self.layers[i]['W'].T
                delta *= self.relu_deriv(self.cache['a'][i])
            
            # Gradient update
            self.layers[i]['W'] -= self.lr * dW
            self.layers[i]['b'] -= self.lr * db
    
    # --- State Builder ---
    @staticmethod
    def get_state(head, food, segments, direction):
        """Build normalized input vector from game state"""
        hx, hy = head.xcor(), head.ycor()
        fx, fy = food.xcor(), food.ycor()
        
        # Wall distances (normalized 0-1)
        r_wall = (290 - hx) / 300
        l_wall = (hx + 290) / 300
        t_wall = (290 - hy) / 300
        b_wall = (hy + 290) / 300
        
        # Food direction (normalized -1 to 1)
        food_dx = (fx - hx) / 600
        food_dy = (fy - hy) / 600
        
        # Euclidean distance to food (normalized)
        food_dist = ((hx-fx)**2 + (hy-fy)**2)**0.5 / 600
        
        # Current direction one-hot [up, down, left, right]
        dir_map = {"up": [1,0,0,0], "down": [0,1,0,0],
                   "left": [0,0,1,0], "right": [0,0,0,1], "stop": [0,0,0,0]}
        dir_encoded = dir_map.get(direction, [0,0,0,0])
        
        return np.array([r_wall, l_wall, t_wall, b_wall,
                         food_dx, food_dy, food_dist] + dir_encoded, dtype=float)
    
    # --- Save/Load Weights ---
    def save(self, path="nn_weights.json"):
        data = [{'W': l['W'].tolist(), 'b': l['b'].tolist()} for l in self.layers]
        with open(path, 'w') as f:
            json.dump({'layers': data, 'lr': self.lr}, f)
        print(f"[NN] Weights saved to {path}")
    
    def load(self, path="nn_weights.json"):
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            self.layers = [{'W': np.array(l['W']), 'b': np.array(l['b'])} 
                          for l in data['layers']]
            self.lr = data.get('lr', self.lr)
            print(f"[NN] Weights loaded from {path}")
        except FileNotFoundError:
            print("[NN] No saved weights found, starting fresh.")
```

Now let me also show the integration into the snake game. The key changes would be:

1. Import the NN at the top
2. Build state each frame
3. Calculate reward each frame
4. Let NN choose action instead of keyboard
5. Train at end of each episode

Let me write a clean, complete implementation. I'll create a separate file for the NN and show the modified game loop.

Actually, I realize I should present this cleanly. Let me write the neural_network.py as a file and then show the key modifications needed for the snake game.

Let me finalize the code and make sure it's correct.Looking at your code, I can see you've already got the normalized inputs partially set up. Let me build you a clean `neural_network.py` module that integrates with your snake game, using **REINFORCE** (policy gradient) — the most natural fit for your reward structure.
```
This block is not supported on your current device yet.
```

Now let me create the modified snake game that integrates with the neural network.Now let me create the modified snake game that wires everything together:
```
This block is not supported on your current device yet.
```


```
This block is not supported on your current device yet.
```

Here's a breakdown of the full system:

**`neural_network.py` — the NN module**

The architecture is `11 → 24 → 12 → 4`. The 11 inputs are your 4 wall distances, food `dx`/`dy` (signed, so it knows *which side* food is on), euclidean food distance, and a 4-element one-hot for current direction. The 4 outputs are action probabilities over `[up, down, left, right]`.

**Reward function** (exactly as you described):
- `+1.0` when food is eaten
- `+0.5 × time_increment` each frame the snake is moving (proportional to your existing 0.1/frame score)
- `−0.7` when direction is `"stop"`

**Training — REINFORCE (policy gradient):**
Each frame, the experience `(state, action, reward)` is stored. When the episode ends (wall/self hit), `train_episode()` computes discounted returns `G_t` going backwards through the episode, normalizes them to reduce variance, and does a single backprop update per timestep. Weights save every 10 episodes to `nn_weights.json`.

**To run:** put both files in the same folder and run `snake_nn.py`. The NN controls the snake automatically — you can still override with the keyboard if you want. To make it fully autonomous just remove the keyboard block (it's clearly marked with a comment).

---

### 🧑 CJ · 2026-04-23 13:19

Traceback (most recent call last):
  File "c:\pyhton projects 2026\ai snakeV2\snakeGame.py", line 149, in <module>
    state = SnakeNN.get_state(head, food, segments)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "c:\pyhton projects 2026\ai snakeV2\nerualnetwork.py", line 247, in get_state
    dir_enc = SnakeNN.DIRECTION_ONE_HOT.get(direction, [0, 0, 0, 0])
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: unhashable type: 'list'

---

### 🤖 Claude · 2026-04-23 13:19

The error is because they're passing `segments` (a list) as the third argument instead of `head.direction` (a string). Quick fix.The bug is in your `snake_nn.py` call — you're passing `segments` (a list) as the third argument instead of `head.direction` (a string). Line 149 in your game file:

**Change this:**
```python
state = SnakeNN.get_state(head, food, segments)
```

**To this:**
```python
state = SnakeNN.get_state(head, food, head.direction)
```

The third parameter `get_state` expects is the current direction string (`"up"`, `"down"`, etc.) so it can build the one-hot encoding. Passing the segments list caused it to try to use a list as a dictionary key, which Python won't allow.

---
claude-conversations-hub feedforward-neural-network-reward-system-design

## Tags
#claude-conversations-hub #feedforward #feedforward-neural-network-reward-system-design
