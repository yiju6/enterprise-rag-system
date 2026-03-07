import streamlit as st
import requests

st.title("KnowledgeDesk")
st.caption("Ask questions about your company documents")

# File upload
uploaded_file = st.file_uploader("Upload a PDF document", type="pdf")

if uploaded_file:
    files = {"file": (uploaded_file.name, uploaded_file, "application/pdf")}
    response = requests.post("http://127.0.0.1:8000/ingest", files=files)
    if response.status_code == 200:
        st.success(f"{uploaded_file.name} uploaded and indexed successfully!")
    else:
        st.error("Failed to upload file.")

# Question input
question = st.text_input("Enter your question")

if st.button("Ask"):
    if not question:
        st.warning("Please enter a question.")
    else:
        with st.spinner("Searching..."):
            response = requests.post(
                "http://127.0.0.1:8000/ask",
                json={"question": question}
            )
            if response.status_code == 200:
                data = response.json()
                st.markdown("### Answer")
                st.write(data["answer"])
                st.markdown("### Sources")
                for source in data["sources"]:
                    st.write(f"- {source}")
            else:
                st.error("Something went wrong. Please try again.")