---
tags: [user, api_reference, api, reference]
---



# API Reference

This document provides detailed information about the Solarus AI assistant's API for developers who want to extend, integrate with, or build upon the system.

## Overview
The Solarus API enables programmatic access to the assistant's core functionality, allowing developers to create custom integrations, extensions, and applications that leverage Solarus's capabilities. The API is designed to be intuitive, consistent, and well-documented.

## API Architecture
Solarus follows a modular architecture where each major component exposes its functionality through well-defined interfaces. The API is organized by module, mirroring the internal architecture of the assistant.

## Authentication
Most API endpoints require authentication for security, especially those that can control applications, access sensitive data, or execute arbitrary commands.

### API Keys
- Generate API keys in the Solarus configuration interface
- Store keys securely; they provide access to your Solarus instance
- Different permission levels available (read-only, standard control, admin)

### Authentication Methods
1. **Header-based**: `Authorization: Bearer <api_key>`
2. **Parameter-based**: `?api_key=<api_key>` (less secure, for simple integrations)
3. **Session-based**: For web interfaces that maintain login state

## Core API Endpoints

### System Control
```
POST /api/system/status
GET  /api/system/version
POST /api/system/restart
POST /api/system/shutdown
GET  /api/system/info
```

### Voice Input
```
POST /api/voice/listen          # Start listening for voice command
POST /api/voice/wake-word       # Configure wake word detection
GET  /api/voice/devices         # List available audio input devices
POST /api/voice/tts             # Convert text to speech
```

### Text Input
```
POST /api/text/process          # Process a text command
GET  /api/text/history          # Get command history
POST /api/text/commands         # Define custom text commands
```

### Application Control
```
POST /api/apps/launch           # Launch an application
POST /api/apps/switch           # Switch focus to application
POST /api/apps/close            # Close an application
GET  /api/apps/list             # List running applications
POST /api/apps/send-keys        # Send keyboard input to application
POST /api/apps/window-state     # Control window (minimize, maximize, etc.)
```

### Web Interaction
```
POST /api/web/open              # Open a URL
POST /api/web/search            # Perform web search
POST /api/web/scrape            # Extract data from webpage
POST /api/web/api-call          # Make request to web API
GET  /api/web/history           # Get browsing history
```

### Face Recognition
```
POST /api/auth/authenticate     # Perform face authentication
POST /api/auth/enroll           # Enroll new user
GET  /api/auth/users            # List enrolled users
DELETE /api/auth/users/{id}     # Remove user
GET  /api/auth/status           # Get authentication status
```

### Task Automation
```
POST /api/automation/run        # Execute a workflow
POST /api/automation/create     # Create new workflow
GET  /api/automation/workflows  # List available workflows
PUT  /api/automation/workflows/{id}  # Update workflow
DELETE /api/automation/workflows/{id} # Delete workflow
GET  /api/automation/executions # Get execution history
```

### Context Management
```
GET  /api/context/session       # Get current session context
GET  /api/context/user          # Get user profile and preferences
POST /api/context/update        # Update context information
GET  /api/context/history       # Get interaction history
POST /api/context/clear         # Clear specific context data
```

## Data Models
All API communication uses JSON format. Here are the primary data models:

### Command Response
```json
{
  "success": boolean,
  "data": object,
  "error": string|null,
  "timestamp": string (ISO 8601),
  "request_id": string
}
```

### Application Info
```json
{
  "name": string,
  "exe_path": string,
  "window_title": string|null,
  "process_id": number,
  "is_running": boolean,
  "window_state": string  // normal, minimized, maximized, hidden
}
```

### Web Search Result
```json
{
  "title": string,
  "url": string,
  "snippet": string,
  "position": number,
  "source": string  // google, bing, duckduckgo, etc.
}
```

### Authentication Result
```json
{
  "authenticated": boolean,
  "confidence": number (0.0-1.0),
  "user_id": string|null,
  "user_name": string|null,
  "timestamp": string (ISO 8601)
}
```

## WebSocket Events
For real-time communication, Solarus supports WebSocket connections for push notifications and live updates.

### Connection
```
Connect to: ws://localhost:8765/solarus/ws
```

### Events
- `context_update` - Notification when context changes significantly
- `command_complete` - Result of command execution
- `system_alert` - Important system notifications
- `workflow_progress` - Updates during long-running automation
- `auth_status_change` - Authentication state modifications

## Extension Points
Developers can extend Solarus through several mechanisms:

### Custom Commands
Create new voice or text commands by implementing the Command interface and registering with the command processor.

### Application Controllers
Extend application control capabilities by creating adapters for specific applications or automation frameworks.

### Web Service Integrations
Add new API integrations by implementing the WebService interface and configuring authentication.

### Workflow Actions
Create custom actions for the task automation system by implementing the Action interface.

### Context Providers
Contribute to context management by implementing ContextProvider interfaces for specialized data sources.

## Security Considerations
- All API endpoints implement rate limiting to prevent abuse
- Sensitive operations require appropriate permission levels
- Input validation and sanitization on all API endpoints
- Audit logging of all API access for security monitoring
- Secure configuration storage for API keys and credentials
- HTTPS/WSS recommended for production deployments

## Error Handling
The API uses standard HTTP status codes:
- 200: Success
- 400: Bad Request (invalid parameters)
- 401: Unauthorized (missing or invalid authentication)
- 403: Forbidden (insufficient permissions)
- 404: Not Found (endpoint or resource doesn't exist)
- 429: Too Many Requests (rate limiting)
- 500: Internal Server Error
- 503: Service Unavailable (temporary overload)

## Versioning
The API follows semantic versioning:
- Backward-compatible changes increment the minor version (1.x → 1.x+1)
- Breaking changes increment the major version (1.x → 2.x)
- Patch versions (x.y.z) indicate bug fixes and minor improvements

Current API Version: 1.0.0

## SDKs and Client Libraries
Official client libraries are available for:
- Python: `pip install solarus-sdk`
- JavaScript/TypeScript: `npm install @solarus/sdk`
- .NET: `nuget install Solarus.SDK`
- REST API: Direct HTTP calls to endpoints

## Examples

### Python Example
```python
import requests
import json

# Configure API access
API_URL = "http://localhost:8000"
API_KEY = "your_api_key_here"
headers = {"Authorization": f"Bearer {API_KEY}"}

# Launch an application
response = requests.post(
    f"{API_URL}/api/apps/launch",
    headers=headers,
    json={"application": "notepad"}
)
print(response.json())

# Process a text command
response = requests.post(
    f"{API_URL}/api/text/process",
    headers=headers,
    json={"text": "search for python tutorials"}
)
result = response.json()
if result["success"]:
    print(f"Search completed: {result['data']['result']}")
```

### JavaScript Example (Browser)
```javascript
const API_URL = "http://localhost:8000";
const API_KEY = "your_api_key_here";

// Initialize WebSocket for real-time updates
const ws = new WebSocket(`ws://localhost:8000/solarus/ws`);
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log("Solarus update:", data);
};

// Send a command
fetch(`${API_URL}/api/text/process`, {
    method: "POST",
    headers: {
        "Authorization": `Bearer ${API_KEY}`,
        "Content-Type": "application/json"
    },
    body: JSON.stringify({text: "open github.com"})
})
.then(response => response.json())
.then(data => console.log("Command result:", data))
.catch(error => console.error("Error:", error));
```

## Related Notes
- [[Solarus|Main Documentation]]
- [[Voice Command System]]
- [[Text Command System]]
- [[Application Control Module]]
- [[Web Interaction Module]]
- [[Task Automation System]]
- [[Context Management]]
- [[Setup Guide]]
- [[Troubleshooting Guide]]
api-reference application-control-module context-management setup-guide solarus task-automation-system text-command-system troubleshooting-guide voice-command-system web-interaction-module

## Tags
#api #api-reference #application-control-module #context-management #setup-guide #solarus #task-automation-system #text-command-system #troubleshooting-guide #voice-command-system #web-interaction-module

## Hashtags
#solarus #voicecommandsystem #textcommandsystem #applicationcontrolmodule #webinteractionmodule #taskautomationsystem #contextmanagement #setupguide #troubleshootingguide
