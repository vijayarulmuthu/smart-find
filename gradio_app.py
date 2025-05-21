import gradio as gr
from core.search_pipeline import search_pipeline

# === MAIN FUNCTION ===
def run_search(query, use_tags):
    try:
        markdown_response = search_pipeline(query, use_reranker=True, use_tags=use_tags)

        if not markdown_response or len(markdown_response.strip()) < 10:
            return "⚠️ No results found. Try refining your query."

        return markdown_response
    except Exception as e:
        return f"❌ Search failed: {e}"

# === UI COMPONENTS ===
with gr.Blocks(title="SmartFind AI") as demo:
    gr.Markdown("""
    # 🔍 SmartFind: Attribute-Aware Semantic Product Search

    Enter a product search query and choose your search mode:

    ## 💡 Sample Queries:
    - Find LEGO sets under $50 for kids aged 5–7
    - What are the best wooden educational toys for toddlers?
    - Top-rated toys for preschoolers
    - Show toys for 8-year-olds rated above 4.5 stars
    - Find STEM kits for 3-year-olds with 4+ star reviews
    - STEM kits for kids between $30 and $60
    - Highly rated board games for families
    - Puzzles with 4+ star reviews for toddlers
    """)

    with gr.Tabs():
        with gr.TabItem("🔎 SmartFind (with Tags)"):
            query_input_smart = gr.Textbox(label="Your Query", placeholder="e.g., LEGO sets under $50 for kids aged 5–7")
            run_btn_smart = gr.Button("Run SmartFind Search")
            output_smart = gr.Markdown(label="Search Results")
            run_btn_smart.click(fn=lambda q: run_search(q, use_tags=True), inputs=query_input_smart, outputs=output_smart)

        with gr.TabItem("🧠 Pure Semantic (no Tags)"):
            query_input_semantic = gr.Textbox(label="Your Query", placeholder="e.g., LEGO sets under $50 for kids aged 5–7")
            run_btn_semantic = gr.Button("Run Semantic Search")
            output_semantic = gr.Markdown(label="Search Results")
            run_btn_semantic.click(fn=lambda q: run_search(q, use_tags=False), inputs=query_input_semantic, outputs=output_semantic)

# === LAUNCH ===
if __name__ == "__main__":
    demo.launch(share=True)
