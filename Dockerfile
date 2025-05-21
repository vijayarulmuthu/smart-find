<<<<<<< HEAD
# Get a distribution that has uv already installed
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

# Add Rust compiler installation
USER root
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Add user - this is the user that will run the app
# If you do not set user, the app will run as root (undesirable)
RUN useradd -m -u 1000 user
USER user

# Set up Rust for the user
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/home/user/.cargo/bin:${PATH}"

# Set the home directory and path
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH        

#ENV UVICORN_WS_PROTOCOL=websockets

# Set the working directory
WORKDIR $HOME/app

# Copy the app to the container
COPY --chown=user . .

# Install the dependencies
RUN uv sync

# Expose the port
EXPOSE 7860

# Run Gradio app
CMD ["uv", "run", "gradio", "app/ui_app.py"]
=======
# Base image with Python + pip
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=7860

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy app code
COPY . /app

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expose Chainlit default port
EXPOSE $PORT

# Command to run Chainlit app
CMD ["chainlit", "run", "ui_app.py", "--port", "7860", "--host", "0.0.0.0"]
>>>>>>> ebeedf8 (initial commit)
