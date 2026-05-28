---
tags: [user, automating_mouse_and_keyboard_actions, mouse-automation, keyboard-automation, pyautogui, vivi, ai-assistant, application-control, web-automation, office-automation, system-automation, safety-features, fail-safe, coordinate-validation, 2025, claude-conversation]
---



# Automating Mouse and Keyboard Actions

**Created:** 2025-05-29 14:50  
**Updated:** 2025-05-29 23:29

> Part of [[Claude Conversations Hub]]

---

### 🧑 CJ · 2025-05-29 14:50

can you add a way for my program to use my mouse  and key boards for example using my mouse to open docs on Google and my key board to type and other things...

---

### 🤖 Claude · 2025-05-29 14:51

I'll help you add mouse and keyboard automation capabilities to V.I.V.I. Looking at your code, I can see you already have `pyautogui` as a dependency, which is perfect for this functionality. Let me create an enhanced version that adds comprehensive mouse and keyboard control.
```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```

---

### 🧑 CJ · 2025-05-29 14:52

Continue

---

### 🤖 Claude · 2025-05-29 14:53

```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```

Perfect! I've created a comprehensive mouse and keyboard automation system for your V.I.V.I. assistant. Here's what I've added:

## 🚀 Key Features Added:

### **Mouse Control:**
- Click anywhere on screen (left, right, double-click)
- Move mouse cursor smoothly
- Drag operations
- Scroll up/down
- Get current mouse position

### **Keyboard Control:**
- Type any text
- Press individual keys (Enter, Space, Arrow keys, etc.)
- Execute hotkey combinations (Ctrl+C, Ctrl+V, etc.)
- Predefined shortcuts for common tasks

### **Application Control:**
- Open any application by name
- Open Google Docs, Gmail, YouTube
- Window management (minimize, maximize, close)
- Browser tab management
- Take screenshots

### **Advanced Automation:**
- **Web Automation**: Google search, open websites
- **Office Automation**: Create Word documents, Excel spreadsheets
- **System Automation**: Desktop organization, recycle bin management
- **Automation Sequences**: Chain multiple actions together

## 📝 How to Use:

Just talk to V.I.V.I. naturally:

```
"click at 500, 300"
"type Hello World"
"open google docs"
"press ctrl+c"
"scroll down"
"take a screenshot"
"google search for python tutorials"
"create word document titled My Report"
```

## 🔧 Integration:

To add this to your existing V.I.V.I. system:

1. **Replace your main assistant class** with `AdvancedAutomationAssistant`
2. **The system will automatically detect** automation requests in user input
3. **PyAutoGUI is already listed** in your dependencies, so it should work immediately

## 🛡️ Safety Features:

- **Fail-safe**: Move mouse to corner to stop execution
- **Coordinate validation**: Prevents clicks outside screen
- **Text sanitization**: Removes potentially dangerous characters
- **Error handling**: Graceful failure with helpful messages

## 💡 Example Voice Commands:

- *"V.I.V.I., click at the center of the screen"*
- *"Type 'Hello World' for me"*
- *"Open Google Docs and create a new document"*
- *"Take a screenshot and save it"*
- *"Press Ctrl+C to copy this text"*

The automation system integrates seamlessly with your existing vision capabilities, so V.I.V.I. can see what's on screen AND control it! This makes it incredibly powerful for automating any computer task.

Would you like me to show you how to integrate this with your existing code, or would you like me to add any specific automation features?

---

### 🧑 CJ · 2025-05-29 14:59

can you just replace it with the.0000

---

### 🧑 CJ · 2025-05-29 15:06

can you just replace **main assistant class** with `AdvancedAutomationAssistant for me`

---

### 🤖 Claude · 2025-05-29 15:08

I'll help you replace the main assistant class with `AdvancedAutomationAssistant` in your existing code. Let me create the updated version with the automation features integrated:
```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```

---

### 🧑 CJ · 2025-05-29 15:09

Continue

---

### 🤖 Claude · 2025-05-29 15:11

```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```

---

### 🧑 CJ · 2025-05-29 15:11

Continue

---

### 🤖 Claude · 2025-05-29 15:14

```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```

---

### 🧑 CJ · 2025-05-29 15:16

continue

---

### 🤖 Claude · 2025-05-29 15:18

```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```

---

### 🧑 CJ · 2025-05-29 15:18

Continue

---

### 🤖 Claude · 2025-05-29 15:19

```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```

Perfect! 🎉 I've successfully integrated the **`AdvancedAutomationAssistant`** class as the main assistant in your V.I.V.I. system. Here's what's been changed and added:

## 🔄 **Main Changes Made:**

### **1. Replaced Main Assistant Class**
- ✅ **Changed from `EnhancedAIAssistant` to `AdvancedAutomationAssistant`**
- ✅ **All automation features are now fully integrated**
- ✅ **Maintains all existing functionality (vision, avatar, voice, etc.)**

### **2. Enhanced Configuration**
- ✅ **Added automation settings to `ViviConfig`**
- ✅ **New automation toggle (`/automation`)**
- ✅ **Safety controls and fail-safe options**

### **3. New Automation Features Available**
- 🖱️ **Complete mouse control** (click, move, scroll, drag)
- ⌨️ **Full keyboard control** (type, press keys, hotkeys)
- 🚀 **Application launching** (Google Docs, any app)
- 🪟 **Window management** (minimize, maximize, close)
- 📸 **Screenshot capture**
- 🎯 **Advanced automation sequences**

### **4. Enhanced Help and Status**
- ✅ **Updated help command with automation instructions**
- ✅ **New `/status` shows automation status**
- ✅ **Enhanced welcome banner with automation info**

## 🎯 **How to Use the New Automation:**

Just talk to V.I.V.I. naturally with commands like:

```
"click at 500, 300"
"type Hello World"
"open google docs"
"press ctrl+c"
"scroll down"
"take a screenshot"
"move mouse to 400, 200"
"minimize window"
"open notepad"
```

## 🛡️ **Safety Features:**

- **Fail-safe**: Move mouse to corner to stop all automation
- **Coordinate validation**: Prevents out-of-bounds clicks
- **Error handling**: Graceful failure with helpful messages
- **Toggle control**: Can enable/disable automation with `/automation`

## 🎮 **Integration Status:**

✅ **Anime Avatar** - Shows "automating" state during automation tasks  
✅ **Vision System** - Can analyze screen before/after automation  
✅ **Voice Control** - Give automation commands by voice  
✅ **Animations** - New "automating" animation with robot emoji  
✅ **Package Management** - Auto-installs PyAutoGUI if needed  

## 🚀 **Ready to Run:**

Your V.I.V.I. system now has **complete mouse and keyboard automation** while maintaining all existing features. The automation system will:

1. **Auto-install PyAutoGUI** if not present
2. **Show automation status** in the startup banner
3. **Provide helpful error messages** if automation fails
4. **Integrate seamlessly** with voice commands and vision analysis

Just run your existing V.I.V.I. script and you'll have full automation capabilities! 🤖✨

---

### 🧑 CJ · 2025-05-29 23:29

can you give me a quick olama set up

---

### 🤖 Claude · 2025-05-29 23:29

I'll give you a quick and easy Ollama setup guide for V.I.V.I.!
```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```

There you go! 🚀 A complete Ollama setup guide that will get you up and running with V.I.V.I. in just a few minutes.

## 🎯 **TL;DR - Super Quick Setup:**

1. **Download & Install**: [ollama.com](https://ollama.com/download)
2. **Start Server**: `ollama serve`
3. **Install Models**: 
   ```bash
   ollama pull llama2
   ollama pull llava:7b
   ```
4. **Run V.I.V.I.**: Your assistant is ready!

## 💡 **Pro Tip:**
The vision model (`llava:7b`) is what makes V.I.V.I. able to see and analyze your screen. This is super powerful when combined with the automation features - V.I.V.I. can literally see what's on screen and then control your mouse/keyboard based on what it sees!

Once you have Ollama running, your V.I.V.I. will have:
- 🧠 **Smart AI responses**
- 👁️ **Screen vision analysis** 
- 🤖 **Full automation control**
- 🎭 **Cute anime avatar**

The setup usually takes about 5-10 minutes depending on your internet speed for downloading the models. Let me know if you run into any issues! 😊

---
automating-mouse-and-keyboard-actions claude-conversations-hub

## Tags
#automating #automating-mouse-and-keyboard-actions #claude-conversations-hub
