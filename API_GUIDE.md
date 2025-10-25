# 🚀 Agentic Tutor API Guide

## Overview

The Agentic Tutor API provides RESTful endpoints for integrating the intelligent tutoring system into external applications. It supports real-time streaming using Server-Sent Events (SSE) and stateful session management.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables

```bash
export GOOGLE_API_KEY="your-google-api-key"
export TAVILY_API_KEY="your-tavily-api-key"
```

### 3. Start the API Server

```bash
python api_server.py
```

The server will start on `http://localhost:8000`

### 4. Access Documentation

- **Interactive API Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## API Endpoints

### 1. Health Check

**Endpoint**: `GET /health`

**Description**: Check if the API is running and get server status.

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-23T10:30:00",
  "active_sessions": 3
}
```

### 2. Start Streaming Session

**Endpoint**: `POST /tutor/stream/{session_id}`

**Description**: Start a new tutoring session with real-time streaming updates.

**Path Parameters**:
- `session_id` (string): Unique identifier for the session

**Request Body**:
```json
{
  "topic": "Neural Networks",
  "stream_tokens": true
}
```

**Response**: Server-Sent Events (text/event-stream)

**Event Types**:

1. **session_started**
```json
{
  "type": "session_started",
  "topic": "Neural Networks",
  "session_id": "session_123",
  "timestamp": "2025-10-23T10:30:00"
}
```

2. **llm_token** (real-time token streaming)
```json
{
  "type": "llm_token",
  "content": "Neural networks are ",
  "node": "generation_agent",
  "session_id": "session_123",
  "timestamp": "2025-10-23T10:30:01"
}
```

3. **node_complete**
```json
{
  "type": "node_complete",
  "node": "research_agent",
  "output": {...},
  "session_id": "session_123",
  "timestamp": "2025-10-23T10:30:05"
}
```

4. **interrupt** (requires user interaction)
```json
{
  "type": "interrupt",
  "interrupt_data": {
    "type": "prerequisite_selection",
    "prerequisites": ["Machine Learning Basics", "Linear Algebra"]
  },
  "session_id": "session_123",
  "timestamp": "2025-10-23T10:30:10"
}
```

5. **error**
```json
{
  "type": "error",
  "message": "Error description",
  "session_id": "session_123",
  "timestamp": "2025-10-23T10:30:15"
}
```

### 3. Resume Session

**Endpoint**: `POST /tutor/resume/{session_id}`

**Description**: Resume a session with user response after an interrupt.

**Path Parameters**:
- `session_id` (string): Session identifier

**Request Body**:
```json
{
  "action": "select_prerequisites",
  "known_prerequisites": ["Machine Learning Basics", "Linear Algebra"]
}
```

**Actions**:
- `select_prerequisites` - Submit prerequisite selection (requires `known_prerequisites` field)
- `continue` - Continue to next topic after lesson review
- `ask_question` - Ask a question about current topic (requires `question` field)
- `regenerate` - Regenerate the current lesson content

**Response**:
```json
{
  "success": true,
  "session_id": "session_123",
  "state": {...},
  "interrupt": {...},
  "workflow_completed": false,
  "timestamp": "2025-10-23T10:35:00"
}
```

### 4. Get Session State

**Endpoint**: `GET /tutor/state/{session_id}`

**Description**: Get the current state of a session.

**Path Parameters**:
- `session_id` (string): Session identifier

**Response**:
```json
{
  "success": true,
  "state": {
    "initial_topic": "Neural Networks",
    "workflow_stage": "learning",
    "current_topic": "Activation Functions",
    "learning_roadmap": ["Linear Algebra", "Neural Networks"],
    "known_prerequisites": ["Machine Learning Basics"],
    "unknown_prerequisites": ["Linear Algebra"],
    "current_lesson": "...",
    "awaiting_user_input": true
  },
  "interrupt": {
    "type": "topic_review",
    "data": {...}
  },
  "workflow_stage": "learning"
}
```

### 5. Delete Session

**Endpoint**: `DELETE /tutor/session/{session_id}`

**Description**: Delete a session and free resources.

**Path Parameters**:
- `session_id` (string): Session identifier

**Response**:
```json
{
  "success": true,
  "message": "Session session_123 deleted",
  "timestamp": "2025-10-23T10:40:00"
}
```

## Usage Examples

### Python (with requests)

```python
import requests
import json

API_URL = "http://localhost:8000"
session_id = "my_session_123"

# Start streaming session
response = requests.post(
    f"{API_URL}/tutor/stream/{session_id}",
    json={"topic": "Neural Networks", "stream_tokens": True},
    stream=True
)

for line in response.iter_lines():
    if line:
        decoded = line.decode('utf-8')
        if decoded.startswith('data: '):
            event = json.loads(decoded[6:])
            print(f"Event: {event['type']}")
            
            if event['type'] == 'interrupt':
                # Handle interrupt
                interrupt_type = event['interrupt_data']['type']
                
                if interrupt_type == 'prerequisite_selection':
                    # Resume with selection
                    requests.post(
                        f"{API_URL}/tutor/resume/{session_id}",
                        json={"action": "select_prerequisites", "known_prerequisites": ["Linear Algebra"]}
                    )
```

### JavaScript (Browser)

```javascript
const sessionId = 'session_' + Date.now();
const apiUrl = 'http://localhost:8000';

// Start streaming session using fetch
fetch(`${apiUrl}/tutor/stream/${sessionId}`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        topic: 'Neural Networks',
        stream_tokens: true
    })
})
.then(response => {
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    
    function readStream() {
        reader.read().then(({done, value}) => {
            if (done) return;
            
            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');
            
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const event = JSON.parse(line.substring(6));
                    handleEvent(event);
                }
            }
            
            readStream();
        });
    }
    
    readStream();
});

function handleEvent(event) {
    switch(event.type) {
        case 'llm_token':
            document.getElementById('output').innerHTML += event.content;
            break;
        case 'interrupt':
            handleInterrupt(event.interrupt_data);
            break;
        // ... handle other events
    }
}
```

### cURL

```bash
# Start session (streaming)
curl -N -X POST "http://localhost:8000/tutor/stream/test_session" \
  -H "Content-Type: application/json" \
  -d '{"topic": "Neural Networks", "stream_tokens": true}'

# Get session state
curl -X GET "http://localhost:8000/tutor/state/test_session"

# Resume with prerequisite selection
curl -X POST "http://localhost:8000/tutor/resume/test_session" \
  -H "Content-Type: application/json" \
  -d '{"action": "select_prerequisites", "known_prerequisites": ["Linear Algebra"]}'

# Resume after topic review
curl -X POST "http://localhost:8000/tutor/resume/test_session" \
  -H "Content-Type: application/json" \
  -d '{"action": "continue"}'

# Delete session
curl -X DELETE "http://localhost:8000/tutor/session/test_session"
```

## Testing

### Option 1: HTML Test Client

Open `test_api_client.html` in your browser:

```bash
# On Windows
start test_api_client.html

# On Mac
open test_api_client.html

# On Linux
xdg-open test_api_client.html
```

### Option 2: Python Test Script

```bash
python test_api.py
```

### Option 3: Interactive API Docs

Visit http://localhost:8000/docs to use FastAPI's built-in Swagger UI.

## Session Management

### Session Lifecycle

1. **Create**: Session is created when you first call `/tutor/stream/{session_id}`
2. **Active**: Session persists in memory and maintains state
3. **Interrupt**: Session pauses and waits for user input
4. **Resume**: Continue session with `/tutor/resume/{session_id}`
5. **Delete**: Explicitly delete with `/tutor/session/{session_id}` or let it timeout

### Session State

Sessions maintain:
- **Learning roadmap**: Personalized list of topics based on prerequisite selection
- **Known/Unknown prerequisites**: User's knowledge state for intelligent roadmap generation
- **Current progress**: Which topic is being studied and lesson completion status
- **Lesson history**: All completed lessons with content and Q&A
- **Interactive state**: Current pause points requiring user input (prerequisite selection, topic reviews)
- **Streaming state**: Real-time token streaming and node completion tracking

## Interrupt Types

### 1. Prerequisite Selection

Occurs at the beginning of a learning session.

**Interrupt Data**:
```json
{
  "type": "prerequisite_selection",
  "prerequisites": ["Topic 1", "Topic 2"],
  "message": "Select topics you already know"
}
```

**Resume Action**:
```json
{
  "action": "select_prerequisites",
  "known_prerequisites": ["Topic 1"]
}
```

### 2. Topic Review

Occurs after each lesson.

**Interrupt Data**:
```json
{
  "type": "topic_review",
  "topic": "Neural Networks",
  "lesson_content": "...",
  "options": [...]
}
```

**Resume Actions**:
- Continue: `{"action": "continue"}`
- Ask Question: `{"action": "ask_question", "question": "..."}`
- Regenerate: `{"action": "regenerate"}`

## Error Handling

### Error Response Format

```json
{
  "detail": "Error description"
}
```

### Common HTTP Status Codes

- `200 OK`: Success
- `404 Not Found`: Session not found
- `422 Unprocessable Entity`: Invalid request body
- `500 Internal Server Error`: Server error

### Error Recovery

```python
try:
    response = requests.post(f"{API_URL}/tutor/stream/{session_id}", ...)
    response.raise_for_status()
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 404:
        print("Session not found, creating new one...")
    elif e.response.status_code == 500:
        print("Server error, retrying...")
```

## Performance Considerations

### Streaming

- **Token streaming**: Provides real-time feedback (~50-100ms latency)
- **Connection**: Keep-alive for entire session
- **Buffering**: Disabled for immediate delivery

### Session Storage

- **Current**: In-memory (simple, fast, but not persistent)
- **Production**: Consider Redis or database for persistence
- **Cleanup**: Implement session timeout/cleanup for production

## Security Considerations

### API Keys

Store API keys securely:
```bash
# Use environment variables
export GOOGLE_API_KEY="..."
export TAVILY_API_KEY="..."

# Or use .env file (don't commit to git!)
# .env
GOOGLE_API_KEY=your-key
TAVILY_API_KEY=your-key
```

### CORS

Configure CORS appropriately for production:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specific domains only
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)
```

### Rate Limiting

Consider adding rate limiting for production:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/tutor/stream/{session_id}")
@limiter.limit("5/minute")
async def stream_tutor_session(...):
    ...
```

## Deployment

### Local Development

```bash
python api_server.py
```

### Production with Uvicorn

```bash
uvicorn api_server:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables for Production

```bash
# Required
GOOGLE_API_KEY=your-key
TAVILY_API_KEY=your-key

# Optional
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=info
```

## Troubleshooting

### Issue: Stream connection drops

**Solution**: Check firewall settings and nginx configuration (if using reverse proxy).

### Issue: Sessions not persisting

**Solution**: Current implementation uses in-memory storage. For persistence, implement Redis or database backend.

### Issue: Slow streaming

**Solution**: 
- Check LLM API latency
- Ensure `stream_tokens=true` is set
- Verify no intermediate proxies are buffering

### Issue: CORS errors in browser

**Solution**: Configure CORS middleware with appropriate origins.

## Integration Examples

### LibreChat Integration

The API is designed for easy integration with platforms like LibreChat:

```javascript
// Custom endpoint for LibreChat
app.post('/api/tutoring/start', async (req, res) => {
    const { topic, userId } = req.body;
    const sessionId = `librechat_${userId}_${Date.now()}`;
    
    // Start streaming session
    const response = await fetch(`${TUTOR_API}/tutor/stream/${sessionId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic, stream_tokens: true })
    });
    
    // Handle SSE stream and forward to client
    // ... implementation details
});
```

### React.js Frontend

```jsx
import React, { useState, useEffect } from 'react';

function TutorChat({ topic }) {
    const [messages, setMessages] = useState([]);
    const [currentInterrupt, setCurrentInterrupt] = useState(null);
    
    useEffect(() => {
        startTutorSession(topic);
    }, [topic]);
    
    const startTutorSession = (topic) => {
        const sessionId = `session_${Date.now()}`;
        
        fetch(`/api/tutor/stream/${sessionId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ topic, stream_tokens: true })
        })
        .then(response => {
            const reader = response.body.getReader();
            processStream(reader);
        });
    };
    
    // ... rest of component
}
```

## Next Steps

1. **Enhanced UI Integration**: Build rich interactive components for prerequisite selection
2. **Authentication**: Implement JWT or API key authentication for production
3. **Persistence**: Add Redis or PostgreSQL for session storage across restarts
4. **Monitoring**: Integrate logging and metrics (Prometheus, DataDog)
5. **Rate Limiting**: Protect against abuse with request throttling
6. **Webhooks**: Notify external systems of learning progress events

## Support

For issues or questions:
- Check the main README.md
- Review the upgrade-plan.md for implementation details
- Open an issue on the repository

---

**Built with**: FastAPI, LangGraph, LangChain, Google Gemini, Tavily Search

