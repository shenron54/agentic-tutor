from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage

class Configuration(BaseModel):
    """Configurable parameters for the agent."""
    
    model_name: str = Field(default="gemini-2.0-flash-exp", description="Google Gemini model to use")
    max_research_retries: int = Field(default=3, description="Maximum retries for research improvement")
    temperature: float = Field(default=0.1, description="LLM temperature for consistency")


class AgentState(BaseModel):
    """State for the agentic tutor workflow.
    
    This state tracks the entire learning journey from initial topic
    through prerequisites discovery, roadmap creation, and topic-by-topic learning.
    """
    
    # Core workflow data
    initial_topic: str = Field(default="", description="The main topic the user wants to learn")
    prerequisites: List[str] = Field(default_factory=list, description="All discovered prerequisites")
    known_prerequisites: List[str] = Field(default_factory=list, description="Prerequisites the user already knows")
    unknown_prerequisites: List[str] = Field(default_factory=list, description="Prerequisites the user doesn't know")
    learning_roadmap: List[str] = Field(default_factory=list, description="Ordered learning sequence")
    completed_topics: List[str] = Field(default_factory=list, description="Topics that have been learned")
    current_topic_index: int = Field(default=0, description="Current position in roadmap")
    
    # Conversation history - using LangGraph's message handling
    messages: List[BaseMessage] = Field(default_factory=list, description="Conversation history")
    
    # Current learning session data
    current_topic: str = Field(default="", description="Currently learning topic")
    current_research: str = Field(default="", description="Research content for current topic")
    current_lesson: str = Field(default="", description="Generated lesson content")
    topic_complete: bool = Field(default=False, description="Whether current topic is complete")
    
    # Human-in-the-loop interaction
    awaiting_user_input: bool = Field(default=False, description="Whether system is waiting for user input")
    user_selection: List[str] = Field(default_factory=list, description="User's prerequisite selections")
    
    # Q&A tracking
    last_qa_question: str = Field(default="", description="Last question asked by user")
    last_qa_answer: str = Field(default="", description="Last answer provided to user")
    questions_asked: List[Dict[str, str]] = Field(default_factory=list, description="A list of all questions asked and answers received during the session")
    
    # Session completion data
    session_completion_data: Dict[str, Any] = Field(default_factory=dict, description="Complete session summary data")
    
    # Loop control and error handling
    research_retry_count: int = Field(default=0, description="Number of research retries for current topic")
    workflow_stage: Literal["start", "prerequisites", "human_selection", "roadmap", "learning", "session_summary", "complete"] = Field(
        default="start", description="Current stage of the workflow"
    ) 