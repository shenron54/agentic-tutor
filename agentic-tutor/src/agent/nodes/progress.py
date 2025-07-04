from typing import Any, Dict

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig

from ..core.state import AgentState


async def progress_tracker_node(state: AgentState, config: RunnableConfig) -> Dict[str, Any]:
    """Track learning progress and update state.
    
    Moves to the next topic in the roadmap or routes to session summary for completion.
    """
    print(f"📊 Progress Tracker: Updating learning progress")
    
    # Mark current topic as completed
    completed_topics = state.completed_topics + [state.current_topic]
    next_index = state.current_topic_index + 1
    
    # Check if we've completed the entire roadmap
    if next_index >= len(state.learning_roadmap):
        # Route to session summary instead of ending directly
        completion_message = AIMessage(
            content="🎯 **All topics completed!** Generating your learning session summary..."
        )
        
        return {
            "completed_topics": completed_topics,
            "current_topic_index": next_index,
            "workflow_stage": "session_summary",  # New stage for summary
            "messages": [completion_message],
            "topic_complete": False
        }
    
    # Move to next topic
    next_topic = state.learning_roadmap[next_index]
    progress_message = AIMessage(
        content=f"🎯 **Progress Update:**\n\n" +
               f"✅ Completed: {state.current_topic}\n" +
               f"📍 Next topic: **{next_topic}**\n" +
               f"📊 Progress: {next_index}/{len(state.learning_roadmap)} topics\n\n" +
               f"🚀 Starting research on {next_topic}..."
    )
    
    return {
        "completed_topics": completed_topics,
        "current_topic_index": next_index,
        "current_topic": next_topic,
        "topic_complete": False,
        "messages": [progress_message]
    } 