#!/usr/bin/env python3
"""Demo script showing LangGraph memory and state persistence."""

import asyncio
import os
from dotenv import load_dotenv
from src.agent.graph import graph_with_memory as graph, AgentState

# Load environment variables
load_dotenv()

async def memory_demo():
    """Demonstrate memory and state persistence with thread_id."""
    
    print("🧠 LangGraph Memory Demo")
    print("=" * 40)
    
    # Session 1: Start a new conversation
    print("\n📍 Session 1: Starting new conversation")
    config1 = {"configurable": {"thread_id": "demo-session-1"}}
    
    initial_state = AgentState(initial_topic="Machine Learning Basics")
    
    # Run first part of workflow
    result1 = await graph.ainvoke(initial_state.model_dump(), config1)
    print(f"✅ Session 1 completed prerequisites stage")
    print(f"   Workflow stage: {result1.get('workflow_stage', 'unknown')}")
    
    # Inspect state
    snapshot1 = graph.get_state(config1)
    print(f"   Prerequisites found: {len(snapshot1.values.get('prerequisites', []))}")
    
    # Session 2: Different thread (fresh start)
    print("\n📍 Session 2: Different thread (fresh start)")
    config2 = {"configurable": {"thread_id": "demo-session-2"}}
    
    initial_state2 = AgentState(initial_topic="Deep Learning")
    result2 = await graph.ainvoke(initial_state2.model_dump(), config2)
    
    snapshot2 = graph.get_state(config2)
    print(f"✅ Session 2 has different state:")
    print(f"   Topic: {snapshot2.values.get('initial_topic', 'unknown')}")
    print(f"   Prerequisites: {len(snapshot2.values.get('prerequisites', []))}")
    
    # Session 1 continued: Resume original conversation
    print("\n📍 Session 1 continued: Resume with same thread_id")
    snapshot1_resumed = graph.get_state(config1)
    print(f"✅ Session 1 state preserved:")
    print(f"   Topic: {snapshot1_resumed.values.get('initial_topic', 'unknown')}")
    print(f"   Stage: {snapshot1_resumed.values.get('workflow_stage', 'unknown')}")
    print(f"   Prerequisites: {len(snapshot1_resumed.values.get('prerequisites', []))}")
    
    # Show that each thread maintains separate state
    print("\n🔍 State Comparison:")
    print(f"   Thread 1 topic: {snapshot1_resumed.values.get('initial_topic')}")
    print(f"   Thread 2 topic: {snapshot2.values.get('initial_topic')}")
    print(f"   Threads are independent: {snapshot1_resumed.values.get('initial_topic') != snapshot2.values.get('initial_topic')}")


async def state_inspection_demo():
    """Demonstrate state inspection capabilities."""
    
    print("\n\n🔍 State Inspection Demo")
    print("=" * 40)
    
    config = {"configurable": {"thread_id": "inspection-demo"}}
    initial_state = AgentState(initial_topic="Neural Networks")
    
    # Run workflow step by step
    print("\n📊 Running workflow and inspecting state...")
    
    async for i, event in enumerate(graph.astream(initial_state.model_dump(), config, stream_mode="updates")):
        for node_name, node_output in event.items():
            print(f"\n   Step {i+1}: {node_name}")
            
            # Get current state after this step
            current_snapshot = graph.get_state(config)
            stage = current_snapshot.values.get('workflow_stage', 'unknown')
            print(f"   Current stage: {stage}")
            
            if 'prerequisites' in node_output:
                prereqs = current_snapshot.values.get('prerequisites', [])
                print(f"   Prerequisites: {len(prereqs)} found")
            
            if 'learning_roadmap' in node_output:
                roadmap = current_snapshot.values.get('learning_roadmap', [])
                current_index = current_snapshot.values.get('current_topic_index', 0)
                print(f"   Roadmap: {len(roadmap)} topics, currently at index {current_index}")
    
    # Final state inspection
    final_snapshot = graph.get_state(config)
    print(f"\n✅ Final state:")
    print(f"   Stage: {final_snapshot.values.get('workflow_stage')}")
    print(f"   Messages: {len(final_snapshot.values.get('messages', []))}")
    print(f"   Next steps: {final_snapshot.next}")


if __name__ == "__main__":
    print("🚀 Testing LangGraph Memory & State Management")
    
    # Check API keys
    if not os.getenv("GOOGLE_API_KEY") or not os.getenv("TAVILY_API_KEY"):
        print("❌ Please set GOOGLE_API_KEY and TAVILY_API_KEY in your .env file")
        exit(1)
    
    # Run demos
    asyncio.run(memory_demo())
    asyncio.run(state_inspection_demo()) 