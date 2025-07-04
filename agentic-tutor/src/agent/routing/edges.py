from typing import Literal

from ..core.state import AgentState


def route_from_start(state: AgentState) -> Literal["prerequisites"]:
    """Always route to prerequisites from start."""
    return "prerequisites"


def route_after_prerequisites(state: AgentState) -> Literal["human_selection"]:
    """Route to human selection after prerequisites discovery."""
    return "human_selection"


def route_after_human_selection(state: AgentState) -> Literal["roadmap"]:
    """Route to roadmap creation after human selection."""
    return "roadmap"


def route_learning_stage(state: AgentState) -> Literal["research", "complete"]:
    """Route within the learning stage."""
    if state.workflow_stage == "complete":
        return "complete"
    return "research"


def route_after_generation(state: AgentState) -> Literal["topic_review"]:
    """Always route to topic review after generation."""
    return "topic_review"


def route_after_topic_review(state: AgentState) -> Literal["progress_tracker", "research_agent", "topic_review"]:
    """Route after topic review based on user feedback."""
    if not state.current_lesson:  # Lesson was cleared for regeneration
        return "research_agent"
    elif state.topic_complete:  # User approved the lesson
        return "progress_tracker"
    else:  # Still waiting for approval (shouldn't happen in normal flow)
        return "topic_review"


def should_continue_overall_learning(state: AgentState) -> Literal["research", "session_summary", "end"]:
    """Determine if we should continue with next topic, go to summary, or end."""
    if state.workflow_stage == "session_summary":
        return "session_summary"
    if state.workflow_stage == "complete":
        return "end"
    if state.current_topic_index >= len(state.learning_roadmap):
        return "session_summary"  # Route to summary instead of end
    return "research"


def route_from_progress_tracker(state: AgentState) -> Literal["research", "session_summary"]:
    """Route from progress tracker to either next topic research or session summary."""
    if state.workflow_stage == "session_summary":
        return "session_summary"
    elif state.current_topic_index >= len(state.learning_roadmap):
        return "session_summary" 
    else:
        return "research" 