# core/search_pipeline.py
import logging
import os
import time
import cohere

from typing import List, Tuple

from qdrant_client import models

from utils.llm_utils import get_embedding, call_chat, safe_json_parse, clean_rag_document
from utils.prompts import QUERY_TAGGING_PROMPT, RESEARCH_PROMPT
from utils.vector_store import get_qdrant_client

# === CONFIG ===
COLLECTION_NAME = "ecommerce-products"
EMBEDDING_MODEL = "text-embedding-3-small"
LLM_MODEL = "gpt-4.1-mini"
COHERE_MODEL = "rerank-v3.5"
COHERE_KEY = os.getenv("COHERE_API_KEY")

# === LOGGING ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("search_agent")

# === INIT ===
co = cohere.Client(COHERE_KEY)

# === QUERY TAG PARSER ===
def get_tags(query: str) -> List[str]:
    """
    Extract structured metadata tags from the user's natural language query using an LLM.

    This is typically used to filter vector search results in Qdrant by product attributes
    such as category, age group, material, brand, or theme.

    Args:
        query (str): The user's product search query.

    Returns:
        List[str]: A list of extracted metadata tags (e.g., ['lego', '3+', 'plastic']).
    """
    raw_response = call_chat(LLM_MODEL, QUERY_TAGGING_PROMPT, query)
    return safe_json_parse(raw_response, key="tags", fallback="misc")


# === Qdrant METADATA FILTER ===
def build_metadata_filter(tags: List[str]) -> models.Filter:
    """
    Build a Qdrant-compatible metadata filter using extracted tags.

    Each tag becomes a field condition matched against the 'tags' field in Qdrant payloads.

    Args:
        tags (List[str]): List of tag strings (e.g., ['stem', 'toddler']).

    Returns:
        models.Filter: A Qdrant filter to restrict vector search results to tagged items.
    """
    conditions = [
        models.FieldCondition(key="tags", match=models.MatchValue(value=tag.lower()))
        for tag in tags if tag
    ]
    return models.Filter(should=conditions)


# === SEMANTIC SEARCH ===
def semantic_search(query: str, filter_obj: models.Filter = None, top_k: int = 5) -> List[Tuple[str, float, str, float, float]]:
    """
    Perform hybrid vector search in Qdrant with optional metadata-based filtering.

    Args:
        query (str): The user's query string.
        filter_obj (models.Filter, optional): Qdrant metadata filter (default: None).
        top_k (int): Number of top results to return (default: 5).

    Returns:
        List[Tuple]: Each tuple contains:
            (cleaned_document, qdrant_score, reviews, price, rating)
    """
    logger.info(f"Searching Qdrant for query: '{query}'")
    try:
        qdrant = get_qdrant_client(collection=COLLECTION_NAME)
        results = qdrant.search(
            collection_name=COLLECTION_NAME,
            query_vector=get_embedding(query),
            query_filter=filter_obj,
            limit=top_k
        )
        return [
            (
                clean_rag_document(hit.payload.get("document", "N/A")), # TODO: fix cleanup before indexing into Qdrant
                hit.score,
                hit.payload.get("reviews", ""),
                hit.payload.get("price", 0.0),
                hit.payload.get("rating", 0.0)
            )
            for hit in results
        ]
    finally:
        qdrant.close()

# === SEMANTIC SEARCH WITHOUT TAG FILTERING ===
def semantic_search_without_tags(query: str, top_k: int = 5) -> List[Tuple[str, float, str, float, float]]:
    """
    Perform pure vector-based semantic search without any metadata filtering.

    Args:
        query (str): User's query string.
        top_k (int): Number of results to retrieve.

    Returns:
        List[Tuple]: Each tuple contains:
            (document, qdrant_score, reviews, price, rating)
    """
    logger.info(f"Performing semantic-only search (no metadata filtering) for query: '{query}'")
    return semantic_search(query=query, filter_obj=None, top_k=top_k)

# === COHERE RERANKER ===
def rerank_with_cohere(query: str, docs: List[Tuple]) -> List[Tuple]:
    """
    Re-rank a list of retrieved documents using Cohere's Rerank API.

    Args:
        query (str): The user's query.
        docs (List[Tuple]): A list of result tuples from Qdrant:
            (document, qdrant_score, reviews, price, rating)

    Returns:
        List[Tuple]: Same tuples, reordered and extended with Cohere relevance score:
            (document, qdrant_score, reviews, price, rating, cohere_score)
    """
    logger.info("🔁 Applying Cohere Reranker...")
    start = time.perf_counter()

    try:
        texts = [doc[0] for doc in docs]

        response = co.rerank(
            query=query,
            documents=texts,
            model=COHERE_MODEL,
            top_n=len(texts)
        )

        if len(response.results) != len(docs):
            logger.warning("⚠️ Cohere returned fewer results than expected. Falling back to original.")
            return docs

        reranked = [
            (*docs[r.index], r.relevance_score)
            for r in response.results
        ]

        def score_key(entry):
            return entry[5] if len(entry) > 5 else entry[1]

        reranked = sorted(reranked, key=score_key, reverse=True)

        logger.info("📊 Top 3 Reranked Results:")
        for i, (doc, _, _, price, rating, coh_score) in enumerate(reranked[:3]):
            logger.info(f"{i+1}. Score={coh_score:.4f} | Price=${price:.2f} | Rating={rating:.1f}")

        elapsed = time.perf_counter() - start
        logger.info(f"✅ Cohere reranking complete in {elapsed:.2f}s")

        return reranked

    except Exception as e:
        logger.warning(f"⚠️ Cohere reranking failed: {e}")
        return docs

# === PLANNER + SUMMARIZER ===
def generate_research_report(query: str, docs: list) -> str:
    """
    Generate a markdown-formatted product comparison report using LLM summarization.

    Args:
        query (str): Original user query.
        docs (list): List of ranked result tuples, including cohere_score if available.

    Returns:
        str: Markdown-formatted analysis and recommendations.
    """
    context = "\n\n---\n\n".join([
        f"Product Description: {doc}\nUser Reviews: {reviews}\nPrice: {price}\nRating: {rating}\nVector Score: {vector_score}\nCohere Score: {cohere_score}"
        for doc, vector_score, reviews, price, rating, cohere_score in docs
    ])
    user = f"User Query: {query}\n\nProducts:\n{context}"

    return call_chat(LLM_MODEL, RESEARCH_PROMPT, user)

# === END-TO-END PIPELINE ===
def search_pipeline(user_query: str, use_reranker: bool = False, use_tags: bool = True) -> str:
    """
    Full end-to-end pipeline for semantic product search with optional metadata filtering and reranking.

    Args:
        user_query (str): The user's product search question.
        use_reranker (bool): Whether to apply Cohere reranking after vector search.
        use_tags (bool): Whether to extract metadata tags and apply filtering.

    Returns:
        str: Markdown-formatted ranked result report.
    """
    tags = get_tags(user_query) if use_tags else []
    logger.info(f"Extracted tags: {tags}")

    filter_obj = build_metadata_filter(tags) if tags else None
    docs = semantic_search(user_query, filter_obj)

    if use_reranker:
        docs = rerank_with_cohere(user_query, docs)

    report = generate_research_report(user_query, docs)
    return report

# === CLI TEST ===
if __name__ == "__main__":
    q = "Find LEGO sets under $50 for kids aged 5–7"
    print("\n--- With Tag Filtering ---\n")
    print(search_pipeline(q, use_reranker=True, use_tags=True))

    print("\n--- Without Tag Filtering ---\n")
    print(search_pipeline(q, use_reranker=True, use_tags=False))
