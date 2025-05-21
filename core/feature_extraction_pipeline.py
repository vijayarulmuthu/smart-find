# core/feature_extraction_pipeline.py
import uuid
import pandas as pd
import logging
from pathlib import Path

from utils.llm_utils import build_rag_document, clean_rag_document

# === CONFIG ===
INPUT_PATH = "./data/amazon_co-ecommerce_sample.csv"
OUTPUT_PATH = "./data/rag_docs.csv"
RAG_FIELDS = ["product_name", "product_description", "description", "product_information", "price", "average_review_rating", "customer_reviews"]

# === LOGGING SETUP ===
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("feature_extraction_pipeline")

# === PIPELINE ===
def run_feature_extraction(input_path=INPUT_PATH, output_path=OUTPUT_PATH):
    if not Path(input_path).exists():
        logger.error(f"Input file not found: {input_path}")
        return

    df = pd.read_csv(input_path)
    logger.info(f"Loaded input CSV with shape: {df.shape}")

    # Drop rows where all RAG-relevant fields are missing
    df_rag = df.dropna(subset=RAG_FIELDS, how="all").copy()
    logger.info(f"Filtered to {len(df_rag)} rows with RAG-relevant content")

    # Clean price: remove currency symbols and convert to float
    df_rag["price"] = df_rag["price"].replace(r"[£$,]", "", regex=True).replace(" ", "").astype(str)
    df_rag["price"] = pd.to_numeric(df_rag["price"], errors="coerce")

    # Clean rating: extract numeric value from text like '4.9 out of 5 stars'
    df_rag.rename(columns={"average_review_rating": "rating"}, inplace=True)
    df_rag["rating"] = df_rag["rating"].astype(str).str.extract(r"([\\d\\.]+)").astype(float)

    # RAG document construction
    df_rag["rag_document"] = df_rag.apply(build_rag_document, axis=1)
    df_rag["rag_document"] = df_rag["rag_document"].apply(clean_rag_document)

    # UUIDs
    df_rag["uniq_id"] = df_rag.get("uniq_id", pd.Series(dtype=str)).fillna("").apply(
        lambda x: x if x else str(uuid.uuid4())
    )

    # Save selected fields
    df_rag[["uniq_id", "product_name", "price", "rating", "customer_reviews", "rag_document"]].to_csv(output_path, index=False)
    logger.info(f"Saved RAG-ready dataset to {output_path} ({len(df_rag)} rows)")

# === CLI EXECUTION ===
if __name__ == "__main__":
    run_feature_extraction()
