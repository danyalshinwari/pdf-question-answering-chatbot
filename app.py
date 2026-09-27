"""Run with: python -m streamlit run app.py. Read comments from top to bottom."""

import hashlib  # Create a stable fingerprint when the uploaded PDF changes.
import os  # Read API settings from environment variables.
from pathlib import Path  # Locate files relative to this project, regardless of terminal location.

import streamlit as st  # Build the browser interface with Python.
from dotenv import load_dotenv  # Load local settings from the .env file.

from rag import EMBEDDING_MODEL, build_index, generate_answer, read_pdf, retrieve, split_pages
# The imported functions keep document processing separate from interface code.

ROOT = Path(__file__).resolve().parent  # Find the folder containing this app.py file.
load_dotenv(ROOT / ".env")  # Load settings without overwriting existing environment variables.
st.set_page_config(page_title="PDF Study Assistant", page_icon="📄", layout="wide")  # Set browser layout.


@st.cache_resource  # Download/load the public embedding model once per running app process.
def load_embeddings():  # No PDF text is stored in this shared model cache.
    from langchain_huggingface import HuggingFaceEmbeddings  # Optional semantic dependency.
    return HuggingFaceEmbeddings(  # Create an object that converts text to vectors on this computer.
        model_name=EMBEDDING_MODEL,  # Use the documented small English embedding model.
        model_kwargs={"device": "cpu"},  # Work without a graphics card.
        encode_kwargs={"normalize_embeddings": True},  # Make vector lengths comparable.
    )


def show_sources(sources):  # Reuse the same source display for every answer.
    for number, source in enumerate(sources, start=1):  # Number the retrieved excerpts.
        with st.expander(f"Source {number} · PDF page {source.metadata['page']}"):
            st.text(source.page_content)  # Render raw text, so PDF contents cannot inject HTML.


if "index" not in st.session_state:  # Initialize state on the first run of this browser session.
    st.session_state.index = None  # No PDF is searchable until processing succeeds.
    st.session_state.messages = []  # Store question/answer cards for display only.
    st.session_state.active_signature = None  # Remember which PDF and backend the index belongs to.
    st.session_state.stats = None  # Store page/chunk counts for the learning panel.

st.title("📄 PDF Study Assistant")  # Draw the main page title.
st.write("Upload notes, find evidence, and ask questions about your PDF.")  # Explain the task.
st.caption("One PDF at a time · English text PDFs · Each question is independent")  # Set expectations.

with st.sidebar:  # Put configuration controls in the left panel.
    st.header("1. Choose a PDF")  # Label the first step.
    use_sample = st.checkbox("Use the included sample PDF", value=True)  # Enable immediate practice.
    uploaded = None  # Avoid referencing an undefined upload variable in sample mode.
    if not use_sample:  # Show upload only when the user wants their own file.
        uploaded = st.file_uploader("Upload PDF (up to 20 MiB)", type=["pdf"])
    st.header("2. Choose search")  # Label the search-method choice.
    search_label = st.selectbox("Search method", ["Keyword (easy start)", "Semantic (optional)"])
    backend = "keyword" if search_label.startswith("Keyword") else "semantic"  # Map label to code value.
    st.caption("Keyword search works locally. Semantic search needs the optional installation and model download.")
    answer_mode = st.radio("Answer mode", ["Search passages only", "Generate answer with Gemini"])
    api_key = os.getenv("GEMINI_API_KEY", "").strip()  # Read the secret without displaying it.
    model = st.text_input("Gemini model ID", value=os.getenv("GEMINI_MODEL", ""))  # Allow model choice.
    if answer_mode == "Generate answer with Gemini":  # Explain data transfer before an API request.
        st.caption("Your question and retrieved passages will be sent to Google Gemini. API billing applies per your Google AI account.")
        if not api_key:  # Help beginners identify missing configuration before asking a question.
            st.warning("Add GEMINI_API_KEY to .env, then restart the app.")
    process = st.button("Process PDF", type="primary", use_container_width=True)  # Explicit indexing action.
    if st.button("Clear conversation", use_container_width=True):  # Keep the index while clearing displayed history.
        st.session_state.messages = []  # Delete only this session's prior cards.

pdf_bytes = None  # Default when no upload has been selected.
filename = ""  # Default display filename.
if use_sample:  # Use a small local PDF for reproducible learning.
    sample_path = ROOT / "sample_documents" / "machine_learning_notes.pdf"  # Locate included notes.
    pdf_bytes = sample_path.read_bytes()  # Read the bundled PDF into memory.
    filename = sample_path.name  # Show just the filename in metadata.
elif uploaded is not None:  # Otherwise use the actual uploaded file.
    pdf_bytes = uploaded.getvalue()  # Copy bytes from Streamlit's in-memory upload object.
    filename = uploaded.name  # Preserve the source label for this session.

signature = None  # No signature exists without a file.
if pdf_bytes is not None:  # Include bytes, filename, and backend in the index identity.
    signature = (hashlib.sha256(pdf_bytes).hexdigest(), filename, backend)
if signature != st.session_state.active_signature:  # Invalidate old results immediately on any input change.
    st.session_state.index = None  # Prevent accidental retrieval from a previous document.
    st.session_state.messages = []  # Prevent stale answers from appearing beside a new upload.
    st.session_state.stats = None  # Clear previous page/chunk counts.
    st.session_state.active_signature = signature  # Record the current inputs, even before processing.

if process:  # Run expensive PDF processing only when the button is clicked.
    st.session_state.index = None  # A failed rebuild must not leave an older index usable.
    st.session_state.messages = []  # Clear cards when rebuilding the document.
    st.session_state.stats = None  # Clear old metrics before the new attempt.
    if pdf_bytes is None:  # Handle clicking Process without selecting a file.
        st.warning("Choose a PDF first.")  # Give an actionable instruction.
    else:  # The selected file can now be processed.
        try:  # Handle expected dependency and document errors gracefully.
            with st.spinner("Reading the PDF and building its search index…"):
                pages, total, skipped = read_pdf(pdf_bytes, filename)  # Extract labelled pages.
                chunks = split_pages(pages)  # Create smaller labelled text sections.
                embeddings = load_embeddings() if backend == "semantic" else None  # Load only if needed.
                index = build_index(chunks, backend, embeddings)  # Build local word or vector search.
                st.session_state.index = index  # Keep the index for subsequent Streamlit reruns.
                st.session_state.stats = {"pages": total, "chunks": len(chunks), "skipped": skipped}
            st.success("PDF ready. Ask a question below.")  # Confirm the successful milestone.
        except ImportError:  # Optional dependencies may not have been installed yet.
            st.error("Install requirements-semantic.txt using the README instructions, then restart.")
        except ValueError as error:  # Our validation messages are designed for display.
            st.error(str(error))  # Show the specific PDF or vocabulary problem.
        except Exception:  # Model download or runtime errors should not expose secrets or traces.
            st.error("Processing failed. Check your internet/model download, or switch to Keyword search. See README troubleshooting.")

if st.session_state.stats:  # Show learning information only for a successfully processed document.
    stats = st.session_state.stats  # Give the stored dictionary a shorter local name.
    first, second = st.columns(2)  # Put the two summary values side by side.
    first.metric("PDF pages", stats["pages"])  # Count includes blank/skipped pages.
    second.metric("Searchable chunks", stats["chunks"])  # Show how splitting changed the document.
    if stats["skipped"]:  # Warn about incomplete text coverage in mixed scanned/text PDFs.
        st.warning(f"No text on these PDF pages: {stats['skipped']}. Answers cannot use their images.")
    with st.expander("Learn: inspect the first chunk"):
        first_chunk = st.session_state.index["chunks"][0]  # Read the actual indexed chunk.
        st.write(f"Physical PDF page: {first_chunk.metadata['page']}")  # Explain the citation coordinate.
        st.text(first_chunk.page_content)  # Show the chunk without markdown interpretation.
else:  # Before processing, provide a useful next action.
    st.info("Click Process PDF in the sidebar. Try: What is overfitting?")

for message in st.session_state.messages:  # Redraw previous cards after each UI interaction.
    with st.chat_message("user"):
        st.write(message["question"])  # Display the question as entered.
    with st.chat_message("assistant"):
        st.write(message["answer"])  # Display either the generated answer or search-mode explanation.
        show_sources(message["sources"])  # Keep supporting text attached to this exact answer.

question = st.chat_input("Ask a complete question about this PDF", disabled=st.session_state.index is None)
if question:  # Streamlit reruns the script when the user submits this input.
    try:  # Do not save a failed question as a successful answer.
        with st.spinner("Finding relevant passages…"):
            sources = retrieve(st.session_state.index, question)  # Search the prepared index once.
            if answer_mode == "Search passages only":  # Free mode shows evidence, not a generated answer.
                answer = "Here are the closest matching passages. This mode does not generate an AI answer."
                if not sources:  # Word search may find no overlapping vocabulary.
                    answer = "No matching passages found. Try words that appear in your PDF."
            else:  # Paid API mode combines retrieval with language generation.
                answer = generate_answer(question, sources, api_key, model.strip())
        st.session_state.messages.append({"question": question, "answer": answer, "sources": sources})
        st.rerun()  # Redraw the page so the new question/answer card appears once.
    except ValueError as error:  # Show input/configuration messages from our own code.
        st.error(str(error))
    except Exception as error:  # Translate common Gemini errors into beginner-friendly actions.
        error_msg = str(error).lower()
        if "api_key" in error_msg or "authentication" in error_msg or "401" in error_msg:
            st.error("API authentication failed. Check your Gemini key in .env and restart.")
        elif "rate" in error_msg or "quota" in error_msg or "429" in error_msg:
            st.error("API quota/rate limit reached. Check billing and usage, or retry later.")
        elif "not found" in error_msg or "404" in error_msg or "permission" in error_msg:
            st.error("Check the model ID and your Google AI account's access to that model.")
        else:  # Network issues and timeouts can be transient.
            st.error("Could not generate an answer. Check your internet/API settings and try again.")

st.caption("Check answers against source passages. Page references use PDF page positions, not printed page labels.")
