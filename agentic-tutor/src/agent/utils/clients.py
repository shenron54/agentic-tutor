import os
from langchain_core.runnables import RunnableConfig
from langchain_google_genai import ChatGoogleGenerativeAI
from tavily import TavilyClient

# Initialize the LLM
def get_llm(config: RunnableConfig) -> ChatGoogleGenerativeAI:
    """Get configured Google Gemini model."""
    configuration = config.get("configurable", {})
    model_name = configuration.get("model_name", "gemini-2.5-flash-lite")
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