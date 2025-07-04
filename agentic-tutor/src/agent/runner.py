import asyncio
from typing import Any, Dict

from langchain_core.messages import HumanMessage
from langgraph.types import Command

from .workflow import create_graph


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