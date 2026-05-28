---
tags: [user, solarus]
---



# Solarus Project

This note documents the Solarus project, a local AI assistant that integrates face recognition for secure authentication and provides voice/text-controlled application and web interaction.

## Location
The code is located in the file system at:
`C:\pyhton projects 2026\solarus\`

## Description
This project contains a face recognition system implemented in Python using OpenCV, Mediapipe, and TensorFlow. It includes modules for:
- Face tracking with landmarks (`facetracking.py`)
- Feature extraction and identity capture (`face_idenity_cap.py`)
- Pre-trained model files (`ID.keras`, `ID.npy`, `face_landmarker.task`)
- Login script (`login.py`) for quick face-based authentication

## Usage
To run the face login system:
1. Navigate to the directory: `cd C:\pyhton projects 2026\solarus`
2. Run the login script: `python login.py`
   - The script will attempt to detect a face, extract features, and compare against the trained model.
   - If the detected face matches the user "cj" with sufficient confidence, login succeeds.
   - Press 'q' to quit early.

To use the full face recognition system (capture, train, recognize):
1. Ensure you have the original face module code in `C:\pyhton projects 2026\face\`.
2. You can run the existing scripts there:
   - `python face_idenity_cap.py` to collect face data
   - `python face_ID_trainer.py` to train the model
   - `python main.py` to run real-time recognition

## Components
- **facetracking.py**: Tracks facial landmarks using MediaPipe FaceLandmarker.
- **face_idenity_cap.py**: Extracts facial geometry features (35 dimensions) from landmarks and provides utilities to save/load data.
- **ID.keras**: Trained Keras model for identity classification.
- **ID.npy**: NumPy array containing class labels (e.g., ["cj", "not_cj"]).
- **face_landmarker.task**: MediaPipe face landmark model file.
- **login.py**: Standalone script for quick face login (uses the above components).

## Notes
- The login script expects the user to be labeled as "cj" in the model. To change the user, retrain the model with new data using the scripts in the face directory.
- The model was trained using the face identity capture system from the face directory.
- For real-time recognition with additional features (like drawing landmarks), refer to the original `main.py` in the face directory.
- The login script does not display video by default to keep it simple; it only shows a window with the detected face and prediction.

## Related Notes
- [[Solaraus Project Hub|README]]
- [[Face Recognition System]] (original notes on face recognition system in the face directory)
- [[Voice Command System]]
- [[Text Command System]]
- [[Application Control Module]]
- [[Web Interaction Module]]
- [[Task Automation System]]
- [[Context Management]]
- [[Dynamic Model Switching]]
- [[Screen Interaction Module]]
- [[Setup Guide]]

## Steps to Set Up
1. Ensure you have Python, OpenCV, Mediapipe, TensorFlow installed.
2. Copy the following from `C:\pyhton projects 2026\face\` to `C:\pyhton projects 2026\solarus\`:
   - `facetracking.py`
   - `face_idenity_cap.py`
   - `ID.keras`
   - `ID.npy`
   - `face_landmarker.task`
3. Place `login.py` in the solarus directory.
4. Run `python login.py` to test face login.

## Tasks
- [ ] Test the login system with different lighting conditions
- [ ] Improve accuracy with more sophisticated models (e.g., deep learning)
- [ ] Add liveness detection to prevent spoofing
- [ ] Integrate with actual login system (e.g., Windows login)



## AI Assistant Capabilities
Solarus is designed as a local AI assistant that can:
- **Voice/Text Command Recognition**: Accept input via voice (with wake word detection) or text, and process spoken or typed commands.
- **Application Control**: Launch, switch, and close local applications (e.g., web browsers, IDEs, media players).
- **Web Interaction**: Open websites, perform searches, and interact with web services via APIs.
- **Face-Based Authentication**: Utilize facial recognition (as documented) for secure user identification before executing sensitive commands.
- **Task Automation**: Execute predefined workflows or scripts based on user input.
- **Screen/Vision Interaction**: Capture and interpret screen content to understand visual context and enable GUI automation.
- **Context Awareness**: Maintain session context and long-term memory stored in Obsidian to provide personalized responses. The system utilizes multiple specialized AI models that activate based on detected context and user activity patterns.

## Workflow Model
The Solarus assistant operates in the following workflow:
1. **Initialization**: Load models, activate audio/text input, prepare system interfaces, connect to Obsidian vault for long-term memory access, and initialize screen capture capabilities.
2. **Input Detection**: Listen for wake word (voice) or await text input.
3. **Screen Capture**: Periodically capture screen content to maintain visual awareness of user's current activity.
4. **Context Analysis**: Analyze current context (applications open, time, recent activity, screen content) to determine appropriate AI model and load necessary resources.
5. **Model Selection**: Activate the appropriate specialized AI model based on detected context (general purpose, coding, writing, analytical, etc.).
6. **Command Acquisition**: For voice input, record and convert speech to text; for text input, use directly. Then parse intent using the active model.
7. **Authentication Check**: For privileged actions, trigger face verification via the login module.
8. **Action Execution**: Based on intent, invoke appropriate modules (app launcher, web search, screen interaction, etc.) using the active model's capabilities.
9. **Feedback**: Provide auditory or visual feedback on command execution.
10. **Context Update**: Update internal state and store relevant information in Obsidian markdown files for long-term memory.
11. **Resource Management**: Unload unused models to conserve resources while maintaining quick reload capability.

## Integration with Face Recognition
The existing face recognition module (detailed above) serves as the authentication layer for Solarus. Before executing commands that modify system settings or access sensitive data, Solarus will:
- Activate the webcam.
- Run the face tracking and identity extraction pipeline.
- Compare the extracted features against the trained model.
- Proceed only if confidence exceeds a threshold (e.g., 0.8) for the authorized user.

## Future Enhancements
- Natural language understanding with local LLMs.
- Integration with home automation (IoT devices).
- Custom skill system for community contributions.
- Offline documentation retrieval.
application-control-module context-management dynamic-model-switching face-recognition-system screen-interaction-module setup-guide solarus solarus-project task-automation-system text-command-system voice-command-system web-interaction-module

## Tags
#application-control-module #context-management #dynamic-model-switching #face-recognition-system #screen-interaction-module #setup-guide #solarus #solarus-project #task-automation-system #text-command-system #voice-command-system #web-interaction-module

## Hashtags
#facerecognitionsystem #voicecommandsystem #textcommandsystem #applicationcontrolmodule #webinteractionmodule #taskautomationsystem #contextmanagement #dynamicmodelswitching #screeninteractionmodule #setupguide
