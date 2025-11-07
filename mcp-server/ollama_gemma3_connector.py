import requests
import json

# 1️⃣ Get a chunk from your NotesHub FastAPI
query_url = "http://127.0.0.1:8000/tools/query?topic=Inheritance"
chunk_resp = requests.get(query_url)
chunk_data = chunk_resp.json()

context = chunk_data.get("chunk", "No chunk found.")
topic = chunk_data.get("topic", "unknown")

# 2️⃣ Send that chunk to Gemma 3 via Ollama
ollama_url = "http://127.0.0.1:11434/api/chat"
payload = {
    "model": "gemma3:1b",
    "messages": [
        {"role": "system", "content": "You are a helpful study buddy who will ask me questions only on the provided context."},
        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: Explain the topic '{topic}' briefly."}
    ]
}

print("\n💬 Gemma 3 Response:\n")

with requests.post(ollama_url, json=payload, stream=True) as resp:
    for line in resp.iter_lines():
        if line:
            try:
                data = json.loads(line.decode("utf-8"))
                message = data.get("message", {}).get("content")
                if message:
                    print(message, end="", flush=True)
            except json.JSONDecodeError:
                pass

print("\n\n✅ Done.")
