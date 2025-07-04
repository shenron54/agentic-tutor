from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver

from .core.state import AgentState, Configuration
from .nodes.prerequisites import prerequisites_agent_node
from .nodes.selection import human_selection_node
from .nodes.roadmap import roadmap_agent_node
from .nodes.learning import (
    research_agent_node,
    critique_agent_node,
    generation_agent_node_main,
    topic_review_node,
)
from .nodes.progress import progress_tracker_node
from .nodes.completion import session_summary_node, session_completion_node
from .routing.edges import (
    route_from_start,
    route_after_prerequisites,
    route_after_human_selection,
    route_learning_stage,
    route_after_generation,
    route_after_topic_review,
    route_from_progress_tracker,
)


def create_graph(with_checkpointer: bool = True):
    """Create the graph with proper conditional routing and individual learning nodes.
    
    Args:
        with_checkpointer: If True, adds MemorySaver checkpointer for local testing.
                          If False, compiles without checkpointer for LangGraph Studio.
    """
    graph_builder = (
        StateGraph(AgentState, config_schema=Configuration)
        
        # Main workflow nodes
        .add_node("prerequisites_agent", prerequisites_agent_node)
        .add_node("human_selection", human_selection_node)
        .add_node("roadmap_agent", roadmap_agent_node)
        
        # Individual learning nodes (moved from subgraph)
        .add_node("research_agent", research_agent_node)
        .add_node("critique_agent", critique_agent_node)
        .add_node("generation_agent_main", generation_agent_node_main)
        .add_node("topic_review", topic_review_node)  # Human-in-the-loop node
        .add_node("progress_tracker", progress_tracker_node)
        
        # Session completion node
        .add_node("session_summary", session_summary_node)  # New summary node
        
        # Entry point - always go to prerequisites first
        .add_conditional_edges(
            START,
            route_from_start,
            {"prerequisites": "prerequisites_agent"}
        )
        
        # Prerequisites -> Human Selection (always)
        .add_conditional_edges(
            "prerequisites_agent",
            route_after_prerequisites,
            {"human_selection": "human_selection"}
        )
        
        # Human Selection -> Roadmap (always)
        .add_conditional_edges(
            "human_selection",
            route_after_human_selection,
            {"roadmap": "roadmap_agent"}
        )
        
        # Roadmap -> Learning Stage
        .add_conditional_edges(
            "roadmap_agent",
            route_learning_stage,
            {
                "research": "research_agent",
            }
        )
        
        # Learning flow: Research -> Critique -> Generation -> Topic Review -> Progress Tracker
        .add_edge("research_agent", "critique_agent")
        .add_edge("critique_agent", "generation_agent_main")
        .add_conditional_edges(
            "generation_agent_main",
            route_after_generation,
            {"topic_review": "topic_review"}
        )
        .add_conditional_edges(
            "topic_review",
            route_after_topic_review,
            {
                "progress_tracker": "progress_tracker",
                "research_agent": "research_agent",  # For regeneration
                "topic_review": "topic_review"  # For continued Q&A
            }
        )
        
        # After progress tracking, continue, go to summary, or end
        .add_conditional_edges(
            "progress_tracker",
            route_from_progress_tracker,
            {
                "research": "research_agent",  # Next topic
                "session_summary": "session_summary"  # Session complete
            }
        )
        
        # Session summary creates interrupt, then routes to completion
        .add_edge("session_summary", "session_completion")
        
        # Session completion node for final cleanup
        .add_node("session_completion", session_completion_node)
        .add_edge("session_completion", END)
    )
    
    if with_checkpointer:
        # For local testing - include checkpointer
        memory = MemorySaver()
        return graph_builder.compile(checkpointer=memory)
    else:
        # For LangGraph Studio - no checkpointer (platform handles persistence)
        return graph_builder.compile()


# Default graph for LangGraph Studio (no checkpointer)
graph = create_graph(with_checkpointer=False)

# Graph with checkpointer for local testing
graph_with_memory = create_graph(with_checkpointer=True) 