import asyncio
from typing import Any, Dict

from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from langgraph.types import interrupt

from ..core.state import AgentState
from ..utils.clients import get_llm, get_search_client


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
                "last_qa_answer": answer_response.content,  # Track the answer for UI purposes
                "questions_asked": state.questions_asked + [{"question": user_question, "answer": answer_response.content}]
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
                "last_qa_answer": "",  # Clear Q&A state when moving on
                "questions_asked": state.questions_asked
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
            "last_qa_answer": "",  # Clear Q&A state when moving on
            "questions_asked": state.questions_asked
        }


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