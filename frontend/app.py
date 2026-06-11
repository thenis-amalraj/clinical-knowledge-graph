"""Clinical Knowledge Graph — Streamlit chat frontend."""

from __future__ import annotations

import os

import requests
import streamlit as st
from streamlit_agraph import Config, Edge, Node, agraph

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# ── Node styling ──────────────────────────────────────────────────────────────
_COLORS = {
    "Disease": "#e74c3c",   # red
    "Drug": "#3498db",      # blue
    "Symptom": "#f39c12",   # amber
    "Document": "#95a5a6",  # gray
}
_SIZES = {"Disease": 25, "Drug": 25, "Symptom": 20, "Document": 12}

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Clinical Knowledge Graph", layout="wide")
st.title("Clinical Knowledge Graph")

# ── Session state bootstrap ───────────────────────────────────────────────────
# Must happen before any widget that reads state.
# clicked_node persists the agraph click across full-script reruns; without this
# the click is lost the moment any other interaction triggers a rerun.
for _key, _default in [
    ("messages", []),
    ("graph_nodes", []),
    ("graph_rels", []),
    ("clicked_node", None),
]:
    if _key not in st.session_state:
        st.session_state[_key] = _default

# ── Layout ────────────────────────────────────────────────────────────────────
col_chat, col_graph = st.columns([1, 2])

# ── Left column: chat ─────────────────────────────────────────────────────────
with col_chat:
    st.subheader("Chat")

    # Render existing messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # Chat input triggers a rerun when submitted; returns None otherwise
    query = st.chat_input("Ask about clinical entities, drugs, or diseases…")
    if query:
        st.session_state.messages.append({"role": "user", "content": query})

        with st.spinner("Querying knowledge graph…"):
            try:
                resp = requests.post(
                    f"{API_BASE_URL}/chat",
                    json={"query": query},
                    timeout=90,
                )
                resp.raise_for_status()
                data = resp.json()

                st.session_state.messages.append(
                    {"role": "assistant", "content": data["answer"]}
                )
                st.session_state.graph_nodes = data["nodes"]
                st.session_state.graph_rels = data["relationships"]
                st.session_state.clicked_node = None  # reset on new query
            except requests.HTTPError as exc:
                st.session_state.messages.append(
                    {"role": "assistant", "content": f"API error {exc.response.status_code}: {exc.response.text}"}
                )
            except Exception as exc:
                st.session_state.messages.append(
                    {"role": "assistant", "content": f"Connection error: {exc}"}
                )

        st.rerun()

# ── Right column: graph ───────────────────────────────────────────────────────
with col_graph:
    st.subheader("Knowledge Graph")

    if not st.session_state.graph_nodes:
        st.info("Ask a question in the chat to explore the knowledge graph.")
    else:
        # Build agraph primitives
        ag_nodes = [
            Node(
                id=n["id"],
                label=n["name"],
                color=_COLORS.get(n["label"], "#bdc3c7"),
                size=_SIZES.get(n["label"], 20),
            )
            for n in st.session_state.graph_nodes
        ]
        ag_edges = [
            Edge(source=r["source"], target=r["target"], label=r["type"])
            for r in st.session_state.graph_rels
        ]

        config = Config(
            width=780,
            height=480,
            directed=True,
            physics=True,
            hierarchical=False,
        )

        # agraph returns the clicked node ID or None.
        # Binding to session_state prevents the selection from vanishing when
        # a different interaction triggers a full-script rerun (Streamlit's
        # ephemeral execution model would otherwise lose the click event).
        clicked = agraph(nodes=ag_nodes, edges=ag_edges, config=config)
        if clicked is not None:
            st.session_state.clicked_node = clicked

        # ── Node detail panel ─────────────────────────────────────────────────
        if st.session_state.clicked_node:
            node_id = st.session_state.clicked_node
            node_info = next(
                (n for n in st.session_state.graph_nodes if n["id"] == node_id),
                None,
            )
            if node_info:
                color = _COLORS.get(node_info["label"], "#bdc3c7")
                st.markdown(
                    f'<span style="color:{color}">■</span> '
                    f'**{node_info["name"]}** &nbsp; `{node_info["label"]}`',
                    unsafe_allow_html=True,
                )
                rels = [
                    r for r in st.session_state.graph_rels
                    if r["source"] == node_id or r["target"] == node_id
                ]
                if rels:
                    for r in rels:
                        is_outbound = r["source"] == node_id
                        other_id = r["target"] if is_outbound else r["source"]
                        other_name = next(
                            (n["name"] for n in st.session_state.graph_nodes if n["id"] == other_id),
                            other_id,
                        )
                        arrow = "→" if is_outbound else "←"
                        st.write(f"{arrow} **{r['type']}** {other_name}")

        # ── Legend ────────────────────────────────────────────────────────────
        st.markdown("---")
        legend_cols = st.columns(len(_COLORS))
        for col, (label, color) in zip(legend_cols, _COLORS.items()):
            col.markdown(
                f'<span style="color:{color}; font-size:18px">■</span> {label}',
                unsafe_allow_html=True,
            )
