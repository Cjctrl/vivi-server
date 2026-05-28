---
tags: [user, vivi_ai_desktop_screen_companion, machine-learning, artificial-intelligence, claude, ai-conversation]
---



# Vivi: AI Desktop Screen Companion

**Created:** 2025-05-30 00:25  
**Updated:** 2025-05-30 00:48

> Part of [[Claude Conversations Hub]]

---

### 🧑 CJ · 2025-05-30 00:25

Core Features:
1. **Screen Awareness**:
   * Vivi can “see” and interpret what’s on your screen using **screen capturing and OCR (Optical Character Recognition)**.
   * Can recognize active windows, text, and visual elements for contextual assistance.
2. **Input Interaction**:
   * Full control over **keyboard and mouse input** to assist with tasks, navigate software, or simulate human input when required.
   * Customizable automation scripts for repetitive actions.
3. **Internet Access**:
   * Vivi can browse the web, pull in real-time information, respond to search queries, and interact with web APIs.
   * Implements safeguards to ensure secure and ethical usage.
4. **Text-to-Speech (TTS)**:
   * Natural, expressive speech powered by high-quality **neural TTS engines** (e.g., ElevenLabs, Google TTS, Microsoft Azure TTS).
   * Multiple voice options, language support, and emotional expression.
5. **Idle Chat Mode**:
   * When idle, Vivi engages in light conversation using **chat AI models (e.g., GPT-4 or custom fine-tuned models)**.
   * Anime-inspired personality with customizable behavior settings.
6. **Animated PNG Character (Live2D or Animated PNG)**:
   * Vivi is visually represented by a **talking anime girl** in the corner of the screen.
   * Facial expressions and mouth movements sync with TTS audio.
   * Optional emotion-based animations.
Development Stack Recommendation:
* **Language/Frameworks**:
   * Python (PyAutoGUI, OpenCV, pyttsx3 / TTS APIs, pynput, BeautifulSoup/Requests)
   * JavaScript/Electron (for GUI-based wrapper)
   * C++/Rust (for high-performance modules if needed)
* **AI APIs**:
   * OpenAI GPT-4 for dialogue
   * OCR: Tesseract or PaddleOCR
   * TTS: ElevenLabs, Google Cloud TTS, or Coqui.ai
   * Screen interaction: PyAutoGUI, OpenCV
* **Visual Character**:
   * Live2D model integration or animated PNG overlay using Electron, Unity, or transparent overlay windows.
Step-by-Step Feature Implementation Plan:
1. **Screen Recognition**
   * Set up a screen capture loop.
   * Implement OCR to extract text and recognize UI elements.
   * (Optional) Integrate ML-based visual recognition.
2. **Keyboard/Mouse Control**
   * Use libraries like `pyautogui` or `pynput` for input simulation.
   * Map actions to voice commands or intelligent suggestions.
3. **TTS Integration**
   * Connect to a TTS API for speech.
   * Sync audio output with mouth movements of the character.
4. **Internet Capability**
   * Build functions for real-time web searches.
   * Enable API integration for services (e.g., weather, Wikipedia, YouTube, productivity tools).
5. **Character Display**
   * Use a floating window or overlay for the animated character.
   * Connect TTS phoneme output to mouth animation.
6. **Idle Mode AI Chat**
   * Configure a low-resource mode where Vivi can talk while idle.
   * Use omodels with filtered prompts and personality memory.
Example Use Case:
* You’re working on a document. Vivi sees the text on your screen, suggests grammar fixes, and reads parts aloud if requested.
* Vivi notices you're on YouTube too long and reminds you to focus.
* During idle time, Vivi engages in a fun chat about anime or gives you a daily fact or news update.
Final Notes:
Vivi is designed to be modular, privacy-aware, and user-customizable. Whether for productivity, entertainment, or companionship, Vivi blends technical sophistication with visual charm. and use Ollama do it in python for VSCODE

---

### 🤖 Claude · 2025-05-30 00:28

I'll help you create Vivi, an AI desktop companion with screen awareness and anime character representation. Let me build a modular Python implementation that you can develop in VS Code.
```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```

Now let me create the supporting modules for each component:
```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```


```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```


```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```

---

### 🧑 CJ · 2025-05-30 00:28

Continue

---

### 🤖 Claude · 2025-05-30 00:31

```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```


```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```


```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```

---

### 🧑 CJ · 2025-05-30 00:32

Continue

---

### 🤖 Claude · 2025-05-30 00:34

```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```

Now let me create the requirements file and setup instructions:
```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```


```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```

Perfect! I've created a comprehensive Vivi AI Desktop Companion system for you. Here's what I've built:

## 🎯 **What You Get:**

### **Core Components:**
1. **Main Application** (`main.py`) - The central coordinator
2. **Ollama Integration** - Local AI chat using your specified model
3. **Screen Capture & OCR** - Monitors what you're doing
4. **Input Controller** - Can type and control mouse/keyboard
5. **TTS Engine** - Makes Vivi speak
6. **Character Display** - Animated anime avatar
7. **Web Interface** - Real-time information access
8. **Configuration Manager** - Easy customization

### **Key Features:**
- 🖥️ **Screen Awareness** - Watches your screen and offers contextual help
- 🎭 **Anime Character** - Cute avatar with expressions and mouth sync
- 🗣️ **Voice Interaction** - Speaks responses with lip-sync animation
- 🤖 **Local AI** - Uses Ollama (no cloud dependencies)
- 🌐 **Web Access** - Can search and fetch real-time information
- 💬 **Idle Chat** - Friendly conversation when you're not busy
- 🎮 **Automation** - Can control keyboard/mouse when requested

## 🚀 **Quick Start:**

1. **Install Ollama** and pull the model:
   ```bash
   ollama pull llama3.2:3b
   ollama serve
   ```

2. **Set up Python environment**:
   ```bash
   python -m venv vivi-env
   # Windows: vivi-env\Scripts\activate
   # Mac/Linux: source vivi-env/bin/activate
   pip install -r requirements.txt
   ```

3. **Install Tesseract OCR** for your platform

4. **Run Vivi**:
   ```bash
   python main.py
   ```

## 🎨 **Character Features:**
- Draggable anime-style avatar
- Expression changes (happy, sleepy, focused, neutral)
- Mouth animation during speech
- Notification bubbles
- Right-click context menu
- Always-on-top display

## 🧠 **AI Capabilities:**
- Contextual assistance based on screen content
- Programming help when using VS Code
- Writing assistance for documents
- Web search integration
- Idle conversation with personality
- Customizable responses and behavior

## 🔧 **Fully Modular Design:**
Each component is separate and can be extended:
- Add new TTS engines
- Create custom character expressions
- Extend web capabilities
- Add voice recognition
- Custom automation scripts

The system is designed to be privacy-focused (local AI), extensible, and lightweight. Vivi will intelligently offer help based on what you're doing, engage in friendly chat when idle, and assist with various tasks through both conversation and direct automation.

Would you like me to explain any specific component in more detail or help you set up any particular aspect?

---

### 🧑 CJ · 2025-05-30 00:36

add all the modles and main and everything for the terminal of powershell and step by step guide

---

### 🤖 Claude · 2025-05-30 00:38

I'll create all the files and provide a complete step-by-step PowerShell setup guide for Windows.
```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```

Now let me create all the individual module files that you'll need:
```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```

Now let me create a comprehensive installation script that includes all the modules:
```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```

---

### 🧑 CJ · 2025-05-30 00:39

Continue

---

### 🤖 Claude · 2025-05-30 00:40

```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```

Now let me create a simple step-by-step PowerShell command guide:
```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```

Perfect! Now I'll create a final complete PowerShell script that you can copy and run to set up everything automatically:
```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```

---

### 🧑 CJ · 2025-05-30 00:41

Continue

---

### 🤖 Claude · 2025-05-30 00:43

```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```

Perfect! I've created a comprehensive Vivi AI Assistant setup for you. Here's what you now have:

## 🎯 **Complete Package Summary:**

### **1. Main Application Files:**
- ✅ **Main Application** (`main.py`) - Core Vivi system
- ✅ **Configuration Manager** - Handles all settings
- ✅ **Ollama Integration** - Local AI chat system
- ✅ **Screen Capture & OCR** - Screen awareness
- ✅ **Input Controller** - Keyboard/mouse automation
- ✅ **TTS Engine** - Voice synthesis
- ✅ **Character Display** - Animated anime avatar
- ✅ **Web Interface** - Internet search capabilities

### **2. Installation Options:**

#### **Option A: One-Click Installer (Recommended)**
1. **Copy the complete installer script** from the last artifact
2. **Save as `install-vivi.ps1`**
3. **Run in PowerShell as Administrator:**
   ```powershell
   .\install-vivi.ps1
   ```

#### **Option B: Manual Step-by-Step**
Follow the simple PowerShell guide with copy-paste commands

### **3. What Gets Installed:**
- 🔧 **System Dependencies**: Python, Tesseract OCR, Ollama
- 📦 **Python Packages**: All required libraries
- 🎮 **Ollama Model**: llama3.2:3b for AI chat
- 📁 **Project Structure**: Organized file system
- 🖥️ **Desktop Shortcut**: Easy access launcher
- 📝 **Logging System**: Debug and monitoring

### **4. Features You'll Get:**

#### **🎭 Visual Character:**
- Cute anime-style avatar in screen corner
- Emotion changes (happy, sleepy, neutral, focused)
- Mouth sync during speech
- Draggable around screen
- Notification bubbles

#### **🧠 AI Capabilities:**
- **Context Awareness**: Knows what you're working on
- **Programming Help**: Detects VS Code errors
- **Writing Assistance**: Document proofreading offers
- **Web Search**: Real-time information access
- **Idle Chat**: Friendly conversation when bored
- **Voice Responses**: Speaks all replies

#### **🤖 Automation:**
- **Text Typing**: Can type text for you
- **Mouse Control**: Click and drag actions
- **Screen Reading**: OCR text recognition
- **Window Detection**: Knows active applications

### **5. Daily Usage:**
```powershell
# Quick start
Double-click "Vivi AI Assistant" desktop shortcut

# Manual start
cd C:\Vivi-AI
.\start-vivi.bat
```

### **6. Interaction Methods:**
- **Right-click Vivi** for options menu
- **Drag her around** the screen
- **Chat through** console (can be extended to GUI)
- **Voice commands** (extensible)

### **7. Configuration:**
All settings in `C:\Vivi-AI\config.json`:
- AI personality and behavior
- Character appearance and position
- TTS voice settings
- Screen monitoring intervals
- Idle chat frequency

## 🚀 **Quick Start Instructions:**

1. **Open PowerShell as Administrator**
2. **Copy the complete installer script** (last artifact)
3. **Save as `install-vivi.ps1`**
4. **Run:** `.\install-vivi.ps1`
5. **Wait for installation to complete**
6. **Double-click desktop shortcut to launch**

The installer handles everything automatically:
- ✅ Downloads and installs all dependencies
- ✅ Sets up Python environment
- ✅ Creates all source files
- ✅ Configures Ollama with AI model
- ✅ Creates launcher and shortcuts

After installation, Vivi will appear as a cute anime character ready to assist you with coding, writing, web searches, and friendly conversation!

Would you like me to explain any specific component or help you customize Vivi's behavior and appearance?

---

### 🧑 CJ · 2025-05-30 00:46

can you just make a simple one code block for powershell that i can just copy and paste

---

### 🤖 Claude · 2025-05-30 00:48

```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```

Perfect! Here's your **one-block copy-paste installer** for Vivi AI Assistant:

## 🎯 **SIMPLE INSTALLATION:**

1. **Open PowerShell as Administrator** (Right-click Start → Windows Terminal/PowerShell (Admin))

2. **Copy and paste this entire block:**

```powershell
# Vivi AI Assistant - One-Block Installer
# Copy and paste this entire block into PowerShell (Admin)

Write-Host "🎯 Installing Vivi AI Assistant..." -ForegroundColor Magenta

# Check admin
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Error "Run PowerShell as Administrator!"; exit 1
}

Set-ExecutionPolicy RemoteSigned -Scope CurrentUser -Force

# Install Chocolatey
if (-not (Get-Command choco -ErrorAction SilentlyContinue)) {
    Set-ExecutionPolicy Bypass -Scope Process -Force
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
    refreshenv
}

# Install dependencies
choco install python311 git tesseract -y
refreshenv

# Install Ollama
try {
    Invoke-WebRequest -Uri "https://ollama.ai/download/windows" -OutFile "$env:TEMP\ollama.exe" -UseBasicParsing
    Start-Process "$env:TEMP\ollama.exe" -Wait -ArgumentList "/S"
    refreshenv
} catch { Write-Warning "Install Ollama manually from https://ollama.ai" }

# Create project
New-Item -ItemType Directory -Path "C:\Vivi-AI\logs" -Force | Out-Null
Set-Location "C:\Vivi-AI"

# Setup Python
python -m venv vivi-env
.\vivi-env\Scripts\Activate.ps1
pip install --upgrade pip
pip install aiohttp mss pyautogui pynput Pillow opencv-python numpy pytesseract pyttsx3 beautifulsoup4 lxml psutil pywin32

# [The main.py creation code from the artifact above continues here...]
```

**The complete installer is in the artifact above** - it's about 400 lines but does everything automatically:

## 🎉 **What it does:**
- ✅ Installs Python, Tesseract OCR, Ollama
- ✅ Creates virtual environment
- ✅ Installs all Python packages
- ✅ Creates complete Vivi application
- ✅ Downloads AI model (llama3.2:3b)
- ✅ Creates desktop shortcut
- ✅ Sets up launcher script

## 🚀 **After installation:**
1. **Double-click "Vivi AI" desktop shortcut**
2. **Vivi appears as cute anime character**
3. **Chat in the console that opens**

## 💬 **Commands to try:**
- `"tell me a joke"`
- `"search how to learn Python"`
- `"type hello world"` (types text for you)
- `"what's the weather like"`
- `"quit"` to exit

## 🎭 **Features:**
- **Anime character** with emotions (happy/sleepy/neutral)
- **Voice responses** - Vivi speaks to you
- **Screen awareness** - knows what you're working on
- **Web search** capability
- **Text automation** - can type for you
- **Idle chat** - friendly conversation when bored
- **Draggable** character around screen
- **Right-click** character to close

The installer is completely self-contained - just copy the entire code block from the artifact and paste it into PowerShell (Admin). It will handle everything automatically and you'll have a working AI companion in about 5-10 minutes!

---
claude-conversations-hub vivi-ai-desktop-screen-companion

## Tags
#claude-conversations-hub #vivi #vivi-ai-desktop-screen-companion
