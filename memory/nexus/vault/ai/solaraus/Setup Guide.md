---
tags: [user, setup_guide, setup, guide]
---



# Setup Guide

This document provides detailed instructions for installing, configuring, and deploying the Solarus AI assistant.

## Overview
The Setup Guide walks you through the process of getting Solarus running on your system, from installing dependencies to configuring individual components and testing the complete system.

## System Requirements
- **Operating System**: Windows 10/11, macOS 12+, or Linux (Ubuntu 20.04+ recommended)
- **Processor**: Modern CPU with at least 4 cores (Intel i5/Ryzen 5 or better)
- **Memory**: 8GB RAM minimum, 16GB+ recommended
- **Storage**: 5GB available space for installation and models
- **Audio**: Microphone for voice input, speakers or headphones for audio output
- **Camera**: Webcam for face recognition functionality (optional but recommended for authentication)

## Prerequisites Installation
### Python Environment
1. Install Python 3.9 or later from https://python.org
2. Verify installation: `python --version` or `python3 --version`
3. Install pip if not included: https://pip.pypa.io/en/stable/installation/

### Required Python Packages
Core dependencies for all Solarus components:
```
pip install opencv-python mediapipe tensorflow torch torchvision
pip install speechrecognition pyaudio pyttsx3
pip install pyautogui psutil
pip install requests beautifulsoup4 lxml
pip install selenium webdriver-manager
pip install PyYAML jinja2
```

### Optional Dependencies
For enhanced functionality:
```
pip install whisper  # For local speech-to-text
pip install TTS      # For local text-to-speech
pip install flask    # For API extensions
pip install watchdog # For file system monitoring
```

## Installation Steps
1. **Clone or download the Solarus repository** to your preferred location
2. **Navigate to the solarus directory**:
   ```
   cd path/to/solarus
   ```
3. **Install Python dependencies**:
   ```
   pip install -r requirements.txt
   ```
4. **Set up face recognition models**:
   - Copy required model files from the face directory (if available)
   - Or run the training scripts to create your own models
5. **Configure audio devices**:
   - Test microphone: `python -m speech_recognition` (Windows) or use audio settings
   - Test speakers: Ensure TTS output is audible
6. **Configure webcam** (for face recognition):
   - Test with: `python -c "import cv2; cap=cv2.VideoCapture(0); print(cap.isOpened())"`

## Component-Specific Configuration
### Voice Command System
- Configure wake word in `config/voice_config.yaml`
- Set speech-to-text preferences (local vs cloud)
- Adjust microphone sensitivity and silence detection

### Text Command System
- Define custom command aliases in `config/text_commands.yaml`
- Configure input sources (keyboard, clipboard, etc.)

### Application Control Module
- Review and customize application aliases in `config/applications.yaml`
- Set up window control preferences

### Web Interaction Module
- Configure default search engine in `config/web_config.yaml`
- Set up API keys for services (stored securely)
- Configure browser preferences

### Face Recognition System
- Run enrollment process to add authorized users
- Adjust confidence thresholds for authentication
- Test lighting conditions and angles

## Initial Setup and Testing
1. **Test face recognition** (if using):
   ```
   python login.py
   ```
   Should detect face and attempt authentication

2. **Test voice input**:
   - Say wake word followed by a simple command like "what time is it"

3. **Test text input**:
   - Type a command like "open notepad" or "search for python tutorials"

4. **Test application control**:
   - Try "open calculator" or "switch to chrome"

5. **Test web interaction**:
   - Try "open google.com" or "search for latest news"

## Configuration Files
Solarus uses YAML configuration files located in the `config/` directory:
- `voice_config.yaml` - Voice input settings
- `text_config.yaml` - Text input settings
- `applications.yaml` - Application aliases and launch parameters
- `web_config.yaml` - Web interaction preferences
- `auth_config.yaml` - Authentication and face recognition settings
- `automation_config.yaml` - Task automation rules
- `context_config.yaml` - Context management parameters
- `output_config.yaml` - Audio/visual feedback preferences

## First Run Wizard
On first execution, Solarus will:
1. Detect available hardware (mic, camera, etc.)
2. Prompt for basic configuration (wake word, preferred language, etc.)
3. Guide you through testing each major component
4. Help you set up your user profile for face recognition
5. Create default configuration files based on your selections

## Troubleshooting Installation
- **Missing dependencies**: Check that all pip install commands completed successfully
- **Audio issues**: Verify microphone and speaker permissions in OS settings
- **Camera problems**: Ensure webcam drivers are installed and not blocked by other applications
- **Performance issues**: Close unnecessary applications to free resources
- **Permission errors**: Run installation with appropriate privileges (not as Administrator unless necessary)

## Updates and Maintenance
- Regularly update Python packages: `pip install --upgrade -r requirements.txt`
- Periodically retrain face recognition model with new images for better accuracy
- Backup configuration files before major updates
- Check compatibility when updating individual components

## Related Notes
- [[Solarus|Main Documentation]]
- [[Voice Command System]]
- [[Text Command System]]
- [[Application Control Module]]
- [[Web Interaction Module]]
- [[Task Automation System]]
- [[Context Management]]
- [[API Reference]]
- [[Troubleshooting Guide]]
api-reference application-control-module context-management setup-guide solarus task-automation-system text-command-system troubleshooting-guide voice-command-system web-interaction-module

## Tags
#api-reference #application-control-module #context-management #setup #setup-guide #solarus #task-automation-system #text-command-system #troubleshooting-guide #voice-command-system #web-interaction-module

## Hashtags
#solarus #voicecommandsystem #textcommandsystem #applicationcontrolmodule #webinteractionmodule #taskautomationsystem #contextmanagement #apireference #troubleshootingguide
