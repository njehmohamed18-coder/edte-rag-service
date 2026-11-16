import streamlit as st
import httpx

API_BASE = "http://127.0.0.1:8000/api/v1/rag"

st.set_page_config(page_title="EDTE GraphRAG", layout="wide")
st.title("🌐 EDTE Semantic GraphRAG Engine")
st.markdown("Team 4: Cognitive Layer for the Enterprise Digital Twin Engine")

col1, col2 = st.columns([1, 2])

with col1:
    st.header("📥 Ingest Document")
    uploaded_file = st.file_uploader("Upload Policy (Markdown/PDF)", type=["md", "pdf"])
    if st.button("Process Document") and uploaded_file:
        with st.spinner("Chunking, embedding, and extracting graph entities..."):
            files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
            resp = httpx.post(f"{API_BASE}/ingest/file", files=files, timeout=60.0)
            if resp.status_code == 200:
                st.success("Document ingested successfully!")
                st.json(resp.json())
            else:
                st.error(f"Error: {resp.text}")

with col2:
    st.header("🔍 Ask the Graph")
    question = st.text_input("Query your enterprise policies:")
    if st.button("Search & Synthesize") and question:
        with st.spinner("Traversing graph and synthesizing answer..."):
            payload = {"question": question, "top_k": 3, "expand_graph_hops": 1}
            resp = httpx.post(f"{API_BASE}/query", json=payload, timeout=60.0)
            
            if resp.status_code == 200:
                data = resp.json()
                st.markdown("### 🤖 Synthesized Answer")
                st.info(data.get("answer"))
                
                st.markdown("### 📊 Retrieved Graph Context")
                st.json(data.get("graph_context", []))
                
                st.markdown("### 📄 Source Text Chunks")
                for source in data.get("sources", []):
                    with st.expander(f"Source: {source['chunk_urn']} (Score: {source['score']:.2f})"):
                        st.write(source['text_snippet'])
            else:
                st.error(f"Error: {resp.text}")
