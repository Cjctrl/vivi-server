---
tags: [user, building_a_powerful_local_ai_assistant, machine-learning, artificial-intelligence, claude, ai-conversation]
---



# Building a Powerful Local AI Assistant

**Created:** 2025-05-28 19:32  
**Updated:** 2025-05-28 20:19

> Part of [[Claude Conversations Hub]]

---

### 🧑 CJ · 2025-05-28 19:32

do it

---

### 🤖 Claude · 2025-05-28 19:35

I'll help you create a comprehensive V.I.V.I. (Virtual Intelligent Viral Internet) AI assistant with vision and internet capabilities. This is a powerful local AI assistant that can see your screen, search the web, and interact via voice.
```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```

---

### 🧑 CJ · 2025-05-28 19:36

Continue

---

### 🤖 Claude · 2025-05-28 19:37

```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```



Perfect! I've created the complete V.I.V.I. (Virtual Intelligent Viral Internet) AI assistant for you. This is a powerful local AI assistant with the following features:

## 🚀 Key Features:

### 1. **Vision Capabilities** 📸
- Auto-captures screen when you mention "PDF", "document", "screen", "look", etc.
- Manual screen capture with `/see` command
- Works with vision models like `llava`

### 2. **Internet Search** 🌐
- Auto-searches when you say "search for", "google", or ask about current events
- Manual search with `/search` command
- Uses DuckDuckGo for privacy-focused searches

### 3. **Voice Interaction** 🎤
- Wake words: "Hey V.I.V.I.", "OK V.I.V.I."
- Voice input mode with `/listen`
- Text-to-speech with feminine voice preference

### 4. **Visual Animations** ✨
- Shows V.I.V.I.'s status (idle, listening, thinking, speaking)
- Wake-up animation on startup
- Colorful terminal interface

### 5. **Smart Context Awareness** 🧠
- Automatically detects when you need screen analysis
- Automatically searches the web for current information
- Maintains conversation history

## 📦 Installation:

1. **Save the code** as `vivi_assistant.py`

2. **Install dependencies**:
```bash
pip install requests pyttsx3 pyautogui pillow duckduckgo-search speechrecognition pyaudio pygame colorama
```

3. **Install Ollama**:
```bash
# Visit https://ollama.ai or use:
curl -fsSL https://ollama.ai/install.sh | sh  # Linux
# or download from website for Windows/Mac
```

4. **Pull AI models**:
```bash
ollama pull llama2     # Basic text model
ollama pull llava      # Vision model (recommended)
```

## 🎯 Usage:

1. **Start Ollama**:
```bash
ollama serve
```

2. **Run V.I.V.I.**:
```bash
python vivi_assistant.py
```

3. **Example commands**:
```
> What's in this PDF?
[Auto-captures screen and analyzes]

> Search for the latest AI news
[Auto-searches web and provides current info]

> /listen
[Activates voice mode - say "Hey V.I.V.I."]

> /help
[Shows all available commands]
```

## 🛠️ Customization:

Edit the `Config` class in the code to customize:
- Change AI models
- Adjust voice settings
- Modify wake words
- Change animation speed
- Set search result limits

## 💡 Tips:

- For best results, use `llava` for vision capabilities
- The assistant automatically detects when to use screen capture or web search
- Voice commands work best with a good microphone
- All processing happens locally for privacy

V.I.V.I. is now ready to be your intelligent assistant with vision and internet access! Let me know if you need any modifications or have questions about using it.

---

### 🧑 CJ · 2025-05-28 20:17

import os import sys import json import base64 import time import threading import random from io import BytesIO from typing import List, Dict, Optional, Tuple from datetime import datetime  # Core libraries import requests  import pyttsx3 import pyautogui import speech_recognition as sr from PIL import Image from duckduckgo_search import DDGS from colorama import init, Fore, Style, Back import pygame  add a pip import

---

### 🤖 Claude · 2025-05-28 20:17

I'll create a requirements.txt file for easy pip installation of all the dependencies:
```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```



Now you can install all dependencies with a single command:

```bash
pip install -r requirements.txt
```

## 📝 Installation Notes:

### **pyaudio Installation Issues:**
If you encounter issues installing pyaudio:

**Windows:**
```bash
# Option 1: Use pipwin
pip install pipwin
pipwin install pyaudio

# Option 2: Download wheel file
# Visit: https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
# Download the appropriate .whl file for your Python version
pip install PyAudio‑0.2.11‑cp39‑cp39‑win_amd64.whl
```

**macOS:**
```bash
brew install portaudio
pip install pyaudio
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install portaudio19-dev python3-pyaudio
pip install pyaudio
```

### **Quick Install Script:**
You can also create a setup script:

```bash
#!/bin/bash
# setup_vivi.sh

echo "Setting up V.I.V.I. Assistant..."

# Install Python dependencies
pip install -r requirements.txt

# Install Ollama (Linux/macOS)
if [[ "$OSTYPE" == "linux-gnu"* ]] || [[ "$OSTYPE" == "darwin"* ]]; then
    curl -fsSL https://ollama.ai/install.sh | sh
fi

# Pull AI models
echo "Pulling AI models..."
ollama pull llama2
ollama pull llava

echo "V.I.V.I. setup complete! Run 'ollama serve' then 'python vivi_assistant.py'"
```

The requirements.txt file includes all necessary dependencies with minimum version requirements to ensure compatibility. The optional dependencies can enhance functionality but aren't strictly required for basic operation.

---

### 🧑 CJ · 2025-05-28 20:17

for vsCode

---

### 🤖 Claude · 2025-05-28 20:19

I'll create a VS Code workspace configuration for the V.I.V.I. project with all the necessary settings, extensions, and launch configurations:
```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```



Now, let me create additional VS Code configuration files for a complete development setup:
```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```



## 🎯 VS Code Setup Complete!

I've created a comprehensive VS Code configuration for your V.I.V.I. project. Here's what you get:

### 📁 File Structure:
```
vivi-assistant/
├── .vscode/
│   ├── settings.json      # Editor & Python settings
│   ├── launch.json        # Debug configurations
│   ├── tasks.json         # Automated tasks
│   └── extensions.json    # Recommended extensions
├── .env                   # Environment variables
├── .gitignore            # Git ignore patterns
├── pyproject.toml        # Python tool configs
├── README.md             # Project documentation
├── vivi_assistant.py     # Main application
└── requirements.txt      # Python dependencies
```

### 🚀 Quick Start:

1. **Run the setup script**:
   ```bash
   chmod +x setup_vscode_project.sh
   ./setup_vscode_project.sh
   ```

2. **Copy your files**:
   ```bash
   cd vivi-assistant
   # Copy the vivi_assistant.py and requirements.txt here
   ```

3. **Open in VS Code**:
   ```bash
   code .
   ```

### ⚡ VS Code Features:

#### **F5 - Debug Configurations**:
- **V.I.V.I. Assistant**: Normal run with debugger
- **V.I.V.I. Debug Mode**: Verbose output for troubleshooting
- **Python: Current File**: Debug any Python file

#### **Ctrl+Shift+B - Build Tasks**:
- **Install Dependencies**: Auto-install all pip packages
- **Create Virtual Environment**: Setup isolated Python env
- **Start Ollama Server**: Launch AI backend
- **Pull Ollama Models**: Download llama2 & llava
- **Setup Complete Environment**: One-click full setup

#### **Auto Features**:
- ✨ Auto-format on save (Black)
- 📦 Auto-organize imports (isort)
- 🔍 Real-time linting (flake8, pylint)
- 🎨 Syntax highlighting for requirements.txt
- 🐍 Virtual environment auto-activation

### 🛠️ Recommended Extensions:
The project will prompt you to install:
- Python & Pylance (IntelliSense)
- Black Formatter
- GitLens (Git integration)
- IntelliCode (AI completions)
- And more...

### 💡 Pro Tips:

1. **Quick Run**: Press `F5` to instantly start V.I.V.I.
2. **Task Runner**: `Ctrl+Shift+P` → "Run Task" for all automation
3. **Terminal**: `` Ctrl+` `` opens integrated terminal
4. **Problems**: `Ctrl+Shift+M` shows all linting issues

### 🔧 Customization:
Edit `.env` file to configure:
```env
OLLAMA_HOST=http://localhost:11434
VIVI_DEBUG=true  # Enable debug mode
VIVI_MODEL=llama2:13b  # Use larger model
VIVI_VISION_MODEL=bakllava  # Alternative vision model
```

This setup provides a professional development environment with all the tools you need to develop, debug, and enhance V.I.V.I.!

---
building-a-powerful-local-ai-assistant claude-conversations-hub

## Tags
#building #building-a-powerful-local-ai-assistant #claude-conversations-hub


[["$OSTYPE" == "linux-gnu"*]]


[["$OSTYPE" == "darwin"*]]
