# Agentic Tutor

An intelligent agentic workflow created using LangGraph for helping students learn ML and AI topics through personalized learning paths with human-in-the-loop interaction.

## Project Status: Core Features Complete ✅

The system is fully functional with advanced multi-agent architecture, proper human-in-the-loop interaction, and robust async support. Recent major fixes include improved prerequisites analysis and working interrupt-based user selection.

### ✅ Implemented Features

#### Core Workflow
- **🔍 Smart Prerequisites Discovery**: Identifies specific ML/AI prerequisites (fixed to avoid generic topics)
- **👤 Human-in-the-Loop Selection**: Working interrupt-based prerequisite selection using `interrupt()`
- **🗺️ Personalized Roadmaps**: Creates optimal learning sequences based on user's knowledge gaps
- **📊 Progress Tracking**: Automatic progression through learning roadmap with completion tracking

#### Multi-Agent Architecture
- **🔬 Research Agent**: Web search integration with Tavily for up-to-date information
- **🔍 Critique Agent**: Reviews and validates research quality and completeness  
- **📝 Generation Agent**: Creates structured educational content and handles Q&A
- **🧩 Modular Subgraph**: Clean research → critique → generation loop in `learning_subgraph.py`

#### Technical Implementation  
- **💾 Conversation Memory**: LangGraph checkpointing with MemorySaver for session persistence
- **🔄 Async Support**: Proper async/await throughout all agents and nodes
- **⚡ Interactive Chat**: CLI interface via `interactive_chat.py` for seamless learning sessions
- **🛠️ Robust Error Handling**: Retry logic, graceful fallbacks, and comprehensive state management
- **📋 Pydantic Models**: Type-safe state management with `AgentState` BaseModel

#### Recent Bug Fixes
- ✅ **Fixed Prerequisites Agent**: Now generates specific ML/AI topics instead of generic ones
- ✅ **Fixed Human Selection**: Replaced simulation with proper LangGraph `interrupt()` function  
- ✅ **Fixed Async Issues**: Removed problematic sync calls, proper `ainvoke()` and `astream()` usage
- ✅ **Fixed Import Paths**: Robust imports with fallback handling
- ✅ **Fixed Subgraph Architecture**: Modular learning subgraph working correctly

### 🐛 Current Issues & Next Steps

#### Critical Issues to Fix
1. **📺 CLI Streaming Display Bug**
   - **Problem**: Actual lesson content not displaying in CLI despite successful generation
   - **Symptoms**: Can see "Subgraph Research/Critique/Generation" messages but missing lesson content
   - **Root Cause**: Async streaming vs getting complete content blocks
   - **Priority**: HIGH - affects core user experience

2. **❓ Missing Follow-up Questions**
   - **Problem**: No interactive Q&A after each topic completion
   - **Impact**: Reduced engagement and assessment capability
   - **Priority**: MEDIUM

#### Technical Improvements Needed
3. **🎨 Better UI for Async Responses**
   - **Current**: CLI limiting for complex async streaming
   - **Solution**: Consider Streamlit web interface for better async handling
   - **Priority**: MEDIUM

4. **🔄 Enhanced Session Management**
   - **Current**: Basic thread-based sessions
   - **Needed**: Better resume functionality and session analytics
   - **Priority**: LOW

#### Potential Solutions Under Investigation
- **Streamlit Web Interface**: Better async response handling than CLI
- **Content Buffering**: Collect complete responses before display
- **Streaming Optimization**: Fix LangGraph streaming for CLI display

## Architecture Overview

```
User Input (Topic) → Prerequisites Agent → [Human Review] → Roadmap Agent → Learning Loop:
                                                                            ↓
                                                              Research Agent → Critique Agent → Generation Agent
                                                                            ↑                                   ↓
                                                                            ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ←
                                                                         (Continue/End)
```

## Quick Start

### Prerequisites
- Python 3.11+
- Google API key for Gemini 2.0 Flash
- Tavily API key for web search

### Installation & Setup

1. **Navigate to the project**:
   ```bash
   cd agentic-tutor
   ```

2. **Install dependencies**:
   ```bash
   pip install -e . "langgraph-cli[inmem]"
   ```

3. **Set up environment variables** (create `.env` file):
   ```bash
   # Required
   GOOGLE_API_KEY=your_google_api_key_here
   TAVILY_API_KEY=your_tavily_api_key_here
   
   # Optional (for tracing)
   LANGSMITH_API_KEY=your_langsmith_api_key_here
   LANGSMITH_TRACING=true
   LANGSMITH_PROJECT=agentic-tutor
   ```

### Running the Application

#### Option 1: Interactive CLI (Recommended for Learning)
```bash
python interactive_chat.py
```
This provides a conversational interface for learning sessions.

#### Option 2: LangGraph Studio (Recommended for Development)
```bash
langgraph dev
```
Opens visual interface for debugging and testing.

#### Option 3: Quick Test
```bash
python test_workflow.py
```
Runs a quick test of the complete workflow.

### Usage Example

```python
from agentic-tutor.src.agent.workflow import graph_with_memory

# Start a learning session
config = {"configurable": {"thread_id": "my-learning-session"}}
initial_state = {"initial_topic": "Q-Learning"}

# The system will:
# 1. Find prerequisites (e.g., "Reinforcement Learning", "Markov Decision Processes")
# 2. Ask which ones you know
# 3. Create a personalized roadmap
# 4. Guide you through each topic with research-backed lessons

# Resume later with the same thread_id
snapshot = graph_with_memory.get_state(config)
print(f"Progress: {snapshot.values['current_topic_index']}/{len(snapshot.values['learning_roadmap'])}")
```

## Key Features

- **🎯 Specific Prerequisites**: Finds relevant ML/AI concepts, not generic topics
- **👤 Human-in-the-Loop**: Proper interrupt-based interaction for prerequisite selection
- **🔬 Research-Backed Content**: Web search ensures up-to-date, accurate information
- **🧩 Modular Architecture**: Clean subgraph design for maintainable code
- **💾 Session Persistence**: Resume learning sessions anytime with thread-based memory
- **⚡ Async-First**: Fully async implementation for responsive interactions

## Technical Stack

- **Framework**: LangGraph for workflow orchestration and state management
- **LLM**: Google Gemini 2.0 Flash via langchain-google-genai
- **Search**: Tavily for real-time web search capabilities
- **State Management**: Pydantic BaseModel for type-safe state tracking
- **Memory**: LangGraph checkpointing with MemorySaver for session persistence
- **Development**: LangGraph Studio for visual debugging and testing
- **Deployment**: LangGraph Platform for production scaling

## Troubleshooting

### Common Issues

#### CLI Not Showing Lesson Content
**Problem**: You see "Subgraph Research/Critique/Generation" messages but no actual lesson content.

**Status**: Known bug - streaming display issue with async responses in CLI.

**Workaround**: Use LangGraph Studio interface for now, or run `test_workflow.py` to see complete responses.

**Solution in Progress**: Investigating Streamlit web interface or content buffering approaches.

#### Prerequisites Too Generic
**Problem**: Getting basic topics like "statistics" instead of specific ML concepts.

**Status**: ✅ FIXED - Prerequisites agent now focuses on specific ML/AI topics.

#### Human Selection Not Working
**Problem**: System not waiting for user input during prerequisite selection.

**Status**: ✅ FIXED - Now uses proper LangGraph `interrupt()` function.

### Getting Help

1. **Check the issue tracker** for known problems
2. **Run tests** with `python test_workflow.py` to verify setup
3. **Use LangGraph Studio** for visual debugging
4. **Check environment variables** are properly set

## Contributing

The project is actively maintained with focus on:

### High Priority
- **Fixing CLI streaming display** - actual lesson content not showing
- **Adding follow-up questions** - interactive Q&A after topics
- **Better async UI** - considering Streamlit web interface

### Medium Priority  
- Enhanced session management and analytics
- More robust error handling and recovery
- Performance optimizations

### How to Contribute
1. Fork the repository
2. Create a feature branch
3. Focus on the issues listed above
4. Add tests for new functionality
5. Submit a pull request

## License

MIT License

