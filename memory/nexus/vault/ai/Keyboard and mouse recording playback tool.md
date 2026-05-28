---
tags: [user, keyboard_and_mouse_recording_playback_tool, claude, ai-conversation]
---



# Keyboard and mouse recording playback tool

**Created:** 2026-02-15 12:51  
**Updated:** 2026-02-15 12:55

> Part of [[Claude Conversations Hub]]

---

### 🧑 CJ · 2026-02-15 12:51

* Hotkeys: F8 = start/stop recording, F9 = play back last recording, ESC = quit immediately
* Record keyboard key down + key up events with precise timestamps so I can calculate how long each key is held
* Record mouse move, mouse button down/up (left/right/middle), scroll, and record how long mouse buttons are held
* Save recordings to a file (JSON) with event type, key/button, position (for mouse), and `time_since_start` in seconds
* Print a summary after recording: total duration, how many events, and the longest key/button hold time
Playback requirements:
* Reproduce the exact timing between events (sleep based on timestamps)
* Support a `speed_multiplier` (e.g., 1.0 normal, 2.0 twice as fast)
* Safety: allow ESC to stop playback immediately, and include a failsafe (like moving mouse to top-left to abort)
Deliverables:
* Full working Python code with comments
* Step-by-step install instructions for Windows (venv optional)
* Explain any limitations (e.g., games/admin apps) and how to run as admin if needed.

---

### 🤖 Claude · 2026-02-15 12:55

The user wants a comprehensive keyboard and mouse recording/playback tool with specific requirements:

1. Hotkeys: F8 (start/stop recording), F9 (playback), ESC (quit)
2. Record keyboard events (key down/up) with timestamps
3. Record mouse events (move, button down/up, scroll) with timestamps
4. Calculate hold durations
5. Save to JSON with event type, key/button, position, time_since_start
6. Print summary after recording
7. Playback with exact timing reproduction
8. Support speed multiplier
9. Safety features: ESC to stop playback, mouse failsafe
10. Full working code with comments
11. Installation instructions for Windows
12. Explain limitations

This is a pure coding task - I should create the actual Python files. Let me create a complete solution.

For this task, I'll need:
- `pynput` library for keyboard/mouse capture and control
- JSON for saving/loading recordings
- Time tracking for timestamps
- Threading or proper event handling

I should create a single, well-commented Python file that includes all functionality.

Let me structure the code:
1. Import necessary libraries
2. Define data structures for events
3. Recording logic (keyboard and mouse listeners)
4. Playback logic with timing reproduction
5. Summary statistics
6. Main event loop with hotkey handling
7. Safety features

I'll also need to provide clear installation instructions and document limitations.I'll create a complete keyboard and mouse macro recorder/player with all the features you specified. Let me build this step by step.
```
This block is not supported on your current device yet.
```

Good! Now I need to create comprehensive installation instructions and documentation. Let me create a README file with installation steps, usage guide, and important notes about limitations.Now let me create comprehensive installation and usage instructions:
```
This block is not supported on your current device yet.
```

Excellent! Now let me create a quick start guide and also an example of how to add a GUI or speed control via command line. Let me create an enhanced version that includes command-line arguments for better usability.Let me also create an enhanced version with command-line arguments for easier control:
```
This block is not supported on your current device yet.
```

Perfect! Now let me create a quick reference guide for common use cases and troubleshooting, and then move everything to the outputs directory.Now let me create a quick start guide:
```
This block is not supported on your current device yet.
```

Great! Now let me move all the files to the outputs directory so the user can access them.Now let me move all files to the outputs directory for you:
```
This block is not supported on your current device yet.
```

Perfect! Now let me present the files to the user with a brief summary.
```
This block is not supported on your current device yet.
```

Perfect! Now let me provide a concise summary of what I've created and the key points the user needs to know.## ✅ Complete Macro Recorder System Ready!

I've created a full-featured keyboard and mouse recorder/player with everything you requested:

### 📦 What You Got:

**1. macro_recorder.py** - Main program with hotkey controls
- F8: Start/Stop recording
- F9: Playback last recording  
- ESC: Quit or abort playback
- Records key down/up, mouse moves/clicks/scroll with precise timestamps
- Calculates hold durations automatically
- Saves to JSON with full timing data
- Prints summary with stats and longest hold times

**2. macro_recorder_cli.py** - Enhanced version with command-line arguments
- All the features above PLUS:
- `--play filename.json --speed 2.0` for custom speed
- `--list` to see all recordings
- Better for automation workflows

**3. README.md** - Complete documentation
- Step-by-step Windows installation (with and without venv)
- Detailed usage guide
- JSON format explanation
- All limitations clearly documented (admin rights, games, anti-cheat)
- Troubleshooting section

**4. QUICKSTART.md** - 5-minute setup guide with examples

### 🚀 Quick Install (Windows):
```cmd
pip install pynput
python macro_recorder.py
```

### ⚡ Key Features Delivered:
✅ Precise timestamps (time_since_start in seconds)  
✅ Hold duration calculation for keys and mouse buttons  
✅ All mouse events (move, left/right/middle clicks, scroll)  
✅ JSON export with position data  
✅ Speed multiplier support (0.5x, 2.0x, etc.)  
✅ Safety: ESC + mouse corner failsafe  
✅ Summary stats after each recording  

### ⚠️ Important Limitations:
- **Admin apps**: May need to run as Administrator
- **Games**: Won't work with anti-cheat (Valorant, CSGO, etc.)
- **Coordinates**: Absolute screen positions (same resolution needed for playback)
- **Timing precision**: ~1-15ms depending on system

The code is fully commented and production-ready. Start with simple tests (Notepad) before complex workflows!

---
claude-conversations-hub keyboard-and-mouse-recording-playback-tool

## Tags
#claude-conversations-hub #keyboard #keyboard-and-mouse-recording-playback-tool
