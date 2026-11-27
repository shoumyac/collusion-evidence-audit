"""Serve an open-weight model behind an OpenAI-compatible endpoint on Modal, for the games runner.

    pip install modal
    modal setup                                   # once per account
    modal deploy games/modal_vllm.py              # prints the endpoint URL
    # then, in the shell that runs the games:
    #   LLM_BASE_URL=<url>/v1  python -m games.runner --backend openai --model Qwen/Qwen3-8B ...
    modal app stop collusion-vllm                 # when done, so nothing keeps billing

Edit MODEL and GPU below. A single 8B model fits on one A100 40GB or L40S. Check Modal's current GPU prices before a big run.
"""
import subprocess

import modal

MODEL = "Qwen/Qwen3-8B"
GPU = "A100-40GB"
PORT = 8000
MINUTES = 60

image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install("vllm==0.10.2", "huggingface_hub")
)
hf_cache = modal.Volume.from_name("collusion-hf-cache", create_if_missing=True)
app = modal.App("collusion-vllm")


@app.function(
    image=image,
    gpu=GPU,
    scaledown_window=5 * MINUTES,  # shuts the GPU down 5 minutes after the last request
    timeout=60 * MINUTES,
    volumes={"/root/.cache/huggingface": hf_cache},
)
@modal.concurrent(max_inputs=64)
@modal.web_server(port=PORT, startup_timeout=10 * MINUTES)
def serve():
    cmd = ["vllm", "serve", MODEL, "--host", "0.0.0.0", "--port", str(PORT),
           "--max-model-len", "16384", "--enable-prefix-caching", "--gpu-memory-utilization", "0.92"]
    subprocess.Popen(" ".join(cmd), shell=True)
