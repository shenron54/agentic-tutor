#!/usr/bin/env python3
"""
Streamlit App for Agentic Tutor
A beautiful UI for the LangGraph-based intelligent tutoring system
"""

import streamlit as st
import asyncio
import sys
import os
from typing import Dict, Any, List
import time
import uuid
from datetime import datetime

# Add the agentic-tutor src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agentic-tutor', 'src'))

try:
    from agent.runner import TutorWorkflowRunner
    from agent.utils.handlers import InterruptHandler
    from agent.utils.tracker import ProgressTracker
    from langchain_core.messages import HumanMessage, AIMessage
    IMPORTS_SUCCESSFUL = True
except ImportError as e:
    st.error(f"❌ Cannot import required modules from the new structure: {str(e)}")
    st.error("Please ensure the agentic-tutor package's refactored structure is correct.")
    st.info("Expected modules: `agent/runner.py`, `agent/utils/handlers.py`, `agent/utils/tracker.py`")
    
    # Show debug info
    with st.expander("🔧 Debug Information"):
        current_dir = os.path.dirname(__file__)
        runner_path = os.path.join(current_dir, 'agentic-tutor', 'src', 'agent', 'runner.py')
        handlers_path = os.path.join(current_dir, 'agentic-tutor', 'src', 'agent', 'utils', 'handlers.py')
        tracker_path = os.path.join(current_dir, 'agentic-tutor', 'src', 'agent', 'utils', 'tracker.py')
        st.json({
            "current_directory": current_dir,
            "runner_path": runner_path,
            "runner_path_exists": os.path.exists(runner_path),
            "handlers_path": handlers_path,
            "handlers_path_exists": os.path.exists(handlers_path),
            "tracker_path": tracker_path,
            "tracker_path_exists": os.path.exists(tracker_path),
            "python_path": sys.path[:3],  # Show first 3 paths
            "import_error": str(e)
        })
    
    IMPORTS_SUCCESSFUL = False

# Page Configuration
st.set_page_config(
    page_title="🎓 Agentic Tutor",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .topic-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        margin: 1rem 0;
    }
    .lesson-container {
        background: #f8f9fa;
        padding: 2rem;
        border-radius: 15px;
        border-left: 5px solid #1f77b4;
        margin: 1rem 0;
    }
    .progress-container {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
    .prerequisite-item {
        background: linear-gradient(135deg, #2196f3 0%, #1976d2 100%);
        padding: 0.8rem 1.2rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 4px solid #0d47a1;
        color: white;
        font-weight: 500;
        box-shadow: 0 2px 8px rgba(33, 150, 243, 0.3);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .prerequisite-item:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(33, 150, 243, 0.4);
    }
    .qa-container {
        background: #f1f8e9;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #4caf50;
        margin: 1rem 0;
    }
    
    /* Streamlit checkbox styling improvements */
    .stCheckbox > label {
        color: white !important;
        font-weight: 600 !important;
    }
    
    /* Custom button styling for better visibility */
    .stButton > button {
        background: linear-gradient(135deg, #1976d2 0%, #0d47a1 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #1565c0 0%, #0a3d91 100%) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(25, 118, 210, 0.4) !important;
    }
    
    /* Primary button (Continue with Learning Plan) special styling */
    div[data-testid="column"]:nth-child(2) .stButton > button {
        background: linear-gradient(135deg, #4caf50 0%, #2e7d32 100%) !important;
        color: white !important;
        font-size: 1.1rem !important;
        padding: 0.6rem 2rem !important;
        font-weight: 700 !important;
    }
    
    div[data-testid="column"]:nth-child(2) .stButton > button:hover {
        background: linear-gradient(135deg, #43a047 0%, #1b5e20 100%) !important;
        box-shadow: 0 6px 16px rgba(76, 175, 80, 0.4) !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state with better error handling
def initialize_session_state():
    """Initialize session state with proper error handling"""
    if not IMPORTS_SUCCESSFUL:
        return False
    
    try:
        if "workflow_runner" not in st.session_state:
            st.session_state.workflow_runner = TutorWorkflowRunner(use_checkpointer=True)
        
        if "session_config" not in st.session_state:
            st.session_state.session_config = None
        
        if "current_state" not in st.session_state:
            st.session_state.current_state = {}
        
        if "learning_history" not in st.session_state:
            st.session_state.learning_history = []
        
        if "current_interrupt" not in st.session_state:
            st.session_state.current_interrupt = None
        
        if "workflow_active" not in st.session_state:
            st.session_state.workflow_active = False
            
        return True
        
    except Exception as e:
        st.error(f"❌ Error initializing workflow runner: {str(e)}")
        
        with st.expander("🔧 Debug Information"):
            st.json({
                "error": str(e),
                "imports_successful": IMPORTS_SUCCESSFUL,
                "session_state_keys": list(st.session_state.keys())
            })
        
        return False

# Helper Functions
def setup_api_keys():
    """Setup API keys - use environment variables if available, otherwise show sidebar"""
    # First check if API keys are already available in environment (e.g., from Streamlit Cloud secrets)
    google_key_env = os.getenv("GOOGLE_API_KEY")
    tavily_key_env = os.getenv("TAVILY_API_KEY")
    
    # If both keys are available in environment, use them directly
    if google_key_env and tavily_key_env:
        # Show a small success indicator in sidebar but don't ask for keys
        with st.sidebar:
            st.success("🔑 API keys configured from environment")
        return True
    
    # If keys are not in environment, show the configuration sidebar
    with st.sidebar:
        st.header("🔧 Configuration")
        st.info("💡 Configure your API keys to start learning")
        
        google_key = st.text_input(
            "Google API Key", 
            type="password",
            help="Required for Google Gemini LLM"
        )
        
        tavily_key = st.text_input(
            "Tavily API Key", 
            type="password",
            help="Required for web search functionality"
        )
        
        if google_key:
            os.environ["GOOGLE_API_KEY"] = google_key
        
        if tavily_key:
            os.environ["TAVILY_API_KEY"] = tavily_key
        
        # Check if keys are set (either from input or environment)
        keys_configured = bool(
            (google_key or google_key_env) and 
            (tavily_key or tavily_key_env)
        )
        
        if keys_configured:
            st.success("✅ API keys configured")
        else:
            st.warning("⚠️ Please configure API keys to use the tutor")
        
        return keys_configured

def display_progress(state: Dict[str, Any]):
    """Display learning progress"""
    # Handle empty state gracefully
    if not state:
        st.info("🔄 Initializing learning session...")
        return
    
    try:
        progress_info = ProgressTracker.calculate_progress(state)
    except Exception as e:
        st.error(f"❌ Error calculating progress: {str(e)}")
        st.json({"state_keys": list(state.keys()), "error": str(e)})
        return
    
    with st.container():
        st.markdown('<div class="progress-container">', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "📚 Total Topics", 
                progress_info.get("total_topics", 0)
            )
        
        with col2:
            st.metric(
                "✅ Completed", 
                progress_info.get("completed_count", 0)
            )
        
        with col3:
            st.metric(
                "📊 Progress", 
                f"{progress_info.get('progress_percentage', 0):.1f}%"
            )
        
        # Progress bar
        total_topics = progress_info.get("total_topics", 0)
        if total_topics > 0:
            st.progress(progress_info.get("progress_percentage", 0) / 100)
        else:
            st.info("📋 Learning roadmap will appear after prerequisite selection")
        
        # Current topic
        current_topic = progress_info.get("current_topic", "")
        if current_topic:
            st.info(f"🎯 **Current Topic:** {current_topic}")
        
        # Learning roadmap
        learning_roadmap = progress_info.get("learning_roadmap", [])
        if learning_roadmap:
            st.subheader("🗺️ Learning Roadmap")
            completed_count = progress_info.get("completed_count", 0)
            
            for i, topic in enumerate(learning_roadmap):
                if i < completed_count:
                    st.markdown(f"✅ ~~{topic}~~")
                elif i == completed_count:
                    st.markdown(f"🎯 **{topic}** (Current)")
                else:
                    st.markdown(f"⏳ {topic}")
        else:
            # Show workflow stage info instead
            workflow_stage = state.get("workflow_stage", "unknown")
            if workflow_stage == "prerequisites":
                st.info("🔍 Discovering prerequisites for your topic...")
            elif workflow_stage == "human_selection":
                st.info("🤔 Waiting for prerequisite selection...")
            elif workflow_stage == "roadmap":
                st.info("🗺️ Creating personalized learning roadmap...")
            elif workflow_stage == "learning":
                st.info("📚 Learning in progress...")
        
        st.markdown('</div>', unsafe_allow_html=True)

def display_lesson(lesson_content: str, topic: str):
    """Display lesson content beautifully"""
    st.markdown('<div class="lesson-container">', unsafe_allow_html=True)
    st.markdown(f"## 📖 Lesson: {topic}")
    
    # Parse and display lesson content
    if lesson_content.startswith("# 📖 Lesson:"):
        # Remove the markdown title since we're adding our own
        content_lines = lesson_content.split('\n')
        content_without_title = '\n'.join(content_lines[1:]) if len(content_lines) > 1 else lesson_content
        st.markdown(content_without_title)
    else:
        st.markdown(lesson_content)
    
    st.markdown('</div>', unsafe_allow_html=True)

def handle_prerequisite_selection(interrupt_data: Dict[str, Any]):
    """Handle prerequisite selection interrupt"""
    st.subheader("🤔 Prerequisite Knowledge Assessment")
    st.info("Please select the topics you're already familiar with:")
    
    prerequisites = interrupt_data.get("prerequisites", [])
    
    if prerequisites:
        st.markdown("**Found Prerequisites:**")
        
        # Create checkboxes for each prerequisite
        selected_prereqs = []
        
        for prereq in prerequisites:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f'<div class="prerequisite-item">{prereq}</div>', unsafe_allow_html=True)
            with col2:
                if st.checkbox("Know this", key=f"prereq_{prereq}"):
                    selected_prereqs.append(prereq)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("📚 Continue with Learning Plan", type="primary", use_container_width=True):
                # Process the selection
                response = InterruptHandler.process_prerequisite_selection(interrupt_data, selected_prereqs)
                return response
    
    return None

def handle_topic_review(interrupt_data: Dict[str, Any]):
    """Handle topic review interrupt"""
    topic = interrupt_data.get("topic", "Unknown Topic")
    lesson_content = interrupt_data.get("lesson_content", "")
    
    st.subheader(f"🤔 Topic Review: {topic}")
    st.info("Please review the lesson above. What would you like to do?")
    
    # Display options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("✅ Continue to Next Topic", type="primary", use_container_width=True):
            return InterruptHandler.process_topic_review(interrupt_data, "continue")
    
    with col2:
        if st.button("🔄 Regenerate Lesson", use_container_width=True):
            return InterruptHandler.process_topic_review(interrupt_data, "regenerate")
    
    with col3:
        if st.button("❓ Ask Question", use_container_width=True):
            st.session_state.show_qa_input = True
    
    # Q&A input (appears when user clicks "Ask Question")
    if st.session_state.get("show_qa_input", False):
        st.markdown('<div class="qa-container">', unsafe_allow_html=True)
        st.subheader("❓ Ask Your Question")
        
        question = st.text_area(
            "What would you like to know about this topic?",
            height=100,
            key="topic_question"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Send Question", type="primary"):
                if question.strip():
                    st.session_state.show_qa_input = False
                    return InterruptHandler.process_topic_review(interrupt_data, "ask_question", question)
                else:
                    st.error("Please enter a question")
        
        with col2:
            if st.button("Cancel"):
                st.session_state.show_qa_input = False
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    return None

async def start_learning_session(topic: str):
    """Start a new learning session"""
    try:
        st.session_state.session_config = st.session_state.workflow_runner.create_session()
        st.session_state.workflow_active = True
        
        with st.spinner("🚀 Starting your learning journey..."):
            result = await st.session_state.workflow_runner.start_learning_session(
                topic, 
                st.session_state.session_config
            )
        
        if result["success"]:
            st.session_state.current_state = result.get("state", {})
            st.session_state.current_interrupt = result.get("interrupt")
            
            # Add to learning history
            st.session_state.learning_history.append({
                "timestamp": datetime.now(),
                "topic": topic,
                "action": "started"
            })
            
            st.success(f"✅ Started learning session for: **{topic}**")
            return True
        else:
            error_msg = result.get('error', 'Unknown error')
            st.error(f"❌ Error starting session: {error_msg}")
            st.session_state.workflow_active = False
            return False
            
    except Exception as e:
        st.error(f"❌ Unexpected error starting session: {str(e)}")
        st.session_state.workflow_active = False
        
        # Show debug info
        with st.expander("🔧 Debug Information"):
            st.json({
                "error": str(e),
                "topic": topic,
                "session_config": st.session_state.get("session_config"),
                "workflow_runner_exists": "workflow_runner" in st.session_state
            })
        return False

async def resume_workflow(user_response):
    """Resume workflow with user response"""
    try:
        with st.spinner("🔄 Processing your response..."):
            result = await st.session_state.workflow_runner.resume_with_response(
                user_response,
                st.session_state.session_config
            )
        
        if result["success"]:
            st.session_state.current_state = result.get("state", {})
            st.session_state.current_interrupt = result.get("interrupt")
            
            # Check if workflow completed (new flag from TutorWorkflowRunner)
            workflow_completed = result.get("workflow_completed", False)
            state = result.get("state", {})
            workflow_stage = state.get("workflow_stage", "")
            
            if workflow_completed:
                # Workflow has completed - we have the final state
                st.session_state.workflow_active = False
                st.success("🎉 Congratulations! You've completed your learning journey!")
                return True
            elif workflow_stage in ["complete", "session_summary"]:
                # Try to get final state if workflow stage indicates completion
                try:
                    final_state_result = st.session_state.workflow_runner.get_session_state(
                        st.session_state.session_config
                    )
                    if final_state_result["success"]:
                        final_state = final_state_result.get("state", {})
                        st.session_state.current_state.update(final_state)
                        
                        if final_state.get("session_completion_data"):
                            st.session_state.workflow_active = False
                            st.success("🎉 Congratulations! You've completed your learning journey!")
                        elif workflow_stage == "complete":
                            st.session_state.workflow_active = False
                            st.success("🎉 Congratulations! You've completed your learning journey!")
                except Exception as refresh_error:
                    st.warning(f"⚠️ Completed session but couldn't refresh final state: {refresh_error}")
                    if workflow_stage == "complete":
                        st.session_state.workflow_active = False
            
            return True
        else:
            error_msg = result.get('error', 'Unknown error')
            st.error(f"❌ Error processing response: {error_msg}")
            return False
            
    except Exception as e:
        st.error(f"❌ Unexpected error resuming workflow: {str(e)}")
        
        # Show debug info
        with st.expander("🔧 Debug Information"):
            st.json({
                "error": str(e),
                "user_response": str(user_response),
                "session_config": st.session_state.get("session_config"),
                "current_state_keys": list(st.session_state.get("current_state", {}).keys())
            })
        return False

def display_session_summary(session_data: Dict[str, Any]):
    """Display comprehensive session summary beautifully"""
    st.markdown("---")
    
    # Header with celebration
    st.markdown("""
    <div style="text-align: center; padding: 2rem; background: linear-gradient(135deg, #4caf50 0%, #2e7d32 100%); 
                border-radius: 15px; color: white; margin: 2rem 0;">
        <h1>🎓 Learning Session Complete!</h1>
        <h3>Congratulations on completing your learning journey!</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Session statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "🎯 Main Topic",
            session_data.get("initial_topic", "Unknown"),
            help="The topic you originally wanted to learn"
        )
    
    with col2:
        st.metric(
            "📚 Topics Learned", 
            f"{session_data.get('total_topics_learned', 0)}/{session_data.get('total_topics_planned', 0)}",
            help="Topics completed vs planned"
        )
    
    with col3:
        st.metric(
            "❓ Questions Asked",
            session_data.get("questions_asked_count", 0),
            help="Number of follow-up questions you asked"
        )
    
    with col4:
        learning_roadmap = session_data.get("learning_roadmap", [])
        if learning_roadmap:
            st.metric(
                "📈 Completion Rate",
                "100%",
                help="You completed your entire learning roadmap!"
            )
    
    # Learning journey visualization
    st.subheader("🗺️ Your Learning Journey")
    
    if learning_roadmap:
        # Create visual roadmap using simpler approach
        cols = st.columns(len(learning_roadmap) * 2 - 1)  # Account for arrows
        
        for i, topic in enumerate(learning_roadmap):
            with cols[i * 2]:
                if i == len(learning_roadmap) - 1:
                    # Main goal topic
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #ff9800 0%, #f57c00 100%); 
                               color: white; padding: 0.8rem 1.2rem; border-radius: 25px; 
                               font-weight: bold; box-shadow: 0 2px 8px rgba(255, 152, 0, 0.3);
                               text-align: center; margin: 0.5rem 0;">
                        🎯 {topic}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    # Prerequisite topics
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #4caf50 0%, #2e7d32 100%); 
                               color: white; padding: 0.6rem 1rem; border-radius: 20px; 
                               font-weight: 500; box-shadow: 0 2px 6px rgba(76, 175, 80, 0.3);
                               text-align: center; margin: 0.5rem 0;">
                        ✅ {topic}
                    </div>
                    """, unsafe_allow_html=True)
            
            # Add arrow between topics (except after the last one)
            if i < len(learning_roadmap) - 1:
                with cols[i * 2 + 1]:
                    st.markdown("""
                    <div style="text-align: center; font-size: 1.5rem; color: #666; 
                               padding: 0.8rem 0; display: flex; align-items: center; justify-content: center;">
                        →
                    </div>
                    """, unsafe_allow_html=True)
    
    # Display the LLM-generated summary
    if session_data.get("session_summary"):
        st.markdown("### 📋 Detailed Session Summary")
        
        # Create a beautiful container for the summary
        st.markdown("""
        <div style="background: #ffffff; border: 2px solid #e3f2fd; border-radius: 15px; 
                   padding: 2rem; margin: 1rem 0; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
        """, unsafe_allow_html=True)
        
        st.markdown(session_data["session_summary"])
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Action buttons
    st.markdown("### 🚀 What's Next?")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🆕 Start New Topic", type="primary", use_container_width=True):
            # Reset session state
            st.session_state.workflow_active = False
            st.session_state.current_interrupt = None
            st.session_state.current_state = {}
            st.rerun()
    
    with col2:
        if st.button("📥 Export Summary", use_container_width=True):
            # Create downloadable summary
            summary_text = f"""# Learning Session Summary - {session_data.get('initial_topic', 'Unknown Topic')}

## Your Learning Journey
{' → '.join(learning_roadmap)}

## Session Statistics
- Topics Learned: {session_data.get('total_topics_learned', 0)}/{session_data.get('total_topics_planned', 0)}
- Questions Asked: {session_data.get('questions_asked_count', 0)}
- Completion Rate: 100%

## Detailed Summary
{session_data.get('session_summary', 'No summary available')}

---
Generated by Agentic Tutor
"""
            
            st.download_button(
                label="📄 Download as Text",
                data=summary_text,
                file_name=f"learning_summary_{session_data.get('initial_topic', 'topic').replace(' ', '_')}.txt",
                mime="text/plain"
            )
    
    with col3:
        if st.button("🔄 Refresh Summary", use_container_width=True):
            st.rerun()

# Main App Layout
def main():
    """Main application"""
    
    # Header
    st.markdown('<h1 class="main-header">🎓 Agentic Tutor</h1>', unsafe_allow_html=True)
    st.markdown("### *Personalized AI-powered learning with human-in-the-loop guidance*")
    
    # Initialize session state
    if not initialize_session_state():
        st.error("❌ Failed to initialize the application. Please check the debug information above.")
        return
    
    # Setup API keys
    keys_configured = setup_api_keys()
    
    if not keys_configured:
        st.warning("⚠️ Please configure your API keys in the sidebar to start learning.")
        return
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Current workflow status
        if st.session_state.workflow_active:
            st.header("📚 Active Learning Session")
            
            # The session summary is now handled via interrupts
            # No need to check for completion here as it's handled in the interrupt flow
            
            # Handle regular workflow progress
            if True:
                # Display progress
                if st.session_state.current_state:
                    display_progress(st.session_state.current_state)
                
                # Handle interrupts
                if st.session_state.current_interrupt:
                    interrupt_type = st.session_state.current_interrupt["type"]
                    interrupt_data = st.session_state.current_interrupt["data"]
                    
                    if interrupt_type == "prerequisite_selection":
                        response = handle_prerequisite_selection(interrupt_data)
                        if response:
                            if asyncio.run(resume_workflow(response)):
                                st.rerun()
                    
                    elif interrupt_type == "topic_review":
                        # First display the lesson
                        if interrupt_data.get("lesson_content"):
                            display_lesson(
                                interrupt_data["lesson_content"], 
                                interrupt_data.get("topic", "Unknown Topic")
                            )
                        
                        # Display any recent Q&A prominently
                        current_state = st.session_state.current_state
                        if current_state.get("last_qa_question") and current_state.get("last_qa_answer"):
                            # Show prominent Q&A notification
                            st.success("💬 **Your question has been answered!** See below:")
                            
                            st.markdown('<div class="qa-container">', unsafe_allow_html=True)
                            st.markdown("### 💬 Your Question & Answer")
                            
                            st.markdown(f"**❓ Question:** {current_state['last_qa_question']}")
                            st.markdown("---")
                            st.markdown(f"**✅ Answer:** {current_state['last_qa_answer']}")
                            
                            st.markdown('</div>', unsafe_allow_html=True)
                            st.markdown("---")
                        
                        # Check for and display any Q&A messages from recent interactions (fallback)
                        elif st.session_state.current_state.get("messages"):
                            messages = st.session_state.current_state["messages"]
                            # Look for recent Q&A messages
                            for msg in reversed(messages[-3:]):  # Check last 3 messages
                                if (hasattr(msg, 'content') and 
                                    hasattr(msg, '__class__') and 
                                    msg.__class__.__name__ == 'AIMessage' and
                                    "Q&A about" in msg.content):
                                    
                                    # Display Q&A response
                                    st.markdown('<div class="qa-container">', unsafe_allow_html=True)
                                    st.markdown("### 💬 Your Question & Answer")
                                    st.markdown(msg.content)
                                    st.markdown('</div>', unsafe_allow_html=True)
                                    st.markdown("---")
                                    break
                        
                        response = handle_topic_review(interrupt_data)
                        if response:
                            if asyncio.run(resume_workflow(response)):
                                st.rerun()
                    
                    elif interrupt_type == "session_summary_display":
                        # Display the session summary using the interrupt data
                        session_data = interrupt_data.get("session_completion_data", {})
                        if session_data:
                            display_session_summary(session_data)
                            
                            # Add a button to finish the session
                            st.markdown("---")
                            col1, col2, col3 = st.columns([1, 2, 1])
                            with col2:
                                if st.button("🎯 Finish Session", type="primary", use_container_width=True):
                                    # Resume workflow to complete the session
                                    response = {"action": "acknowledge_summary"}
                                    if asyncio.run(resume_workflow(response)):
                                        st.session_state.workflow_active = False
                                        st.rerun()
                        else:
                            st.error("❌ Session summary data not available")
                    
                    elif interrupt_type == "session_completion_acknowledgment":
                        # Final acknowledgment - session is complete
                        st.session_state.workflow_active = False
                        st.success("🎉 Session completed successfully!")
                        st.rerun()
                
                # Display current lesson if available (but not if it's a session summary)
                elif (st.session_state.current_state.get("current_lesson") and 
                      not st.session_state.current_state.get("session_completion_data")):
                    display_lesson(
                        st.session_state.current_state["current_lesson"],
                        st.session_state.current_state.get("current_topic", "Unknown Topic")
                    )
                
                # Control buttons
                st.markdown("---")
                col_stop, col_status = st.columns(2)
                with col_stop:
                    if st.button("⏹️ End Session", type="secondary"):
                        st.session_state.workflow_active = False
                        st.session_state.current_interrupt = None
                        st.rerun()
                
                with col_status:
                    if st.button("🔄 Refresh Status"):
                        try:
                            # Get current session state
                            state_result = st.session_state.workflow_runner.get_session_state(
                                st.session_state.session_config
                            )
                            if state_result["success"]:
                                st.session_state.current_state = state_result["state"]
                                st.session_state.current_interrupt = state_result["interrupt"]
                            else:
                                st.error(f"❌ Error refreshing state: {state_result.get('error', 'Unknown error')}")
                        except Exception as e:
                            st.error(f"❌ Error refreshing status: {str(e)}")
                        st.rerun()
        
        else:
            # Start new session
            st.header("🎯 Start New Learning Session")
            
            with st.form("new_session_form"):
                topic = st.text_input(
                    "What would you like to learn?",
                    placeholder="e.g., Italian Cooking, Music Theory, Ancient History, Quantum Physics...",
                    help="Enter any topic you want to learn about"
                )
                
                submitted = st.form_submit_button("🚀 Start Learning", type="primary")
                
                if submitted and topic.strip():
                    success = asyncio.run(start_learning_session(topic.strip()))
                    if success:
                        st.rerun()
                elif submitted:
                    st.error("Please enter a topic to learn about")
    
    with col2:
        # Sidebar content
        st.header("📊 Session Info")
        
        # Session status
        if st.session_state.workflow_active:
            st.success("🟢 Session Active")
            
            if st.session_state.current_state:
                initial_topic = st.session_state.current_state.get("initial_topic", "Unknown")
                st.info(f"**Topic:** {initial_topic}")
                
                stage = st.session_state.current_state.get("workflow_stage", "unknown")
                st.info(f"**Stage:** {stage.title()}")
        else:
            st.info("🔵 Ready to Start")
        
        # Learning history
        st.subheader("📝 Recent Activity")
        if st.session_state.learning_history:
            for entry in reversed(st.session_state.learning_history[-5:]):  # Show last 5
                st.text(f"{entry['timestamp'].strftime('%H:%M')} - {entry['action']}: {entry['topic']}")
        else:
            st.text("No recent activity")
        
        # Help section
        st.subheader("❓ How it Works")
        st.markdown("""
        1. **Enter a topic** you want to learn
        2. **Review prerequisites** and select what you know
        3. **Follow the roadmap** topic by topic
        4. **Ask questions** after each lesson
        5. **Complete your journey** at your own pace
        """)
        
        # Debug info (expandable)
        with st.expander("🔧 Debug Info"):
            debug_info = {
                "workflow_active": st.session_state.workflow_active,
                "has_interrupt": bool(st.session_state.current_interrupt),
                "session_exists": bool(st.session_state.session_config),
                "state_keys": list(st.session_state.current_state.keys()) if st.session_state.current_state else [],
                "imports_successful": IMPORTS_SUCCESSFUL
            }
            
            # Add Q&A debug info if available
            if st.session_state.current_state:
                current_state = st.session_state.current_state
                debug_info.update({
                    "has_qa_question": bool(current_state.get("last_qa_question")),
                    "has_qa_answer": bool(current_state.get("last_qa_answer")),
                    "qa_question": current_state.get("last_qa_question", ""),
                    "qa_answer_preview": current_state.get("last_qa_answer", "")[:100] + "..." if current_state.get("last_qa_answer") else "",
                    "topic_complete": current_state.get("topic_complete", False),
                    "awaiting_input": current_state.get("awaiting_user_input", False),
                    "workflow_stage": current_state.get("workflow_stage", "unknown"),
                    "current_topic": current_state.get("current_topic", ""),
                    "message_count": len(current_state.get("messages", [])),
                    "has_session_completion_data": bool(current_state.get("session_completion_data")),
                    "session_completion_keys": list(current_state.get("session_completion_data", {}).keys()) if current_state.get("session_completion_data") else [],
                    "has_session_summary": bool(current_state.get("session_completion_data", {}).get("session_summary")) if current_state.get("session_completion_data") else False
                })
            
            st.json(debug_info)

if __name__ == "__main__":
    main()
