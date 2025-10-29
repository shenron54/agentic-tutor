from typing import Any, Dict

from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from langgraph.types import interrupt

from ..core.state import AgentState
from ..utils.clients import get_llm


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
    
    # Extract questions asked during the session from the state
    questions_asked_from_state = state.questions_asked
    questions_count = len(questions_asked_from_state)
    questions_list_for_prompt = "; ".join([qa['question'] for qa in questions_asked_from_state]) if questions_asked_from_state else "No questions asked"
    
    # Create comprehensive summary prompt
    summary_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert learning advisor creating a comprehensive summary of a student's learning journey.

Your task is to create an engaging, insightful summary that:
1. Celebrates their learning achievement
2. Highlights key concepts and connections
3. Shows the learning progression and logic
4. Suggests meaningful next steps
5. Provides practical applications they can now understand

Be encouraging, specific, and educational. Adapt your language and examples to the subject matter being learned. Use the actual topics and information provided."""),
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
        questions_count=questions_count,
        questions_list=questions_list_for_prompt
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
        "questions_asked_count": questions_count,
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