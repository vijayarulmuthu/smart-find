# Attribute-Aware Semantic Product Search

## Problem Statement

E-commerce product managers struggle to deliver precise and context-aware search experiences because traditional search pipelines fail to effectively interpret user intent and product attributes.

### User Persona

* **Role**: E-Commerce Product Manager / Search Product Lead
* **Responsibility**: Improving site search UX and product discovery
* **Pain Points**:

  * Keyword search lacks context
  * Semantic search misses key filters like price, material, brand
  * Hybrid search doesn't decompose queries or leverage structured metadata

### Common Questions

* "Find LEGO sets under \$50 for kids aged 5–7"
* "What are the best wooden educational toys for toddlers?"
* "Can I see puzzles for 3-year-olds with 4+ star reviews?"
* "Show all STEM toys made of plastic under \$25"

---

## Proposed Solution

We will build a next-generation semantic product search engine powered by **Query Attribute Modeling (QAM)**. The pipeline first uses an LLM to decompose the query into structured metadata (tags like price, brand, category), filters candidate documents using this metadata in Qdrant, then performs semantic retrieval on rich RAG documents. Finally, results are reranked using Cohere.

The end-user benefits from fast, context-aware, and relevant results — whether they search by keyword, description, or preference.

### Tooling Stack

* **LLM**: `gpt-4.1` – Query decomposition, tag generation
* **Embedding Model**: `text-embedding-3-small` – Lightweight, scalable vector encoding
* **Vector DB**: `Qdrant` – Fast semantic search with metadata filtering
* **Reranker**: `Cohere Rerank` – Final precision-optimized ranking
* **UI**: `Gradio` – Interactive front-end for LLM product search

---

## Architecture
![alt text](./images/architecture.png)

### 1️⃣ Feature Extraction Pipeline

- Drops rows with missing price/rating
- Parses price and rating fields
- Constructs structured **markdown-style RAG documents**
- Produces a cleaned CSV: `rag_document`, `price`, `rating`

---

### 2️⃣ Ingest Pipeline

- 🔖 Uses OpenAI + LLMs to auto-generate **metadata tags** (category, age group, material, etc.)
- 🔢 Generates embeddings using `text-embedding-3-small`
- 🚀 Ingests into Qdrant with vector + metadata payloads
- 🔐 Index is built using **HNSW** for fast similarity search

---

### 3️⃣ Search Pipeline

- Accepts free-form user queries
- Optionally performs **tag extraction** for filtering
- Performs vector similarity search via Qdrant
- Optionally applies **semantic reranking (Cohere)**
- Appends product info (name + rating + price) to prompt
- Uses GPT-4.1-mini to generate **final product recommendation markdown**

---

## ⚠️ Optimization Opportunities

- **Embedding Size Variation**: Consider chunking or dual-indexing (short + long form)
- **LLM Bottlenecks**: Summarization and reranking can be parallelized or batched
- **Local Qdrant Locking**: Use remote Qdrant for concurrent multi-process access
- **Telemetry**: Track reranker quality, filter miss rates, and user feedback
- **Tagging Model**: Replace LLM tagger with fast lightweight classifier if needed