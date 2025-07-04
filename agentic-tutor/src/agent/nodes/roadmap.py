from typing import Any, Dict

from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig

from ..core.state import AgentState
from ..utils.clients import get_llm


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