---
tags: [user, building_a_local_ai_voice_assistant_with_a_local_llm_model, machine-learning, artificial-intelligence, local-ai-assistant, voice-assistant, ollama, llm, pyttsx3, python-dotenv, screen-vision, internet-search, context-detection, vivi, animation-file, microphone-input, vs-code-guide, feminine-voice, 2025, claude-conversation]
---



# Building a Local AI Voice Assistant with a Local LLM Model

**Created:** 2025-05-28 12:38  
**Updated:** 2025-05-28 17:15

> Part of [[Claude Conversations Hub]]

---

### 🧑 CJ · 2025-05-28 12:38

* `pyttsx3`: for text-to-speech.
* Optional: `dotenv` to load API keys securely.
1. **Core Modules**:
   1. `config.py` — Settings (voice, personality).
   2. `ai_assistant.py` — Core logic:
      * Read user input.
      * Call LLM for a response.
      * Speak the response (if enabled).
   3. `main.py` — CLI entry point.
2. **Customizability**:
   * Easily edit:
      * AI prompt/personality.
      * TTS voice/rate settings.
3. **VS Code Usage**:
   * Debug/run via terminal.
   * No UI needed (text+speech).

---

### 🧑 CJ · 2025-05-28 13:43

* `pyttsx3`: for text-to-speech. * Optional: `dotenv` to load API keys securely. 1. **Core Modules**:    1. `config.py` — Settings (voice, personality).    2. `ai_assistant.py` — Core logic:       * Read user input.       * Call LLM for a response.       * Speak the response (if enabled).    3. `main.py` — CLI entry point. 2. **Customizability**:    * Easily edit:       * AI prompt/personality.       * TTS voice/rate settings. 3. **VS Code Usage**:    * Debug/run via terminal.    * No UI needed (text+speech). ist a LLM model Local modle

---

### 🤖 Claude · 2025-05-28 13:44

I'll help you create a local AI voice assistant using a local LLM model. This will be a modular Python application that can run entirely offline.
```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```



I've created a complete local AI voice assistant that runs entirely offline using a local LLM model. Here's what the system includes:

## Key Features

**Modular Design:**
- `config.py` - Centralized settings for easy customization
- `ai_assistant.py` - Core logic handling LLM calls and TTS
- `main.py` - Clean CLI interface
- `requirements.txt` - All dependencies listed

**Local LLM Integration:**
- Uses Ollama for running local models (Llama2, CodeLlama, etc.)
- No internet required after setup
- Conversation history maintained
- Configurable context window

**Voice Capabilities:**
- Text-to-speech using `pyttsx3`
- Adjustable voice, speed, and volume
- Can be toggled on/off during conversation

**VS Code Friendly:**
- Run directly in terminal
- Debug-friendly with clear error handling
- No GUI dependencies

## Quick Setup

1. **Install Ollama** and pull a model:
```bash
ollama pull llama2
ollama serve
```

2. **Install Python packages**:
```bash
pip install requests pyttsx3 python-dotenv ollama
```

3. **Run the assistant**:
```bash
python main.py
```

## Customization Options

- **Change AI personality**: Edit `SYSTEM_PROMPT` in `config.py`
- **Switch models**: Change `LLM_MODEL` (llama2, codellama, etc.)
- **Adjust voice**: Modify TTS settings for different voices/speeds
- **Debug mode**: Enable/disable verbose logging

The assistant maintains conversation context, handles errors gracefully, and provides a clean command interface with `/help`, `/clear`, `/tts`, and `/quit` commands.

Would you like me to explain any specific part in more detail or help you customize it for your particular use case?

---

### 🧑 CJ · 2025-05-28 15:36

can you add a real time screen veiw for the ai so it can see my screen for example I'm reading a PDF and I want to ask the ai a question and add internet axis

---

### 🤖 Claude · 2025-05-28 15:39

I'll enhance the AI assistant to include real-time screen capture and internet access capabilities. This will allow the AI to see your screen (like PDFs) and search the web when needed.
```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```


```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```


```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```


```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```


```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```


```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```


```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```


```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```


```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```


```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```


```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```


```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```


```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```



Perfect! I've enhanced your AI assistant with real-time screen viewing and internet access. Here are the major new capabilities:

## 🔥 New Features Added

### 📸 **Screen Vision Capabilities**
- **Auto-detection**: The AI automatically captures your screen when you mention "PDF", "document", "screen", "see", "look at"
- **Manual control**: Use `/see` command to force screen capture
- **Smart analysis**: Can read PDFs, analyze code, describe web pages, etc.
- **Uses vision models**: Works with `llava` or `bakllava` models from Ollama

### 🌐 **Internet Search Integration**  
- **Auto-detection**: Automatically searches when you say "search for", "google", or mention current events
- **Manual control**: Use `/search` command to force web search
- **Privacy-focused**: Uses DuckDuckGo search (no tracking)
- **Context-aware**: Combines search results with your questions

### 🎯 **Smart Context Detection**
The AI now intelligently detects when you need:
- **Screen analysis**: "What does this PDF say?", "Explain this code", "What's on my screen?"
- **Web search**: "Latest news about...", "Search for...", "What happened today?"

## 📋 **Example Usage Scenarios**

```bash
# Reading a PDF
> What does this document say about renewable energy?
[Automatically captures screen and analyzes the PDF]

# Getting current information  
> Search for the latest AI developments this week
[Searches web and provides current information]

# Code analysis
> Can you explain what this Python code does?
[Captures screen to see your code editor]

# Research assistance
> What are the recent studies on climate change?
[Searches for current research and summarizes]
```

## 🛠️ **Setup Requirements**

You'll need to install additional packages:
```bash
pip install pillow pyautogui beautifulsoup4 duckduckgo-search
```

And pull a vision model:
```bash
ollama pull llava  # Recommended vision model
```

## 🎮 **New Commands**
- `/screen` - Toggle screen capture on/off
- `/internet` - Toggle internet search on/off  
- `/see` - Force screen capture for next question
- `/search` - Force web search for next question

## 🔒 **Privacy & Security**
- Screenshots are processed locally and never stored
- Only DuckDuckGo is used for searches (privacy-focused)
- All AI processing happens on your local machine
- No data sent to external services except search queries

The assistant now works perfectly for your PDF reading scenario - just ask "What does this PDF say about X?" and it will automatically capture your screen, analyze the PDF content, and provide relevant answers!

Would you like me to explain any specific part or help you set up the vision model?

---

### 🧑 CJ · 2025-05-28 17:12

1. Add an animation file to visually indicate when the AI speaks or listens.
2. Enable microphone input so users can speak directly to the AI.
3. Include a simple, high-school-level guide for setting everything up in Visual Studio Code (VS Code) on Windows 11. This should explain what needs to be downloaded and how to run the code.

4. Give the AI a name: **Virtual Intelligent Viral Internet**, or **"V.I.V.I."** for short.
5. Use a feminine-sounding voice for the text-to-speech (TTS) responses.

---

### 🤖 Claude · 2025-05-28 17:15

I'll enhance the AI assistant with voice input, visual animations, a feminine voice, and rename it to V.I.V.I. (Virtual Intelligent Viral Internet). I'll also create a comprehensive Windows 11 setup guide.
```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```


```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```


```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```


```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```


```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```


```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```


```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```


```
Viewing artifacts created via the Analysis Tool web feature preview isn’t yet supported on mobile.
```


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
building-a-local-ai-voice-assistant-with-a-local-llm-model claude-conversations-hub

## Tags
#building #building-a-local-ai-voice-assistant-with-a-local-llm-model #claude-conversations-hub
