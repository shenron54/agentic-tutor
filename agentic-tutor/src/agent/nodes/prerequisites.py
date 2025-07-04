import asyncio
from typing import Any, Dict

from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig

from ..core.state import AgentState
from ..utils.clients import get_llm, get_search_client


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