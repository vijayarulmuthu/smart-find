import modal

# Define the Modal app
app = modal.App(name="smartfind")
app.image = modal.Image.debian_slim().pip_install_from_pyproject("pyproject.toml")

# Secrets from .env (OpenAI, Cohere, etc.)
secrets = modal.Secret.from_dotenv()

# Register web server function with mount
@app.function(secrets=[secrets], timeout=600)
@modal.web_server(port=7860)
def run():
    import gradio_app
    gradio_app.demo.launch(server_name="0.0.0.0", server_port=7860, share=False)
