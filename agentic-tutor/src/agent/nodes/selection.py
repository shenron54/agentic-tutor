from typing import Any, Dict

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.types import interrupt

from ..core.state import AgentState


async def human_selection_node(state: AgentState, config: RunnableConfig) -> Dict[str, Any]:
    """Handle human-in-the-loop prerequisite selection.
    
    This node uses the interrupt function to pause execution and wait for
    the user to select which prerequisites they already know.
    """
    print("👤 Human Selection: Waiting for user to select known prerequisites")
    
    # Use interrupt to pause execution and wait for user input
    # The user should provide a list of prerequisites they already know
    user_response = interrupt({
        "type": "prerequisite_selection",
        "message": "Please select which of these prerequisites you already know:",
        "prerequisites": state.prerequisites,
        "instructions": "Provide a list of prerequisites you're already familiar with"
    })
    
    # Process the user's response
    # Expected format: {"known_prerequisites": ["topic1", "topic2", ...]}
    known_prereqs = []
    unknown_prereqs = []
    
    if isinstance(user_response, dict) and "known_prerequisites" in user_response:
        # User provided their known prerequisites
        known_prereqs = user_response["known_prerequisites"]
        # Validate that these are actually from the prerequisite list
        known_prereqs = [p for p in known_prereqs if p in state.prerequisites]
        # Everything else is unknown
        unknown_prereqs = [p for p in state.prerequisites if p not in known_prereqs]
    else:
        # If user response is not in expected format, assume they don't know any prerequisites
        unknown_prereqs = state.prerequisites
    
    # If user knows all prerequisites, they still need to learn the main topic
    if not unknown_prereqs and state.prerequisites:
        # Add a note that user knows all prerequisites
        selection_message = AIMessage(
            content=f"Great! You're already familiar with all the prerequisites:\n" +
                    "\n".join(f"✅ {topic}" for topic in known_prereqs) +
                    f"\n\nLet's proceed directly to learning **{state.initial_topic}**!"
        )
    else:
        selection_message = AIMessage(
            content=f"Based on your selections:\n\n" +
                    f"✅ Known topics ({len(known_prereqs)}):\n" +
                    "\n".join(f"• {topic}" for topic in known_prereqs) if known_prereqs else "• None" +
                    f"\n\n📚 Topics to learn ({len(unknown_prereqs)}):\n" +
                    "\n".join(f"• {topic}" for topic in unknown_prereqs) +
                    "\n\nNow I'll create your personalized learning roadmap!"
        )
    
    return {
        "known_prerequisites": known_prereqs,
        "unknown_prerequisites": unknown_prereqs,
        "user_selection": unknown_prereqs,
        "messages": [selection_message],
        "workflow_stage": "roadmap",
        "awaiting_user_input": False
    } 