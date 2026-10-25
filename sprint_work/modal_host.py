"""Our own minimal vLLM-on-Modal host (the starter's poseidon_compute.modal_serve OOMs the KV cache on an A10G
because it does not cap --max-model-len). Same image and secrets as the starter; adds a context cap and concurrency.
"""
import contextlib
import os
import subprocess
import time
import urllib.request

import modal

MODEL = os.environ.get("HOST_MODEL", "Qwen/Qwen2.5-7B-Instruct")
GPU = os.environ.get("HOST_GPU", "A10G")
MAXLEN = os.environ.get("HOST_MAXLEN", "4096")
PORT = 8000

app = modal.App("collusion-audit-host")
image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install("vllm==0.6.6", "huggingface_hub[hf_transfer]==0.26.2")
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1"})
)
secrets = [modal.Secret.from_name("huggingface"), modal.Secret.from_name("modal-serve"),
           modal.Secret.from_dict({"HOST_MODEL_RT": MODEL, "HOST_MAXLEN_RT": MAXLEN})]  # reaches the container (local env does not)


@app.function(image=image, gpu=GPU, timeout=6 * 3600, scaledown_window=120, secrets=secrets, max_containers=1)
@modal.concurrent(max_inputs=64)
@modal.web_server(port=PORT, startup_timeout=1200, label=os.environ.get("HOST_LABEL") or None)
def serve():
    model = os.environ.get("HOST_MODEL_RT", MODEL)
    maxlen = os.environ.get("HOST_MAXLEN_RT", MAXLEN)
    cmd = ["python", "-m", "vllm.entrypoints.openai.api_server", "--model", model, "--host", "0.0.0.0",
           "--port", str(PORT), "--served-model-name", model, "--max-model-len", maxlen,
           "--gpu-memory-utilization", "0.92"]
    key = os.environ.get("MODAL_SERVE_API_KEY")
    if key:
        cmd += ["--api-key", key]
    subprocess.Popen(" ".join(cmd), shell=True)


@contextlib.contextmanager
def hosted(api_key, ready_timeout=1200):
    with modal.enable_output(), app.run():
        url = serve.get_web_url()
        base = url.rstrip("/") + "/v1"
        os.environ["LLM_BASE_URL"], os.environ["LLM_API_KEY"] = base, api_key
        req = urllib.request.Request(base + "/models", headers={"Authorization": f"Bearer {api_key}"})
        deadline = time.time() + ready_timeout
        while True:
            try:
                with urllib.request.urlopen(req, timeout=10) as r:
                    if r.status == 200:
                        break
            except Exception:
                pass
            if time.time() > deadline:
                raise TimeoutError("vLLM endpoint not ready")
            time.sleep(5)
        print("[host] ready", base, flush=True)
        yield base
