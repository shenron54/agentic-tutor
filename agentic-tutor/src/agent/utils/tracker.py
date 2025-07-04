from typing import Any, Dict

class ProgressTracker:
    """Utility for tracking learning progress."""
    
    @staticmethod
    def calculate_progress(state: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate learning progress from state.
        
        Args:
            state: Current workflow state
            
        Returns:
            Progress information dictionary
        """
        # Handle None or empty state
        if not state or not isinstance(state, dict):
            return {
                "total_topics": 0,
                "completed_count": 0,
                "current_topic": "",
                "progress_percentage": 0,
                "remaining_topics": [],
                "learning_roadmap": []
            }
        
        # Safely extract values with defaults
        learning_roadmap = state.get("learning_roadmap", [])
        completed_topics = state.get("completed_topics", [])
        current_topic_index = state.get("current_topic_index", 0)
        current_topic = state.get("current_topic", "")
        
        # Ensure we have valid lists
        if not isinstance(learning_roadmap, list):
            learning_roadmap = []
        if not isinstance(completed_topics, list):
            completed_topics = []
        
        # Calculate metrics
        total_topics = len(learning_roadmap)
        completed_count = len(completed_topics)
        progress_percentage = (completed_count / total_topics) * 100 if total_topics > 0 else 0
        
        # Calculate remaining topics safely
        remaining_topics = []
        if learning_roadmap and isinstance(current_topic_index, int):
            if current_topic_index < len(learning_roadmap) - 1:
                remaining_topics = learning_roadmap[current_topic_index + 1:]
        
        return {
            "total_topics": total_topics,
            "completed_count": completed_count,
            "current_topic": current_topic,
            "progress_percentage": progress_percentage,
            "remaining_topics": remaining_topics,
            "learning_roadmap": learning_roadmap
        } 