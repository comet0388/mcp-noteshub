from unstructured.partition.auto import partition
from pathlib import Path
import re

def extract_chunks(file_path: str, max_chars: int = 1200):
    """
    Smart context-aware chunker:
    - Keeps sections with lead-in colons and their list items together
    - Avoids dangling or premature chunk breaks
    - Groups small fragments or short headings with their related paragraphs
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    elements = partition(file_path)
    chunks = []
    current_chunk = ""
    current_type = None
    i = 0

    while i < len(elements):
        el = elements[i]
        text = (el.text or "").strip()
        if not text:
            i += 1
            continue

        el_type = type(el).__name__

        # 🧠 Case 1: Lead-in that ends with ':' — check next elements
        if re.search(r":$", text.strip()) and len(text.split()) < 30:
            # Look ahead for list items or short related lines
            lookahead_texts = []
            j = i + 1
            while j < len(elements):
                nxt = elements[j]
                nxt_text = (nxt.text or "").strip()
                if not nxt_text:
                    j += 1
                    continue
                nxt_type = type(nxt).__name__

                # Stop if next is a Title or too long paragraph (new section)
                if nxt_type == "Title" or len(nxt_text.split()) > 60:
                    break

                # Include if it's a list item or short colon-style line
                if nxt_type == "ListItem" or re.match(r"^[-•]|\w+:", nxt_text):
                    lookahead_texts.append(nxt_text)
                    j += 1
                    continue

                # Otherwise, stop at first normal paragraph
                break

            # Merge this lead-in and all its related lines
            if lookahead_texts:
                text = text + "\n" + "\n".join(lookahead_texts)
                i = j - 1  # skip over the merged ones

        # 🧩 Detect short fragments (avoid making them standalone)
        is_fragment = (
            len(text.split()) < 8
            and not re.search(r"[.!?]$", text)
            and not re.search(r"\b(is|are|was|were|has|have|can|should|will|be)\b", text.lower())
        )
        if is_fragment and chunks:
            chunks[-1] += "\n" + text
            i += 1
            continue

        # 🚧 Split when too large or structural change
        if (
            len(current_chunk) + len(text) > max_chars
            or el_type == "Title"
            or (current_type and el_type != current_type and len(current_chunk) > 0)
        ):
            chunks.append(current_chunk.strip())
            current_chunk = ""

        current_chunk += ("\n" if current_chunk else "") + text
        current_type = el_type
        i += 1

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    # Filter out tiny leftover lines
    chunks = [c for c in chunks if len(c.split()) > 5]

    return chunks
