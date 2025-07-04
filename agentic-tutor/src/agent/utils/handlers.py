from typing import Any, Dict, List

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