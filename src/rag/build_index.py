from pathlib import Path
import json
import chromadb
from sentence_transformers import SentenceTransformer


def load_jsonl(file_path: str):
    """
    Load JSONL records from disk.
    Each line is one JSON object.
    """
    records = []

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            records.append(json.loads(line))

    print(f"Loaded {len(records)} records from {file_path}")
    return records


def chunk_list(items, batch_size: int):
    """
    Yield successive chunks from a list.
    """
    for i in range(0, len(items), batch_size):
        yield items[i:i + batch_size]


def build_index():
    """
    Build a Chroma vector index from the RAG knowledge base.
    """
    input_path = "data/processed/rag_knowledge_base.jsonl"
    chroma_path = "artifacts/rag/chroma_db"
    collection_name = "incident_memory"

    # Safe batch size below Chroma's max batch size
    batch_size = 5000

    # Load records
    records = load_jsonl(input_path)

    # Load embedding model
    model = SentenceTransformer("all-MiniLM-L6-v2")
    print("Loaded embedding model: all-MiniLM-L6-v2")

    # Create persistent Chroma client
    Path(chroma_path).mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=chroma_path)

    # Delete existing collection if it already exists
    existing = [c.name for c in client.list_collections()]
    if collection_name in existing:
        client.delete_collection(collection_name)
        print(f"Deleted existing collection: {collection_name}")

    # Create fresh collection
    collection = client.create_collection(name=collection_name)
    print(f"Created collection: {collection_name}")

    # Prepare data
    ids = []
    documents = []
    metadatas = []

    for record in records:
        ids.append(record["doc_id"])
        documents.append(record["retrieval_text"])

        # Metadata must be simple primitive values
        metadatas.append(
            {
                "source": record["source"],
                "issue_description": record["issue_description"],
                "resolution": record["resolution"],
                "type": record["type"],
                "queue": record["queue"],
                "priority": record["priority"],
                "tags": ", ".join(record["tags"]) if isinstance(record["tags"], list) else str(record["tags"]),
            }
        )

    # Create embeddings
    embeddings = model.encode(documents, show_progress_bar=True).tolist()
    print("Embeddings created.")

    # Add to Chroma in batches
    total_docs = len(ids)
    print(f"Adding {total_docs} documents to Chroma in batches of {batch_size}...")

    start = 0
    while start < total_docs:
        end = min(start + batch_size, total_docs)

        collection.add(
            ids=ids[start:end],
            documents=documents[start:end],
            embeddings=embeddings[start:end],
            metadatas=metadatas[start:end],
        )

        print(f"Added batch: {start} to {end - 1}")
        start = end

    print(f"Indexed {len(ids)} documents into Chroma.")
    print(f"Vector DB saved at: {chroma_path}")


if __name__ == "__main__":
    build_index()