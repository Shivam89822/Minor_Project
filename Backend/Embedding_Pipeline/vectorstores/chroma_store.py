import uuid


def _get_client(persist_directory=None):
    try:
        import chromadb
    except ImportError as exc:
        raise ImportError("The 'chromadb' package is required to store vectors.") from exc

    return (
        chromadb.PersistentClient(path=persist_directory)
        if persist_directory
        else chromadb.Client()
    )


def _get_collection(collection_name, persist_directory=None):
    client = _get_client(persist_directory)
    return client.get_or_create_collection(name=collection_name)


def reset_collection(collection_name, persist_directory=None):
    client = _get_client(persist_directory)

    try:
        client.delete_collection(name=collection_name)
    except Exception:
        pass

    return client.get_or_create_collection(name=collection_name)


def store_in_chroma(chunks, collection_name, persist_directory=None):
    if not chunks:
        return {
            "collection_name": collection_name,
            "stored_count": 0,
        }

    from embeddings.embedder import embed_texts

    collection = _get_collection(collection_name, persist_directory)

    documents = [chunk["text"] for chunk in chunks]
    embeddings = embed_texts(documents)

    collection.add(
        documents=documents,
        embeddings=embeddings.tolist(),
        metadatas=[chunk["metadata"] for chunk in chunks],
        ids=[
            f"{chunk.get('id', 'chunk')}-{uuid.uuid4().hex}"
            for chunk in chunks
        ],
    )

    return {
        "collection_name": collection_name,
        "stored_count": len(chunks),
    }


def query_chroma(question, collection_name, top_k=2, persist_directory=None):
    from embeddings.embedder import embed_texts

    collection = _get_collection(collection_name, persist_directory)
    query_embedding = embed_texts([question])[0].tolist()
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    ids = results.get("ids", [[]])[0]
    distances = results.get("distances", [[]])[0]

    matches = []
    for chunk_id, document, metadata, distance in zip(ids, documents, metadatas, distances):
        matches.append(
            {
                "id": chunk_id,
                "text": document,
                "metadata": metadata,
                "distance": distance,
            }
        )

    return matches
