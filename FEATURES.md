# 🎓 Agentic Tutor Feature Roadmap

This document outlines the prioritized features for the development of the Agentic Tutor application.

---

###  foreseeable-future: High Priority (Core Backend & API)
-   **Implement FastAPI Backend:** 
    -   [ ] Create the basic FastAPI application structure.
    -   [ ] Design and implement API endpoints (`/start`, `/resume`, `/state`) to interact with the `TutorWorkflowRunner`.
    -   [ ] This will replace the direct Streamlit integration with a scalable, decoupled API.

-   **Enable Streaming:**
    -   [ ] Implement Server-Sent Events (SSE) in a dedicated FastAPI endpoint.
    -   [ ] Stream real-time updates and logs from the LangGraph workflow to the client as they happen.

---

### next-version: Medium Priority (Web Application & User Features)
-   **Basic Web Frontend:**
    -   [ ] Develop a simple, modern web application (e.g., using React, Vue, or HTMX).
    -   [ ] This new UI will communicate with the FastAPI backend instead of running in-process like Streamlit.

-   **User Authentication:**
    -   [ ] Add user registration, login/logout functionality.
    -   [ ] Secure API endpoints and manage user sessions (e.g., with JWT).

-   **Learning History:**
    -   [ ] Implement a UI component to display a user's previously completed learning topics.
    -   [ ] This requires a corresponding API endpoint and database integration.

---

### future: Low Priority (Advanced Agent & Content Features)
-   **PDF-based Learning:**
    -   [ ] Create functionality to allow users to upload a PDF document.
    -   [ ] The agent will need to be able to extract content chapter-by-chapter and use it as the knowledge base for a learning session.

-   **Visual Language Model (VLM) Integration:**
    -   [ ] Enhance lessons by integrating a VLM.
    -   [ ] The agent could use the VLM to dynamically generate or retrieve diagrams and model architectures to better illustrate concepts. 