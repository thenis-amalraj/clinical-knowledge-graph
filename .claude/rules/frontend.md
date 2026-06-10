---
paths: ["app/**/*.py", "**/*streamlit*.py", "**/ui/**/*.py"]
---

# Frontend Conventions & Guardrails

- **Session State:** ALL click events and UI state MUST be persisted via `st.session_state`. Never rely on local variables across reruns.
- **agraph Events:** `agraph` click events trigger full script reruns. Bind the selected node ID to `st.session_state["selected_node"]` before issuing any downstream queries.
- **No Blocking Calls:** Do not call Neo4j or the LLM directly from top-level Streamlit script scope. Wrap in functions and gate with `if st.session_state.get(...)`.
- **Component Hygiene:** Keep `streamlit-agraph` node/edge config (colors, sizes) in a single builder function — do not scatter magic values across the script.
