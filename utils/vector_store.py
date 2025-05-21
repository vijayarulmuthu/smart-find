from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

def init_qdrant(path="./qdrant_storage", collection="ecommerce-products"):
    client = QdrantClient(path=path)
    if collection not in [c.name for c in client.get_collections().collections]:
        client.create_collection(
            collection_name=collection,
            vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
        )
    return client

def get_qdrant_client(path="./qdrant_storage", collection="ecommerce-products"):
    return QdrantClient(path=path)
