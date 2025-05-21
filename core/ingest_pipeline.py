# core/ingest_pipeline.py
import uuid
import pandas as pd

from tqdm import tqdm
from qdrant_client.http.models import PointStruct

from utils.llm_utils import get_embedding, call_chat, safe_json_parse
from utils.prompts import PRODUCT_TAGGING_PROMPT
from utils.vector_store import init_qdrant

# === CONFIG ===
INPUT_CSV = "./data/rag_docs.csv"
COLLECTION_NAME = "ecommerce-products"
EMBEDDING_MODEL = "text-embedding-3-small"
LLM_MODEL = "gpt-4.1-mini"

# === LOAD DATA ===
df = pd.read_csv(INPUT_CSV)
df = df.fillna("")

# === INIT QDRANT (uses shared utility) ===
qdrant = init_qdrant(collection=COLLECTION_NAME)

# === PIPELINE ===
points = []
for i, row in tqdm(df.iterrows(), total=len(df)):
    doc = row["rag_document"]
    uniq_id = row.get("uniq_id") or str(uuid.uuid4())

    # Step 1: Tag generation
    tag_response = call_chat(LLM_MODEL, PRODUCT_TAGGING_PROMPT, doc)
    tags = safe_json_parse(tag_response, key="tags", fallback="misc")

    # Step 2: Embedding
    embedding = get_embedding(doc)

    # Step 3: Qdrant point construction
    point = PointStruct(
        id=str(uniq_id),
        vector=embedding,
        payload={
            "reviews": row.get("customer_reviews", ""),
            "price": row.get("price"),
            "rating": row.get("rating"),
            "tags": tags,
            "document": doc
        }
    )
    points.append(point)

# === UPSERT TO QDRANT ===
qdrant.upsert(collection_name=COLLECTION_NAME, points=points)
print(f"✅ Indexed {len(points)} documents into Qdrant collection '{COLLECTION_NAME}'.")
