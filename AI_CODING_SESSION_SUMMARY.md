# AI Coding Session Summary

**AI Tool Used:** Antigravity (Agentic AI Coding Assistant)

## How the Tool Was Used
I used Antigravity as a primary pair-programming agent to architect, build, and debug the Dodge AI take-home assignment from scratch. The workflow involved:

1. **Architectural Planning:** Collaborating with the AI to decide on the tech stack (React + Vite for frontend, FastAPI + SQLite for backend, Groq for fast LLM inference) and defining the two-step LLM pipeline.
2. **Backend Implementation:** Iteratively building the database schema (`db.py`), seeding the mock SAP Order-to-Cash dataset, and setting up the core conversational logic (`llm.py` and `main.py`).
3. **Frontend Development:** Working with the AI to integrate `react-force-graph-2d` for the SAP document visualization, designing the chat interface, and connecting the REST API.
4. **Refining Guardrails:** Implementing the multi-layer guardrail system (keyword filtering, system prompt strictness, and fallback error handling) directly into the routing logic to prevent off-topic queries and hallucination.

## Key Prompts & Workflows
- **Initial Setup Workflow:** 
  > *"Build a production-aware, graph-based context system for SAP Order-to-Cash data using React and FastAPI. Set up a two-step LLM pipeline using Groq for NL-to-SQL and grounded answers."*
- **Graph Visualization Prompt:** 
  > *"Integrate react-force-graph-2d into the frontend. The backend will return nodes (Sales Orders, Deliveries, Billing, Journal Entries) and links. Render them with different colors based on document type and handle hover/click states."*
- **Guardrails Implementation Prompt:** 
  > *"Add strict guardrails to the FastAPI backend. If the user asks something unrelated to the dataset (e.g., 'What is 2+2?' or generic questions), the system must reject it instantly. Implement a 3-layer guardrail: keyword check, prompt instruction, and execution catch."*

## Debugging and Iteration Process
1. **SQL Generation Iteration:** Initially, the LLM sometimes hallucinated JOIN queries on columns that didn't exist or used generic syntax not supported by the lightweight SQLite setup. 
   - *Fix:* I worked with the AI to forcefully inject the exact SQLite schema and query shot-examples (few-shot prompting) into the system prompt context, alongside setting the `temperature` to `0` for the NL-to-SQL step.
2. **Graph Rendering Optimization:** Rendering the SAP flow caused overlapping nodes and visual clutter in the early iterations.
   - *Fix:* Iterated with the AI to tweak the D3 force physics and implemented purely canvas-based drawing logic for custom node rendering, which vastly improved performance compared to heavy DOM nodes.
3. **Guardrail Edge Cases:** The system initially rejected valid but vaguely-phrased queries if they lacked exact table names.
   - *Fix:* Broadened the keyword heuristic list and shifted more reliance onto the LLM's semantic understanding in the system prompt. If the first step returns `CANNOT_ANSWER`, the flow elegantly halts.

By leveraging an agentic AI workflow, I was able to focus on the high-level system design, data modeling, and UX decisions, while delegating boilerplate generation, component wiring, and syntax-level debugging to the AI.
