# Agentic Tutor

[![CI](https://github.com/langchain-ai/new-langgraph-project/actions/workflows/unit-tests.yml/badge.svg)](https://github.com/langchain-ai/new-langgraph-project/actions/workflows/unit-tests.yml)
[![Integration Tests](https://github.com/langchain-ai/new-langgraph-project/actions/workflows/integration-tests.yml/badge.svg)](https://github.com/langchain-ai/new-langgraph-project/actions/workflows/integration-tests.yml)

An agentic workflow created using LangGraph for helping students of ML and AI improve their grip on the topic. The system uses Google Gemini 2.0 Flash for intelligent tutoring with multi-agent collaboration.

## Features

- **Prerequisites Discovery**: Automatically identifies what you need to know before learning a topic
- **Personalized Roadmaps**: Creates custom learning paths based on your current knowledge
- **Multi-Agent Teaching**: Research, critique, and generation agents work together to create quality content
- **Web Search Integration**: Uses Tavily for up-to-date information gathering
- **Conversation Memory**: Maintains context throughout your learning journey

## Architecture

1. **Prerequisites Agent**: Finds all necessary prerequisites for your target topic
2. **Roadmap Agent**: Creates a personalized learning sequence
3. **Research Agent**: Gathers comprehensive information using web search
4. **Critique Agent**: Reviews and validates research quality
5. **Generation Agent**: Creates structured educational content

## Getting Started

### Prerequisites

- Python 3.11+
- Google API key for Gemini 2.0 Flash
- Tavily API key for web search
- LangSmith API key (optional, for tracing)

### Installation

1. Install dependencies:

```bash
cd agentic-tutor
pip install -e . "langgraph-cli[inmem]"
```

2. Set up environment variables:

Create a `.env` file with:

```bash
# Required
GOOGLE_API_KEY=your_google_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here

# Optional (for tracing)
LANGSMITH_API_KEY=your_langsmith_api_key_here
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=agentic-tutor
```

### Quick Test

Test the workflow with the included test script:

```bash
python test_workflow.py
```

### Running the Application

Start the LangGraph server:

```bash
langgraph dev
```

This will start the server and open LangGraph Studio where you can:
- Test your agent interactively
- Visualize the graph execution
- Debug with time travel features
- Monitor conversation state

### Usage

1. **Start a Session**: Provide your target learning topic and a unique thread_id
   ```python
   config = {"configurable": {"thread_id": "my-learning-session"}}
   initial_state = {"initial_topic": "Convolutional Neural Networks"}
   ```

2. **Review Prerequisites**: The system will find and display prerequisite topics
3. **Select Unknowns**: Indicate which prerequisites you don't know yet
4. **Follow the Roadmap**: Work through the personalized learning sequence
5. **Interactive Learning**: Each topic includes research, review, and structured lessons
6. **Resume Anytime**: Use the same thread_id to continue your learning session

### Inspecting State
```python
# Check current conversation state
snapshot = graph.get_state(config)
print(f"Current stage: {snapshot.values['workflow_stage']}")
print(f"Progress: {snapshot.values['current_topic_index']}/{len(snapshot.values['learning_roadmap'])}")
```

## Configuration

The system uses Pydantic models for robust state management and configuration:

### Configuration Options
- `model_name`: Google Gemini model to use (default: "gemini-2.0-flash-exp")
- `max_research_retries`: Maximum retries for research improvement (default: 3)
- `temperature`: LLM temperature for consistency (default: 0.1)

### State Management & Memory
The system uses LangGraph's built-in checkpointing for conversation memory:
- **MemorySaver**: In-memory checkpointing for development (production would use SqliteSaver/PostgresSaver)
- **Thread-based Conversations**: Each conversation has a unique `thread_id` for state persistence
- **State Inspection**: Use `graph.get_state(config)` to inspect conversation state at any time

The `AgentState` Pydantic model tracks:
- **Workflow Progress**: Current stage (prerequisites/roadmap/learning/complete)
- **Learning Data**: Prerequisites, roadmap, current topic index
- **Conversation History**: Full message history with proper typing
- **Research Content**: Current research and critique feedback
- **Error Handling**: Retry counters and completion flags

## Development

### Local Development

The project uses LangGraph Studio for development:

1. Make changes to `src/agent/graph.py`
2. Changes are automatically reloaded
3. Test in the Studio interface
4. Use time travel for debugging

### Testing

Run tests:

```bash
# Unit tests
make test

# Integration tests  
make integration_tests

# Linting
make lint
```

## Deployment

Deploy to LangGraph Platform:

1. Push your code to GitHub
2. Connect repository to LangGraph Platform
3. Deploy with automatic scaling

For detailed deployment instructions, see the [LangGraph Platform documentation](https://langchain-ai.github.io/langgraph/cloud/quick_start/).

## API Keys Setup

### Google Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Add to your `.env` file as `GOOGLE_API_KEY`

### Tavily API Key

1. Sign up at [Tavily](https://tavily.com/)
2. Get your API key from the dashboard
3. Add to your `.env` file as `TAVILY_API_KEY`

### LangSmith API Key (Optional)

1. Sign up at [LangSmith](https://smith.langchain.com/)
2. Create an API key
3. Add to your `.env` file as `LANGSMITH_API_KEY`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details.
