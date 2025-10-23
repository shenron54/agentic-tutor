# Agentic Tutor

An intelligent agentic workflow created using LangGraph for helping students learn ML and AI topics through personalized learning paths with human-in-the-loop interaction.

## Project Status: Major Refactor Complete ✅

The project has undergone a significant refactoring to a modular, scalable architecture. The core logic is now separated into distinct modules for state, nodes, routing, and utilities, making the system more maintainable and ready for API integration. Key bugs have been resolved, and a formal process for tracking bugs and features is now in place.

### ✅ Implemented Features

#### Core Workflow
- **🔍 Smart Prerequisites Discovery**: Identifies specific ML/AI prerequisites for a given topic.
- **👤 Human-in-the-Loop Selection**: Uses LangGraph's `interrupt()` feature to allow users to select their known prerequisites.
- **🗺️ Personalized Roadmaps**: Creates optimal learning sequences based on the user's knowledge gaps.
- **📊 Progress Tracking**: Automatically progresses through the learning roadmap topic-by-topic.

#### Multi-Agent Architecture
- **🔬 Research Agent**: Uses Tavily to perform web searches for up-to-date information.
- **🧐 Critique Agent**: Reviews and validates the quality and completeness of the research.
- **📝 Generation Agent**: Creates structured educational content and handles Q&A.

#### Technical Implementation  
- **🧩 Modular Project Architecture**: The codebase is now highly modular, with logic separated into `core`, `nodes`, `routing`, and `utils`.
- **💾 Conversation Memory**: LangGraph checkpointing with `MemorySaver` enables session persistence.
- **🔄 Async Support**: Fully asynchronous implementation for a responsive and non-blocking workflow.
- **🛠️ Robust State Management**: Pydantic models provide type-safe state management.
- **📄 Formal Documentation**: `BUGS.md` and `FEATURES.md` are now used to track project status.
- **⚡ Streaming Support**: Real-time token-level streaming for immediate feedback (both in UI and API).
- **🌐 REST API**: FastAPI server for external integration with SSE streaming endpoints.

#### Recent Updates
- ✅ **Streaming & API Integration**: Added complete FastAPI server with SSE streaming (v1.1.0)
- ✅ **JSON Serialization Fixed**: Resolved BaseMessage serialization with recursive `model_dump()` approach
- ✅ **Token-Level Streaming**: Real-time LLM token streaming fully functional
- ✅ **Full Test Coverage**: All endpoints tested with interrupts and resume functionality
- ✅ **Resolved Question Tracking**: Questions are now reliably tracked in the agent's state
- ✅ **Identified Roadmap Generation Bug**: Pinpointed the root cause of the "all-but-one" prerequisite bug

### 🐛 Bugs and ✨ Features

This project now uses dedicated markdown files to track bugs and plan future features.

-   **[View Current Bugs](./BUGS.md)**
-   **[View Feature Roadmap](./FEATURES.md)**

---

## Architecture Overview

The agentic workflow is structured as a state graph, allowing for complex, conditional routing between different functional nodes. The diagram below illustrates the flow from the initial topic selection to the final session summary.

![Agentic Tutor Workflow](graph.png)

---

## Quick Start

### Prerequisites
- Python 3.9+
- A Google API key for the Gemini model family.
- A Tavily API key for the web search functionality.

### Installation & Setup

1.  **Clone the repository and navigate to the project root.**

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up environment variables**:
    Create a `.env` file in the project root and add your API keys:
    ```env
    # Required for core functionality
    GOOGLE_API_KEY="your_google_api_key_here"
    TAVILY_API_KEY="your_tavily_api_key_here"
    
    # Optional (for LangSmith tracing)
    LANGSMITH_API_KEY="your_langsmith_api_key_here"
    LANGSMITH_TRACING="true"
    LANGSMITH_PROJECT="agentic-tutor"
    ```

### Running the Application

#### Option 1: Streamlit UI (Recommended for Learning)

The primary way to interact with the tutoring system is through the beautiful Streamlit interface:

```bash
streamlit run app.py
```

This provides an interactive, user-friendly experience with:
- Real-time streaming responses (token-by-token)
- Visual progress tracking
- Interactive lesson reviews and Q&A
- Session history

#### Option 2: FastAPI Server (For External Integration)

For integrating the tutor into external applications, use the REST API:

```bash
python api_server.py
```

This starts a FastAPI server on `http://localhost:8000` with:
- **Streaming endpoints** with Server-Sent Events (SSE)
- **Session management** with stateful workflows
- **RESTful API** for easy integration
- **Auto-generated documentation** at `/docs`

**Quick API Example:**
```bash
# Start a streaming session
curl -N -X POST "http://localhost:8000/tutor/stream/my_session" \
  -H "Content-Type: application/json" \
  -d '{"topic": "Neural Networks", "stream_tokens": true}'
```

For detailed API documentation, see **[API_GUIDE.md](./API_GUIDE.md)**

**API Features:**
- ✅ Real-time token streaming with Server-Sent Events
- ✅ Session management with state persistence  
- ✅ Interrupt handling for human-in-the-loop workflows
- ✅ Comprehensive error handling and recovery
- ✅ Auto-generated OpenAPI documentation
- ✅ Test clients included (HTML + Python)

### Usage Example (Programmatic)

You can also interact with the workflow programmatically. This is useful for testing or embedding the agent in other applications.

```python
from agentic-tutor.src.agent.workflow import graph_with_memory

# Use a unique ID for each session to maintain state
config = {"configurable": {"thread_id": "my-learning-session-1"}}

# Start a new learning session
initial_state = {"initial_topic": "Q-Learning"}
events = graph_with_memory.stream(initial_state, config, stream_mode="values")

for event in events:
    # Process events as they stream in
    print(event)

# You can resume the session later using the same thread_id
snapshot = graph_with_memory.get_state(config)
print(f"Current topic: {snapshot.values['current_topic']}")
```

## Technical Stack

- **Framework**: LangGraph
- **LLM**: Google Gemini
- **Search**: Tavily
- **State Management**: Pydantic
- **UI**: Streamlit
- **API**: FastAPI with Server-Sent Events (SSE)
- **Deployment**: Uvicorn

## Contributing

Contributions are welcome! Please see the **[Feature Roadmap](./FEATURES.md)** for high-priority items to work on.

1.  Fork the repository.
2.  Create a feature branch.
3.  Add tests for your new functionality.
4.  Submit a pull request for review.

## License

This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for details.

