import os
import re
import json
import openai
import logging

from typing import List
from dotenv import load_dotenv

# Load API keys from .env
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Logger setup
logger = logging.getLogger("llm_utils")
logging.basicConfig(level=logging.INFO)

# === Embedding Utility ===
def get_embedding(text: str, model: str = "text-embedding-3-small") -> List[float]:
    try:
        response = openai.embeddings.create(input=text, model=model)
        return response.data[0].embedding
    except Exception as e:
        logger.warning(f"[Embedding Error] {e}")
        return [0.0] * 1536   # Fallback vector


# === Safe JSON Parse Utility ===
def safe_json_parse(content: str, key: str = "tags", fallback: str = "misc") -> List[str]:
    try:
        parsed = json.loads(content)
        return parsed.get(key, [fallback]) if isinstance(parsed.get(key, []), list) else [fallback]
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            try:
                parsed = json.loads(match.group(0))
                return parsed.get(key, [fallback]) if isinstance(parsed.get(key, []), list) else [fallback]
            except Exception:
                return [fallback]
        return [fallback]


# === Chat Completion Wrapper ===
def call_chat(model: str, system_prompt: str, user_input: str, temperature: float = 0.3) -> str:
    try:
        response = openai.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            temperature=temperature
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"[ChatCompletion Error] {e}")
        return "{}"  # Return empty JSON as fallback


# === Build Markdown RAG Document ===
def build_rag_document(row) -> str:
    """
    Build a markdown-formatted RAG document from structured product row fields.
    Expected keys in row: product_name, product_description, description, product_information
    """
    sections = []
    name = row.get("product_name")
    desc = row.get("product_description") or row.get("description")
    info = row.get("product_information")

    if name:
        sections.append(f"### Product Name\n{name}")
    if desc:
        sections.append(f"### Description\n{desc}")
    if info:
        sections.append(f"### Product Information\n{info}")

    return "\n\n".join(sections)

# === Clean RAG Document ===
def clean_rag_document(doc: str) -> str:
    """
    Cleans noisy JavaScript and Amazon-specific clutter from product RAG documents.
    """
    # Remove embedded JavaScript snippets
    doc = re.sub(r"amznJQ\.onReady\([\s\S]*?\)\);", "", doc)
    doc = re.sub(r"\(function\(\$.*?\}\)\(\$.*?\);", "", doc)
    
    # Remove redundant 'Customer Reviews' JS junk
    doc = re.sub(r"Customer Reviews[\s\S]+?(?:\d+ out of 5 stars|See all reviews)", "", doc)

    # Remove Amazon popover configs and trailing JS
    doc = re.sub(r"window\.reviewHistPopoverConfig[\s\S]*?onCacheUpdateReselect_average_customer_reviews.*?\);", "", doc)

    # Remove stray HTML/JS tail
    doc = re.sub(r"(Feedback\s+Would you like to update product info.*)", "", doc)

    # Collapse excessive spacing
    doc = re.sub(r"\n{2,}", "\n\n", doc).strip()

    return doc
