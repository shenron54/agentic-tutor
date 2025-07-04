# Bug Reports and Resolutions

This document tracks identified bugs and their root causes within the Agentic Tutor project.

---

### 1. Incorrect Roadmap Generation for Single Topics

*   **Status:** Identified
*   **Associated Files:** `agent/nodes/roadmap.py`

#### Observed Behavior

When a user is presented with a list of prerequisites and marks all but one as "known", the subsequent learning roadmap is generated incorrectly. Instead of creating a simple two-step roadmap (the single unknown prerequisite followed by the main topic), the agent expands the single prerequisite into a detailed, multi-step curriculum.

For example, if the only unknown prerequisite is "Ensemble Methods," the agent creates a full course on that topic, as seen below.

*Image: Prerequisite selection showing only one topic remaining.*
![Prerequisite Selection](bug-captures\bug1a.png)

*Image: The incorrectly expanded roadmap for the single topic.*
![Incorrect Roadmap](bug-captures\bug1b.png)

#### Root Cause Analysis

The issue stems from an ambiguous instruction in the prompt for the `roadmap_agent_node`. The prompt instructs the LLM to "create a logical, step-by-step learning roadmap."

-   When the input list of topics is long, the LLM correctly interprets its task as **ordering** the given topics.
-   However, when the input list contains only two items (the single unknown prerequisite and the main goal), the LLM misinterprets the instruction and acts as a **curriculum designer**, breaking down the broad prerequisite topic into smaller sub-topics. This emergent behavior is a side effect of the prompt's lack of constraints.

---

### 2. Follow-up Question Count is Not Tracked

*   **Status:** Resolved
*   **Associated Files:** `agent/core/state.py`, `agent/nodes/learning.py`, `agent/nodes/completion.py`

#### Observed Behavior

The final session summary screen consistently shows "0" for the "Questions Asked" metric, even when the user has asked one or more questions about the lesson content during the topic review stage.

*Image: The session summary screen displaying an incorrect question count.*
![Session Summary](bug-captures\bug2.jpeg)

#### Root Cause Analysis

The root cause was an unreliable method for tracking questions. The original implementation did not explicitly store a list of questions in the agent's state. Instead, the `session_summary_node` attempted to calculate the count by **parsing the entire chat history** from `state.messages` and searching for specific keywords (e.g., "Q&A about").

This method was brittle and would fail if:
- The format of the Q&A message changed.
- The chat history was not perfectly preserved or retrieved.

The fix involved modifying the `AgentState` to include a dedicated `questions_asked` list, updating the `topic_review_node` to append to this list, and changing the `session_summary_node` to get the count directly from `len(state.questions_asked)`. 