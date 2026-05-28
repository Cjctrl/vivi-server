---
tags: [user, dynamic_model_switching, dynamic, model, switching]
---



# Dynamic Model Switching System

This document details the dynamic model switching system in Solarus that enables the assistant to activate different AI models based on context and user activity patterns.

## Overview
The Dynamic Model Switching System allows Solarus to optimize performance and accuracy by deploying specialized AI models for specific tasks rather than relying on a single general-purpose model. The system detects user context and automatically switches to the most appropriate model for the current activity.

## Core Concepts
- **Context Awareness**: The system continuously monitors user activity, applications in use, time of day, and interaction patterns to determine the optimal AI model.
- **Model Specialization**: Different models are optimized for different types of tasks (coding, writing, analysis, general conversation).
- **Seamless Transitions**: Model switching happens transparently without interrupting the user experience.
- **Resource Efficiency**: Only necessary models are loaded in memory, with intelligent unloading of unused models.
- **Obsidian Integration**: Long-term memory and context information are stored in the user's Obsidian vault, enabling cross-model knowledge sharing.

## Model Types and Specializations

### 1. General Purpose Model
- **Use Case**: Everyday conversations, general questions, basic task assistance
- **Strengths**: Broad knowledge base, conversational fluency, versatility
- **Activation**: Default model when no specific context is detected

### 2. Code-Specialized Model
- **Use Case**: Programming tasks, code review, debugging, technical documentation
- **Strengths**: Understanding of programming languages, code patterns, technical concepts
- **Activation Triggers**:
  - Opening IDEs (VS Code, PyCharm, IntelliJ, etc.)
  - Working with code file extensions (.py, .js, .java, .cpp, etc.)
  - Detecting programming keywords in user input
  - Active terminals or command-line interfaces
  - Viewing technical documentation (MDN, Stack Overflow, dev.to, etc.)

### 3. Writing/Creative Model
- **Use Case**: Content creation, storytelling, email writing, documentation
- **Strengths**: Language generation, creativity, tone adaptation, grammatical accuracy
- **Activation Triggers**:
  - Opening writing applications (Word, Google Docs, Notion, etc.)
  - Working with document file extensions (.docx, .txt, .md, etc.)
  - Detecting writing-related keywords ("write", "draft", "compose", etc.)
  - Extended periods of text input without coding patterns
  - Creative applications open (design tools, presentation software)

### 4. Analytical Model
- **Use Case**: Data analysis, logical reasoning, problem-solving, research
- **Strengths**: Logical processing, mathematical reasoning, data interpretation
- **Activation Triggers**:
  - Opening analysis tools (Excel, Jupyter Notebook, RStudio, etc.)
  - Working with data file extensions (.csv, .xlsx, .json, .sql, etc.)
  - Detecting analytical keywords ("analyze", "calculate", "compare", etc.)
  - Spreadsheet or database applications active
  - Research-oriented browsing patterns

### 5. Multimodal Model
- **Use Case**: Complex interactions combining text, voice, and visual input including screen vision
- **Strengths**: Processing multiple input types simultaneously, contextual understanding, screen content interpretation
- **Activation Triggers**:
  - Video calls or conferencing software active
  - Screen sharing or presentation modes
  - Combined voice and text input detected
  - Accessibility features in use
  - Tasks requiring interpretation of visual context
  - Screen content analysis needed for GUI automation or visual assistance

## Implementation Details

### Context Detection Mechanisms
1. **Application Monitoring**: Tracks which applications are currently active and focused
2. **File System Awareness**: Monitors recently accessed or modified files and their types
3. **Input Pattern Analysis**: Examines user input for domain-specific patterns and keywords
4. **Temporal Patterns**: Recognizes regular activity cycles (morning email, afternoon coding, etc.)
5. **Environmental Sensors**: Utilizes available system information (time, location if permitted)
6. **Explicit Commands**: Responds to user requests to switch specific modes ("switch to coding mode")

### Model Management
- **Lazy Loading**: Models are loaded into memory only when needed
- **Intelligent Unloading**: Infrequently used models are unloaded to free resources
- **Preloading Prediction**: Based on patterns, likely-needed models may be preloaded
- **Version Control**: Different model versions can be specified for different use cases
- **Fallback Mechanism**: If a specialized model fails, system falls back to general purpose

### Obsidian Integration for Long-Term Memory
- **Context Storage**: Important interaction context is saved as markdown files in Obsidian
- **Cross-Model Knowledge**: Information learned in one mode is accessible to others via Obsidian
- **Personal Knowledge Base**: Leverages user's existing Obsidian vault as Solarus's long-term memory
- **Semantic Search**: Uses embeddings to find relevant past interactions stored in Obsidian
- **Temporal Awareness**: Tracks when information was stored to apply decay functions
- **Privacy Controls**: Respects Obsidian's permission systems and user-defined privacy settings

### Configuration Options
- **Model Paths**: Specify locations or identifiers for different AI models
- **Activation Thresholds**: Set sensitivity for context detection triggers
- **Resource Limits**: Define maximum memory/CPU usage for model operations
- **Transition Settings**: Control how quickly the system switches between models
- **Fallback Preferences**: Specify which model to use when detection is uncertain
- **Obsidian Vault Path**: Configure which Obsidian vault to use for memory storage
- **Memory Retention Policies**: Define how long different types of context are stored

## Usage Examples

### Scenario 1: Morning Routine to Coding Session
1. **6:00 AM**: User checks email → General Purpose Model active
2. **7:30 AM**: User opens VS Code → System detects IDE, switches to Code-Specialized Model
3. **7:35 AM**: User starts writing comments in code → Context analysis shows mixed activity, maintains Code Model
4. **9:00 AM**: User opens Word document → System detects writing app, switches to Writing Model
5. **9:15 AM**: User returns to coding → System switches back to Code Model
6. **12:00 PM**: User opens Excel for data analysis → System detects spreadsheet, switches to Analytical Model
7. **1:00 PM**: User returns to email and light tasks → System reverts to General Purpose Model

### Scenario 2: Creative Writing Project
1. **2:00 PM**: User opens Scrivener → System detects writing software, activates Writing Model
2. **2:05 PM**: User asks for help with character names → Writing Model generates creative suggestions
3. **2:15 PM**: User opens research browser tabs → System detects research activity, briefly shifts to Analytical Model for fact-checking
4. **2:20 PM**: User returns to writing → System switches back to Writing Model
5. **3:00 PM**: User shares screen for feedback → System detects screen sharing, activates Multimodal Model temporarily
6. **3:15 PM**: User returns to solo writing → System reverts to Writing Model

## Benefits
- **Improved Accuracy**: Specialized models perform better on their domain-specific tasks
- **Faster Response Times**: Optimized models can be more efficient for specific tasks
- **Reduced Resource Usage**: Only necessary model components are loaded
- **Enhanced User Experience**: Responses feel more natural and context-appropriate
- **Knowledge Persistence**: Long-term memory in Obsidian ensures learning persists across sessions and model switches
- **Personalization**: System adapts to individual user patterns and preferences over time

## Related Notes
- [[Solarus|Main Documentation]]
- [[Context Management]]
- [[Setup Guide]]
- [[API Reference]]
- [[Voice Command System]]
- [[Text Command System]]
api-reference context-management dynamic-model-switching dynamic-model-switching-system setup-guide solarus text-command-system voice-command-system

## Tags
#api-reference #context-management #dynamic #dynamic-model-switching #dynamic-model-switching-system #setup-guide #solarus #text-command-system #voice-command-system

## Hashtags
#solarus #contextmanagement #setupguide #apireference #voicecommandsystem #textcommandsystem
