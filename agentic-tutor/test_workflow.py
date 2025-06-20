#!/usr/bin/env python3
"""Test script for the agentic tutor LangGraph workflow."""

import asyncio
import os
from dotenv import load_dotenv
from src.agent.graph import graph_with_memory as graph, AgentState, Configuration

# Load environment variables
load_dotenv()

async def test_workflow():
    """Test the complete agentic tutor workflow."""
    
    # Check API keys
    print("🔑 Checking API Keys...")
    google_key = os.getenv("GOOGLE_API_KEY")
    tavily_key = os.getenv("TAVILY_API_KEY")
    
    if not google_key:
        print("❌ GOOGLE_API_KEY not found. Please set it in your .env file.")
        return
    if not tavily_key:
        print("❌ TAVILY_API_KEY not found. Please set it in your .env file.")
        return
    
    print("✅ API keys found!")
    
    # Test configuration with thread_id for memory
    config = {
        "configurable": {
            "thread_id": "test-conversation-1",
            "model_name": "gemini-2.0-flash-exp",
            "max_research_retries": 3,
            "temperature": 0.1
        }
    }
    
    # Initial state
    initial_state = AgentState(
        initial_topic="Convolutional Neural Networks"
    )
    
    print(f"\n🚀 Starting workflow for topic: {initial_state.initial_topic}")
    print("=" * 60)
    
    try:
        # Stream the workflow execution
        async for event in graph.astream(
            initial_state.model_dump(),
            config,  # config is the second positional argument
            stream_mode="updates"
        ):
            for node_name, node_output in event.items():
                print(f"\n📍 Node: {node_name}")
                
                # Print messages if any
                if "messages" in node_output:
                    for msg in node_output["messages"]:
                        print(f"💬 {msg.content[:200]}..." if len(msg.content) > 200 else f"💬 {msg.content}")
                
                # Print state updates
                if "workflow_stage" in node_output:
                    print(f"🔄 Stage: {node_output['workflow_stage']}")
                
                if "prerequisites" in node_output:
                    print(f"📋 Prerequisites found: {len(node_output['prerequisites'])}")
                
                if "learning_roadmap" in node_output:
                    print(f"🗺️ Roadmap created: {len(node_output['learning_roadmap'])} topics")
                
                print("-" * 40)
        
        print("\n✅ Workflow completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during workflow execution: {e}")
        import traceback
        traceback.print_exc()


async def test_with_checkpointing():
    """Test the workflow with checkpointing and state persistence."""
    
    print("\n🔄 Testing with checkpointing...")
    
    config = {
        "configurable": {
            "thread_id": "persistent-test-thread",
            "model_name": "gemini-2.0-flash-exp"
        }
    }
    
    initial_state = AgentState(
        initial_topic="Neural Networks"
    )
    
    try:
        # Run just the first few steps
        result = await graph.ainvoke(
            initial_state.model_dump(),
            config  # config is the second positional argument
        )
        
        print("✅ Checkpointing test completed!")
        print(f"📊 Final state workflow stage: {result.get('workflow_stage', 'unknown')}")
        
    except Exception as e:
        print(f"❌ Checkpointing test failed: {e}")


if __name__ == "__main__":
    print("🧪 Testing Agentic Tutor LangGraph Workflow")
    print("=" * 50)
    
    # Run the main workflow test
    asyncio.run(test_workflow())
    
    # Run checkpointing test
    asyncio.run(test_with_checkpointing()) 