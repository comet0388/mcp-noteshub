import os

# Define path to the notes directory
NOTES_PATH = os.path.join(os.path.dirname(__file__), "../notes")

def load_notes():
    notes = []
    for fname in os.listdir(NOTES_PATH):
        if fname.endswith(".md"):
            with open(os.path.join(NOTES_PATH, fname), "r", encoding="utf-8") as f:
                content = f.read()
            notes.append({
                "id": f"note:{fname}",
                "title": fname.replace(".md", ""),
                "preview": content[:80] + "...",
                "content": content
            })
    return notes
