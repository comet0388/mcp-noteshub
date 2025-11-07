# utils/rag_helper.py
"""
RAG (Retrieval-Augmented Generation) helper for MCP NotesHub.
This version:
- Explicitly selects the correct Unstructured parser for each file type.
- Avoids "source code string cannot contain null bytes" errors.
- Returns contextual chunks for AI-based quiz generation.
"""

from pathlib import Path
import os
from unstructured.partition.auto import partition
from unstructured.partition.pdf import partition_pdf
from unstructured.partition.docx import partition_docx
from unstructured.partition.text import partition_text
from unstructured.partition.md import partition_md
from unstructured.partition.html import partition_html

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings



# ---------------------- #
#       CONSTANTS        #
# ---------------------- #

NOTES_DIR = Path(__file__).resolve().parent.parent / "notes"
VECTOR_DIR = Path(__file__).resolve().parent.parent / "data" / "chroma_store"
embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")


# ---------------------- #
#     SAFE PARTITION     #
# ---------------------- #

def safe_partition(file_path: str):
    """
    Selects the appropriate Unstructured parser based on file extension.
    Prevents null byte decoding errors by avoiding incorrect file mode.
    """
    ext = Path(file_path).suffix.lower()

    try:
        if ext == ".pdf":
            return partition_pdf(filename=file_path)
        elif ext == ".docx":
            return partition_docx(filename=file_path)
        elif ext == ".txt":
            return partition_text(filename=file_path)
        elif ext == ".md":
            return partition_md(filename=file_path)
        elif ext == ".html":
            return partition_html(filename=file_path)
        else:
            # Fallback for unsupported or rare formats
            return partition(filename=file_path)
    except Exception as e:
        raise RuntimeError(f"Error parsing {file_path}: {e}")


# ---------------------- #
#   BUILD VECTOR STORE   #
# ---------------------- #

def build_vectorstore(file_name: str):
    """
    Extracts text from a given note file, splits it into chunks,
    and builds a Chroma vectorstore with sentence embeddings.
    """
    file_path = NOTES_DIR / file_name
    if not file_path.exists():
        raise FileNotFoundError(f"File '{file_name}' not found in {NOTES_DIR}")

    # 1️⃣ Parse text safely
    elements = safe_partition(str(file_path))
    text = "\n".join([el.text.strip() for el in elements if getattr(el, "text", None)])

    # 2️⃣ Split text into overlapping chunks
    splitter = RecursiveCharacterTextSplitter(chunk_size=2500, chunk_overlap=100)
    docs = splitter.create_documents([text])

    # 3️⃣ Build and persist embeddings
    os.makedirs(VECTOR_DIR, exist_ok=True)
    vectorstore = Chroma.from_documents(
        docs,
        embedding_model,
        persist_directory=str(VECTOR_DIR)
    )

    return vectorstore


# ---------------------- #
#   CONTEXT RETRIEVAL    #
# ---------------------- #
from difflib import SequenceMatcher
import os

def is_similar(a, b, threshold=0.9):
    """Check if two text chunks are semantically similar."""
    return SequenceMatcher(None, a, b).ratio() > threshold

def deduplicate_semantic(chunks, threshold=0.9):
    """Remove near-duplicate chunks using semantic similarity."""
    unique = []
    for chunk in chunks:
        if not any(is_similar(chunk, u, threshold) for u in unique):
            unique.append(chunk)
    return unique


def get_relevant_chunks(file_name: str = None, topic: str = None, k: int = 5):
    """
    Adaptive retrieval:
    - file only  -> contextual chunking of that file
    - topic only -> search all note files for topic
    - both       -> semantic retrieval on that file for topic
    """

    if not file_name and not topic:
        raise ValueError("❌ Please provide at least a file name or a topic.")

    # ------------------------------
    # CASE 1: File only
    # ------------------------------
    if file_name and not topic:
        file_path = NOTES_DIR / file_name
        if not file_path.exists():
            raise FileNotFoundError(f"File '{file_name}' not found in {NOTES_DIR}")

        elements = safe_partition(str(file_path))
        text = "\n".join([el.text.strip() for el in elements if getattr(el, "text", None)])

        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=50)
        docs = splitter.create_documents([text])
        chunks = [d.page_content.strip() for d in docs if d.page_content.strip()]

        return {
            "mode": "file_only",
            "file": file_name,
            "topic": None,
            "total_chunks": len(chunks),
            "context_chunks": chunks
        }

    # ------------------------------
    # CASE 2: Topic only
    # ------------------------------
    elif topic and not file_name:
        all_chunks = []

        for file in os.listdir(NOTES_DIR):
            if not file.endswith(('.pdf', '.docx', '.txt', '.md', '.html')):
                continue
            try:
                vectorstore = build_vectorstore(file)
                retriever = vectorstore.as_retriever(search_kwargs={"k": k})
                retrieved_docs = retriever.invoke(topic)
                all_chunks.extend(
                    [doc.page_content.strip() for doc in retrieved_docs if doc.page_content.strip()]
                )
            except Exception as e:
                print(f"⚠️ Skipping {file}: {e}")

        # Simple deduplication
        chunks = list(dict.fromkeys(all_chunks))

        return {
            "mode": "topic_only",
            "topic": topic,
            "file": None,
            "total_chunks": len(chunks),
            "context_chunks": chunks
        }

    # ------------------------------
    # CASE 3: File + Topic
    # ------------------------------
    else:
        vectorstore = build_vectorstore(file_name)
        retriever = vectorstore.as_retriever(search_kwargs={"k": k})
        retrieved_docs = retriever.invoke(topic)

        chunks = [doc.page_content.strip() for doc in retrieved_docs if doc.page_content.strip()]
        chunks = deduplicate_semantic(chunks)

        return {
            "mode": "file_and_topic",
            "file": file_name,
            "topic": topic,
            "total_chunks": len(chunks),
            "context_chunks": chunks
        }
