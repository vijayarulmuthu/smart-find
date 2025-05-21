def format_report(query: str, results: list) -> str:
    """
    Format a ranked list of product documents into a markdown SmartFind research report.

    Each tuple must be:
      (doc, original_score, reviews, price, rating [, cohere_score])
    """
    # Sort by reranked cohere_score if available, else fallback to vector_score
    def score_key(entry):
        return entry[5] if len(entry) > 5 else entry[1]  # cohere or original

    results = sorted(results, key=score_key, reverse=True)

    # Build blocks
    blocks = []
    for i, item in enumerate(results):
        doc, vec_score, reviews, price, rating, *rest = item
        coh_score = rest[0] if rest else None

        title = (
            "🏆 Top Recommendation" if i == 0 else
            f"🔹 Alternative #{i+1}"
        )

        score_line = f"**Relevance Score:** {coh_score:.4f}" if coh_score else f"**Vector Score:** {vec_score:.4f}"

        blocks.append(
            f"### {title}\n\n"
            f"{score_line}  \n"
            f"**Price:** ${price:.2f}  \n"
            f"**Rating:** {rating:.1f} ⭐  \n\n"
            f"**Product Description:**\n{doc.strip()}\n\n"
            f"**User Reviews:**\n{reviews.strip() if reviews else 'N/A'}"
        )

    markdown = f"## 🔍 SmartFind Research Report\n\n### Query\n> {query.strip()}\n\n---\n\n" + "\n\n---\n\n".join(blocks)
    return markdown
