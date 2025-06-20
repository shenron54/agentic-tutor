"""LangGraph agentic tutor workflow.

An intelligent tutoring system that helps students learn ML/AI topics through
personalized learning paths with prerequisites analysis and multi-agent teaching.
"""

from __future__ import annotations

import os
import asyncio
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command
from tavily import TavilyClient


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
    
    # Session completion data
    session_completion_data: Dict[str, Any] = Field(default_factory=dict, description="Complete session summary data")
    
    # Loop control and error handling
    research_retry_count: int = Field(default=0, description="Number of research retries for current topic")
    workflow_stage: Literal["start", "prerequisites", "human_selection", "roadmap", "learning", "session_summary", "complete"] = Field(
        default="start", description="Current stage of the workflow"
    )


# Initialize the LLM
def get_llm(config: RunnableConfig) -> ChatGoogleGenerativeAI:
    """Get configured Google Gemini model."""
    configuration = config.get("configurable", {})
    model_name = configuration.get("model_name", "gemini-2.0-flash-exp")
    temperature = configuration.get("temperature", 0.1)
    
    return ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=temperature
    )

# Initialize Tavily search client
def get_search_client() -> TavilyClient:
    """Get configured Tavily search client."""
    return TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


async def prerequisites_agent_node(state: AgentState, config: RunnableConfig) -> Dict[str, Any]:
    """Find all necessary prerequisites for the given topic.
    
    Uses web search to identify foundational concepts needed before
    learning the target topic.
    """
    print(f"🔍 Prerequisites Agent: Finding prerequisites for {state.initial_topic}")
    
    llm = get_llm(config)
    search_client = get_search_client()
    
    # Search for prerequisites information (async to avoid blocking)
    search_query = f"prerequisites for learning {state.initial_topic} machine learning AI"
    search_results = await asyncio.to_thread(search_client.search, search_query, max_results=3)
    
    # Create prompt for analyzing prerequisites
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert ML/AI educator with deep knowledge of learning sequences and dependencies.
        
        Your task is to identify the ESSENTIAL and SPECIFIC prerequisites for learning the given topic.
        Focus on:
        - Direct conceptual dependencies (what must be understood first)
        - Specific algorithms, techniques, or frameworks that are building blocks
        - Mathematical concepts that are actually used in the topic
        - Practical skills needed to implement or understand the topic
        
        AVOID generic topics like "statistics" or "programming" unless they are specifically relevant.
        BE SPECIFIC: Instead of "machine learning basics", say "supervised learning" or "gradient descent"
        
        Based on the search results and your expertise, identify 3-6 specific prerequisite topics.
        Return ONLY the prerequisite names, one per line, no explanations or bullets."""),
        ("human", "Topic to learn: {topic}\n\nSearch results:\n{search_results}")
    ])
    
    response = await llm.ainvoke(prompt.format_messages(topic=state.initial_topic, search_results=search_results))
    
    # Parse prerequisites from response
    prerequisites = [line.strip() for line in response.content.split('\n') if line.strip()]
    
    # Create message for user
    prereq_message = AIMessage(
        content=f"I found {len(prerequisites)} prerequisites for learning {state.initial_topic}:\n\n" + 
                "\n".join(f"• {prereq}" for prereq in prerequisites) +
                "\n\nPlease let me know which of these topics you're already familiar with, and I'll create a personalized learning roadmap for the ones you need to learn."
    )
    
    return {
        "prerequisites": prerequisites,
        "messages": [prereq_message],
        "workflow_stage": "human_selection",
        "awaiting_user_input": True
    }





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


async def roadmap_agent_node(state: AgentState, config: RunnableConfig) -> Dict[str, Any]:
    """Create a personalized learning roadmap.
    
    Takes unknown prerequisites and creates an ordered learning plan
    from the user's current knowledge to the target topic.
    """
    print(f"🗺️ Roadmap Agent: Creating learning roadmap")
    
    llm = get_llm(config)
    
    # Create roadmap from unknown prerequisites + main topic
    topics_to_learn = state.unknown_prerequisites + [state.initial_topic]
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert curriculum designer for ML/AI education.
        Your task is to create a logical, step-by-step learning roadmap.
        
        Given a list of topics the student needs to learn, arrange them in the optimal 
        learning order considering dependencies between topics. The last topic in the list
        is the main learning goal.
        
        Return your response as a simple ordered list, one topic per line, without numbering or bullets."""),
        ("human", "Create an optimal learning sequence for these topics:\n{topics}\n\n"
                 "The main goal is to learn the final topic in this list.")
    ])
    
    response = await llm.ainvoke(prompt.format_messages(topics='\n'.join(f"• {topic}" for topic in topics_to_learn)))
    
    # Parse roadmap from response
    roadmap = [line.strip() for line in response.content.split('\n') if line.strip()]
    
    roadmap_message = AIMessage(
        content=f"🎯 Your Personalized Learning Roadmap:\n\n" +
                "\n".join(f"{i+1}. {topic}" for i, topic in enumerate(roadmap)) +
                f"\n\n🚀 Let's start with the first topic: **{roadmap[0]}**"
    )
    
    return {
        "learning_roadmap": roadmap,
        "current_topic_index": 0,
        "current_topic": roadmap[0] if roadmap else "",
        "messages": [roadmap_message],
        "workflow_stage": "learning"
    }


# Research, Critique, and Generation nodes - moved from subgraph to main graph
async def research_agent_node(state: AgentState, config: RunnableConfig) -> Dict[str, Any]:
    """Research the current topic using web search tools."""
    current_topic = state.current_topic
    if not current_topic:
        return {"current_research": "No topic to research"}
    
    print(f"🔬 Research Agent: Researching {current_topic}")
    
    search_client = get_search_client()
    
    # Perform comprehensive search
    search_query = f"{current_topic} tutorial explanation machine learning AI"
    search_results = await asyncio.to_thread(search_client.search, search_query, max_results=5)
    
    # Compile research
    research_content = f"Research for: {current_topic}\n\n"
    for i, result in enumerate(search_results.get("results", []), 1):
        research_content += f"Source {i}: {result.get('title', 'No title')}\n"
        research_content += f"URL: {result.get('url', 'No URL')}\n"
        research_content += f"Content: {result.get('content', 'No content')[:300]}...\n\n"
    
    research_message = AIMessage(
        content=f"🔍 Completed research on {current_topic}. Found {len(search_results.get('results', []))} relevant sources."
    )
    
    return {
        "current_research": research_content,
        "research_retry_count": 0,
        "messages": [research_message]
    }


async def critique_agent_node(state: AgentState, config: RunnableConfig) -> Dict[str, Any]:
    """Evaluate the quality and completeness of research."""
    print(f"🧐 Critique Agent: Reviewing research quality for {state.current_topic}")
    
    llm = get_llm(config)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert content reviewer for educational materials.
        Your task is to evaluate research content for teaching purposes.
        
        Assess if the research content is:
        1. Accurate and factual
        2. Comprehensive enough for learning
        3. Well-structured and clear
        4. Relevant to the topic
        
        Respond with either 'APPROVED' if the content is good enough, or 'NEEDS_IMPROVEMENT' 
        followed by specific feedback on what needs to be better."""),
        ("human", "Please review this research content:\n\n{research_content}")
    ])
    
    response = await llm.ainvoke(prompt.format_messages(research_content=state.current_research))
    
    critique_message = AIMessage(
        content=f"📋 Research review completed for {state.current_topic}. Quality assessment: {'Approved' if 'APPROVED' in response.content.upper() else 'Needs refinement'}"
    )
    
    # For now, we'll approve after one review to avoid infinite loops
    approved_research = state.current_research + f"\n\n[REVIEW FEEDBACK: {response.content}]"
    
    return {
        "current_research": approved_research,
        "messages": [critique_message]
    }


async def generation_agent_node_main(state: AgentState, config: RunnableConfig) -> Dict[str, Any]:
    """Generate educational content from approved research."""
    current_topic = state.current_topic
    print(f"📚 Generation Agent: Creating lesson for {current_topic}")
    
    llm = get_llm(config)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert educator specializing in ML/AI topics.
        Your task is to create clear, engaging educational content from research material.
        
        Structure your lesson with:
        1. Brief introduction to the topic
        2. Key concepts explained simply
        3. Practical examples where relevant
        4. Summary of main points
        5. Connection to next learning steps
        
        Make the content accessible and engaging for students."""),
        ("human", "Create a comprehensive lesson on: {topic}\n\n"
                 "Based on this research:\n{research}")
    ])
    
    response = await llm.ainvoke(prompt.format_messages(topic=current_topic, research=state.current_research))
    
    # Create a full lesson message with proper formatting
    lesson_content = f"# 📖 Lesson: {current_topic}\n\n{response.content}\n\n✅ Topic completed! Ready for your review."
    
    # Create lesson message for display
    lesson_message = AIMessage(content=lesson_content)
    
    return {
        "current_lesson": lesson_content,
        "messages": [lesson_message],
        "awaiting_user_input": True,  # Set flag to indicate we're waiting for review
        "topic_complete": False  # Don't mark as complete until reviewed
    }


async def topic_review_node(state: AgentState, config: RunnableConfig) -> Dict[str, Any]:
    """Human-in-the-loop topic review after lesson generation.
    
    This node uses interrupt to pause execution and wait for user feedback
    on the lesson before proceeding to the next topic.
    """
    current_topic = state.current_topic
    print(f"👤 Topic Review: Waiting for user feedback on {current_topic}")
    
    # Use interrupt to pause and wait for user feedback
    user_feedback = interrupt({
        "type": "topic_review",
        "topic": current_topic,
        "lesson_content": state.current_lesson,
        "message": f"Please review the lesson on '{current_topic}'. Do you understand the concepts and are ready to continue?",
        "options": [
            {"value": "continue", "label": "✅ I understand, continue to next topic"},
            {"value": "ask_question", "label": "❓ I have questions about this topic"},
            {"value": "regenerate", "label": "🔄 Please explain this topic differently"}
        ],
        "instructions": "Choose an option or ask specific questions about the topic"
    })
    
    # Process user feedback
    if isinstance(user_feedback, dict):
        feedback_type = user_feedback.get("action", "continue")
        user_question = user_feedback.get("question", "")
        
        if feedback_type == "ask_question" and user_question:
            # User has a question - answer it and stay in review mode
            llm = get_llm(config)
            
            qa_prompt = ChatPromptTemplate.from_messages([
                ("system", f"""You are an expert tutor answering student questions about {current_topic}.
                
                Provide clear, helpful answers based on the lesson content. 
                If the question requires additional examples or clarification, provide them.
                Keep your answer focused and educational."""),
                ("human", f"Student question about {current_topic}: {user_question}\n\n"
                         f"Lesson context:\n{state.current_lesson}")
            ])
            
            answer_response = await llm.ainvoke(qa_prompt.format_messages())
            
            qa_message = AIMessage(
                content=f"📖 **Q&A about {current_topic}:**\n\n**Question:** {user_question}\n\n**Answer:** {answer_response.content}\n\n---\n\n*Please review the lesson and answer above. Choose an option below to continue.*"
            )
            
            return {
                "messages": [qa_message],
                "awaiting_user_input": True,  # Still waiting for final approval
                "topic_complete": False,
                "last_qa_question": user_question,  # Track the question for UI purposes
                "last_qa_answer": answer_response.content  # Track the answer for UI purposes
            }
        
        elif feedback_type == "regenerate":
            # User wants the lesson regenerated - trigger regeneration
            regenerate_message = AIMessage(
                content=f"🔄 I'll regenerate the lesson on {current_topic} with a different approach."
            )
            
            return {
                "messages": [regenerate_message],
                "awaiting_user_input": False,
                "topic_complete": False,
                "current_lesson": ""  # Clear current lesson to trigger regeneration
            }
        
        else:  # continue or default
            # User is satisfied - mark topic as complete
            approval_message = AIMessage(
                content=f"✅ Great! You've completed learning **{current_topic}**. Let's move to the next topic!"
            )
            
            return {
                "messages": [approval_message],
                "awaiting_user_input": False,
                "topic_complete": True,
                "last_qa_question": "",  # Clear Q&A state when moving on
                "last_qa_answer": ""  # Clear Q&A state when moving on
            }
    
    else:
        # Fallback - treat any other response as approval to continue
        approval_message = AIMessage(
            content=f"✅ Moving on from **{current_topic}** to the next topic!"
        )
        
        return {
            "messages": [approval_message],
            "awaiting_user_input": False,
            "topic_complete": True,
            "last_qa_question": "",  # Clear Q&A state when moving on
            "last_qa_answer": ""  # Clear Q&A state when moving on
        }


# Simple generation agent for Q&A sessions
async def generation_agent_node(state: AgentState, config: RunnableConfig) -> Dict[str, Any]:
    """Simple generation agent for Q&A sessions."""
    llm = get_llm(config)
    
    if state.messages:
        latest_message = state.messages[-1]
        if hasattr(latest_message, 'content'):
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an expert tutor answering student questions.
                Provide clear, helpful answers based on the topics they've been learning."""),
                ("human", "{question}")
            ])
            
            response = await llm.ainvoke(prompt.format_messages(question=latest_message.content))
            
            return {
                "messages": [AIMessage(content=response.content)]
            }
    
    return {"messages": []}


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


async def session_summary_node(state: AgentState, config: RunnableConfig) -> Dict[str, Any]:
    """Generate a comprehensive learning session summary.
    
    This node creates an intelligent summary of the entire learning journey,
    including insights, connections, and next steps recommendations.
    """
    print(f"📊 Session Summary: Generating comprehensive learning summary")
    
    llm = get_llm(config)
    
    # Gather all session information
    initial_topic = state.initial_topic
    prerequisites = state.prerequisites
    known_prerequisites = state.known_prerequisites
    unknown_prerequisites = state.unknown_prerequisites
    learning_roadmap = state.learning_roadmap
    completed_topics = state.completed_topics
    
    # Calculate session statistics
    total_topics = len(learning_roadmap)
    total_prerequisites_found = len(prerequisites)
    topics_learned = len(completed_topics)
    
    # Extract questions asked during the session
    questions_asked = []
    if state.messages:
        for msg in state.messages:
            if hasattr(msg, 'content') and "Q&A about" in str(msg.content):
                # Extract question from Q&A format
                content = str(msg.content)
                if "**Question:**" in content:
                    question_start = content.find("**Question:**") + len("**Question:**")
                    question_end = content.find("**Answer:**")
                    if question_end > question_start:
                        question = content[question_start:question_end].strip()
                        questions_asked.append(question)
    
    # Create comprehensive summary prompt
    summary_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert learning advisor creating a comprehensive summary of a student's AI/ML learning journey.

Your task is to create an engaging, insightful summary that:
1. Celebrates their learning achievement
2. Highlights key concepts and connections
3. Shows the learning progression and logic
4. Suggests meaningful next steps
5. Provides practical applications they can now understand

Be encouraging, specific, and educational. Use the actual topics and information provided."""),
        ("human", """Create a comprehensive learning session summary for this student:

LEARNING GOAL:
- Original topic requested: {initial_topic}

LEARNING JOURNEY:
- Prerequisites discovered: {total_prerequisites} topics
- Already knew: {known_topics}
- Learned during session: {learned_topics}
- Complete learning roadmap: {roadmap}

SESSION STATISTICS:
- Total topics completed: {topics_completed}/{total_topics}
- Questions asked: {questions_count}
- Student questions: {questions_list}

Please create a summary with these sections:
1. **🎉 Congratulations & Achievement**
2. **📚 Your Learning Journey** (show progression and connections)
3. **🎯 Key Concepts Mastered** (specific takeaways from each topic)
4. **🔗 How Everything Connects** (how prerequisites led to main goal)
5. **💡 Practical Applications** (what you can now understand/do)
6. **🚀 Recommended Next Steps** (3-4 specific advanced topics or projects)
7. **📊 Session Summary** (stats and achievements)

Make it personal, encouraging, and specific to their actual learning path."""),
    ])
    
    # Generate the summary
    response = await llm.ainvoke(summary_prompt.format_messages(
        initial_topic=initial_topic,
        total_prerequisites=total_prerequisites_found,
        known_topics=", ".join(known_prerequisites) if known_prerequisites else "None",
        learned_topics=", ".join(unknown_prerequisites) if unknown_prerequisites else "None", 
        roadmap=" → ".join(learning_roadmap),
        topics_completed=topics_learned,
        total_topics=total_topics,
        questions_count=len(questions_asked),
        questions_list="; ".join(questions_asked) if questions_asked else "No questions asked"
    ))
    
    # Create the final summary message
    summary_content = f"""# 🎓 Learning Session Complete!

{response.content}

---

*Thank you for using the Agentic Tutor! Your learning journey has been saved and you can start a new topic anytime.*"""
    
    summary_message = AIMessage(content=summary_content)
    
    # Create session completion data for the UI
    session_completion_data = {
        "session_complete": True,
        "summary_generated": True,
        "initial_topic": initial_topic,
        "total_topics_learned": topics_learned,
        "total_topics_planned": total_topics,
        "learning_roadmap": learning_roadmap,
        "completed_topics": completed_topics,
        "prerequisites_known": known_prerequisites,
        "prerequisites_learned": unknown_prerequisites,
        "questions_asked_count": len(questions_asked),
        "session_summary": response.content
    }
    
    # Create an interrupt to display the session summary
    interrupt(
        {
            "type": "session_summary_display",
            "session_completion_data": session_completion_data,
            "summary_content": summary_content,
            "summary_message": response.content
        }
    )
    
    return {
        "messages": [summary_message],
        "workflow_stage": "complete",
        "session_completion_data": session_completion_data,
        "current_lesson": summary_content,  # For display purposes
        "topic_complete": True,
        "awaiting_user_input": True  # Indicate we're waiting for user to dismiss summary
    }


async def session_completion_node(state: AgentState, config: RunnableConfig) -> Dict[str, Any]:
    """Final session completion node - handles user acknowledgment of summary."""
    print("🎯 Session Completion: Finalizing learning session")
    
    # Wait for user to acknowledge the session summary
    user_response = interrupt({
        "type": "session_completion_acknowledgment",
        "message": "Thank you for completing your learning journey! Click 'Start New Topic' to begin a new session.",
        "session_completion_data": state.session_completion_data
    })
    
    # Create final completion message
    completion_message = AIMessage(
        content="🎓 Learning session successfully completed! Thank you for using the Agentic Tutor."
    )
    
    return {
        "messages": [completion_message],
        "workflow_stage": "complete",
        "awaiting_user_input": False,
        "topic_complete": True
    }


# Routing Functions oe edges
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


# Create the sophisticated graph structure
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
                "complete": END
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


# Utility Functions for External Applications
class TutorWorkflowRunner:
    """Main interface for running the agentic tutor workflow from external applications."""
    
    def __init__(self, use_checkpointer: bool = True):
        """Initialize the workflow runner.
        
        Args:
            use_checkpointer: Whether to use memory checkpointing for interrupt support
        """
        self.graph = create_graph(with_checkpointer=use_checkpointer)
        self.current_config = None
    
    def create_session(self, session_id: str = None) -> Dict[str, Any]:
        """Create a new tutoring session.
        
        Args:
            session_id: Optional session identifier. If None, generates a UUID.
            
        Returns:
            Configuration dictionary for the session
        """
        if session_id is None:
            import uuid
            session_id = str(uuid.uuid4())
        
        self.current_config = {"configurable": {"thread_id": session_id}}
        return self.current_config
    
    async def start_learning_session(self, topic: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Start a new learning session for a given topic.
        
        Args:
            topic: The topic to learn
            config: Session configuration (uses current_config if None)
            
        Returns:
            Dictionary with session results and any interrupt information
        """
        if config is None:
            config = self.current_config
        if config is None:
            config = self.create_session()
        
        initial_state = {
            "initial_topic": topic,
            "messages": [HumanMessage(content=f"I want to learn about {topic}")],
            "workflow_stage": "start"
        }
        
        try:
            # Run until interrupt or completion
            result = await self.graph.ainvoke(initial_state, config)
            
            # Check for interrupts
            current_state = self.graph.get_state(config)
            interrupt_info = self._extract_interrupt_info(current_state)
            
            return {
                "success": True,
                "state": current_state.values if current_state else {},
                "interrupt": interrupt_info,
                "config": config
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "config": config
            }
    
    async def resume_with_response(self, user_response: Any, config: Dict[str, Any]) -> Dict[str, Any]:
        """Resume workflow execution with user response.
        
        Args:
            user_response: User's response to the interrupt
            config: Session configuration
            
        Returns:
            Dictionary with updated session results and any new interrupt information
        """
        try:
            # Resume with user response
            result = await self.graph.ainvoke(Command(resume=user_response), config)
            
            # Check if workflow completed - if so, use the result directly
            current_state = self.graph.get_state(config)
            
            # If state is not available (workflow ended), use the result
            if not current_state or not current_state.values:
                # Workflow has completed - use the final result
                return {
                    "success": True,
                    "state": result if result else {},
                    "interrupt": None,  # No interrupts when workflow ends
                    "config": config,
                    "workflow_completed": True
                }
            
            # Workflow is still active - check for interrupts
            interrupt_info = self._extract_interrupt_info(current_state)
            
            return {
                "success": True,
                "state": current_state.values,
                "interrupt": interrupt_info,
                "config": config,
                "workflow_completed": False
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "config": config
            }
    
    async def stream_workflow_updates(self, initial_state_or_command, config: Dict[str, Any]):
        """Stream workflow updates for real-time UI updates.
        
        Args:
            initial_state_or_command: Initial state dict or Command for resuming
            config: Session configuration
            
        Yields:
            Dictionaries with node updates and workflow information
        """
        try:
            async for chunk in self.graph.astream(initial_state_or_command, config, stream_mode="updates"):
                for node_name, node_output in chunk.items():
                    yield {
                        "node_name": node_name,
                        "node_output": node_output,
                        "timestamp": asyncio.get_event_loop().time()
                    }
        except Exception as e:
            yield {
                "error": str(e),
                "timestamp": asyncio.get_event_loop().time()
            }
    
    def get_session_state(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Get current session state.
        
        Args:
            config: Session configuration
            
        Returns:
            Current state values and metadata
        """
        try:
            current_state = self.graph.get_state(config)
            interrupt_info = self._extract_interrupt_info(current_state)
            
            return {
                "success": True,
                "state": current_state.values if current_state else {},
                "interrupt": interrupt_info,
                "metadata": current_state.metadata if current_state else {}
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _extract_interrupt_info(self, state) -> Dict[str, Any] or None:
        """Extract interrupt information from the graph state.
        
        Args:
            state: LangGraph state object
            
        Returns:
            Interrupt information dictionary or None
        """
        if not state or not state.tasks:
            return None
        
        for task in state.tasks:
            if task.interrupts:
                interrupt = task.interrupts[0]
                return {
                    "type": interrupt.value.get("type") if interrupt.value else "unknown",
                    "data": interrupt.value,
                    "resumable": getattr(interrupt, 'resumable', True)
                }
        
        return None


# Interrupt Processing Utilities
class InterruptHandler:
    """Utility class for processing different types of interrupts."""
    
    @staticmethod
    def process_prerequisite_selection(interrupt_data: Dict[str, Any], user_selections: List[str]) -> Dict[str, Any]:
        """Process prerequisite selection interrupt.
        
        Args:
            interrupt_data: The interrupt data from the graph
            user_selections: List of prerequisites the user already knows
            
        Returns:
            Command data for resuming the workflow
        """
        prerequisites = interrupt_data.get("prerequisites", [])
        
        # Validate selections
        known_prereqs = [p for p in user_selections if p in prerequisites]
        
        return {"known_prerequisites": known_prereqs}
    
    @staticmethod
    def process_topic_review(interrupt_data: Dict[str, Any], action: str, question: str = None) -> Dict[str, Any]:
        """Process topic review interrupt.
        
        Args:
            interrupt_data: The interrupt data from the graph
            action: User's chosen action ("continue", "ask_question", "regenerate")
            question: User's question (if action is "ask_question")
            
        Returns:
            Command data for resuming the workflow
        """
        result = {"action": action}
        
        if action == "ask_question" and question:
            result["question"] = question
        
        return result
    
    @staticmethod
    def process_session_summary_display(interrupt_data: Dict[str, Any], action: str) -> Dict[str, Any]:
        """Process session summary display interrupt.
        
        Args:
            interrupt_data: The interrupt data from the graph
            action: User's chosen action (usually "acknowledge_summary")
            
        Returns:
            Command data for resuming the workflow
        """
        return {"action": action}


# Progress Tracking Utilities
class ProgressTracker:
    """Utility for tracking learning progress."""
    
    @staticmethod
    def calculate_progress(state: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate learning progress from state.
        
        Args:
            state: Current workflow state
            
        Returns:
            Progress information dictionary
        """
        # Handle None or empty state
        if not state or not isinstance(state, dict):
            return {
                "total_topics": 0,
                "completed_count": 0,
                "current_topic": "",
                "progress_percentage": 0,
                "remaining_topics": [],
                "learning_roadmap": []
            }
        
        # Safely extract values with defaults
        learning_roadmap = state.get("learning_roadmap", [])
        completed_topics = state.get("completed_topics", [])
        current_topic_index = state.get("current_topic_index", 0)
        current_topic = state.get("current_topic", "")
        
        # Ensure we have valid lists
        if not isinstance(learning_roadmap, list):
            learning_roadmap = []
        if not isinstance(completed_topics, list):
            completed_topics = []
        
        # Calculate metrics
        total_topics = len(learning_roadmap)
        completed_count = len(completed_topics)
        progress_percentage = (completed_count / total_topics) * 100 if total_topics > 0 else 0
        
        # Calculate remaining topics safely
        remaining_topics = []
        if learning_roadmap and isinstance(current_topic_index, int):
            if current_topic_index < len(learning_roadmap) - 1:
                remaining_topics = learning_roadmap[current_topic_index + 1:]
        
        return {
            "total_topics": total_topics,
            "completed_count": completed_count,
            "current_topic": current_topic,
            "progress_percentage": progress_percentage,
            "remaining_topics": remaining_topics,
            "learning_roadmap": learning_roadmap
        }
