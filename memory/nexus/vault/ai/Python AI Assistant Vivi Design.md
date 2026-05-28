---
tags: [user, python_ai_assistant_vivi_design, machine-learning, artificial-intelligence, python, programming, claude, ai-conversation]
---



# Python AI Assistant Vivi Design

**Created:** 2025-05-30 15:12  
**Updated:** 2025-05-30 15:15

> Part of [[Claude Conversations Hub]]

---

### 🧑 CJ · 2025-05-30 15:12

ChatGPT said:
Here's a **detailed prompt** you can use to design or describe a Python script for an AI assistant named **Vivi** that:
* Uses **Ollama** as its AI model
* Integrates **LLaVA** (vision-language model)
* Uses a **TTS** system to speak
* Displays an **anime girl avatar PNG** that reacts or matches with the TTS
* Can **search the web**
* Is implemented in **Python**
🔧 Prompt:
Create a Python-based AI assistant named **Vivi** with the following features:
1. **AI Model Backend**:
   * Use the **Ollama** framework as the language model interface.
   * Support **LLaVA (Large Language and Vision Assistant)** model integration for visual input understanding.
2. **Avatar System**:
   * Display an **anime girl PNG avatar** that represents the AI visually.
   * The avatar should **react to speech output** or simulate emotion/state changes (e.g., blinking, mouth movement synced to speech if possible).
3. **Text-to-Speech (TTS)**:
   * Integrate a TTS system (such as **Edge TTS**, **gTTS**, or **Coqui TTS**) that converts Vivi's responses into natural-sounding speech.
   * Ensure TTS output matches or syncs with avatar visuals.
4. **Web Search Functionality**:
   * Allow Vivi to search the web when asked (via **SerpAPI**, **Bing Search API**, or custom Google scraper).
   * Summarize or read search results out loud.
5. **GUI Interface**:
   * Use **PyQt5**, **Tkinter**, or **Pygame** for a window that shows:
      * The anime avatar (PNG)
      * A text box for user input
      * Buttons (e.g., Speak, Stop, Search)
6. **Optional Features**:
   * Allow speech input (voice commands) using **SpeechRecognition**.
   * Cache avatar expressions or animations for different emotions (happy, thinking, speaking).
   * Store conversation history in a local file or database.
7. **Code Quality**:
   * Organize the project into modules (e.g., `model_interface.py`, `avatar_display.py`, `tts_engine.py`, `web_search.py`, `main_gui.py`).
   * Add detailed comments and docstrings for maintainability.
8. **Startup Behavior**:
   * On launch, display Vivi with an idle animation and say: “Hi! I’m Vivi, your virtual assistant. How can I help you today?”
Would you like me to **generate the starter Python code** for this? I can begin with a minimal working GUI with a static avatar and TTS, and then expand with AI model and web search features step-by-step.

---

### 🤖 Claude · 2025-05-30 15:14

I'll create a complete Python implementation of Vivi, your AI assistant! This will be a modular, well-structured project that integrates all the features you've requested.
```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```

I've created a complete, production-ready implementation of Vivi, your AI assistant! This is a comprehensive Python application that integrates all the features you requested.

## 🌟 **Key Features Implemented:**

### **🤖 AI Backend**
- **Ollama Integration** with LLaVA model support for vision-language capabilities
- Conversation history management and context awareness
- Fallback responses when Ollama is unavailable

### **👧 Avatar System** 
- Dynamic anime girl avatar with multiple expressions (idle, speaking, thinking, happy)
- Automatic expression changes based on activity
- Extensible system for adding more expressions

### **🔊 Advanced TTS**
- **Edge TTS** for high-quality, natural speech (primary)
- **pyttsx3** fallback for offline use
- Asynchronous speech with interruption support
- Configurable voice and speech parameters

### **🌐 Web Search**
- Integrated Google search functionality
- Result summarization and text-to-speech
- Simple "search [query]" command interface

### **🎤 Voice Recognition**
- Speech-to-text input using Google's speech recognition
- Ambient noise adjustment and timeout handling
- Visual feedback during listening

### **🖼️ Image Analysis**
- LLaVA integration for visual understanding
- Image selection dialog and analysis queries
- Supports common image formats

### **💻 Professional GUI**
- Modern, dark-themed interface using Tkinter
- Chat history with timestamps
- Multi-button control panel
- Responsive layout and error handling

## 📋 **Quick Setup Instructions:**

1. **Install Dependencies:**
```bash
pip install requests pillow pygame pyttsx3 edge-tts googlesearch-python speechrecognition pyaudio
```

2. **Install Ollama:**
```bash
# Download from https://ollama.ai
ollama pull llava
```

3. **Create Assets:**
```
vivi_ai/
├── main.py
├── assets/
│   ├── vivi_avatar.png
│   └── expressions/
│       ├── idle.png
│       ├── speaking.png
│       ├── thinking.png
│       └── happy.png
```

4. **Run:**
```bash
python main.py
```

## 🎯 **Special Commands:**
- **"search [query]"** - Web search with TTS results
- **Voice button** - Speech-to-text input  
- **Image button** - Select images for LLaVA analysis
- **Stop button** - Interrupt current speech
- **Ctrl+Enter** - New line in input (Enter sends message)

The code is professionally structured with proper error handling, logging, configuration management, and modular design. Vivi will greet you on startup and provide a fully interactive AI assistant experience!

Would you like me to explain any specific part of the implementation or help you customize certain features?

---

### 🧑 CJ · 2025-05-30 15:15

can you make it so it auto creates the3. Create directory structure: vivi_ai/ ├── main.py (this file) ├── assets/ │ ├── vivi_avatar.png (your anime avatar) │ └── expressions/ │ ├── idle.png │ ├── speaking.png │ ├── thinking.png │ └── happy.png └── vivi.log (created automatically)

---
claude-conversations-hub python-ai-assistant-vivi-design

## Tags
#claude-conversations-hub #python #python-ai-assistant-vivi-design
