#!/usr/bin/env bash
set -euo pipefail
mkdir -p /workspace/independent-ai /workspace/hf-cache
python3 -m pip install --upgrade uv
uv pip install --system vllm --torch-backend=auto --extra-index-url https://wheels.vllm.ai/nightly
python3 -m pip install --upgrade huggingface_hub
cat > /workspace/independent-ai/start-model.sh &lt;&lt;'EOF'
#!/usr/bin/env bash
set -euo pipefail
export HF_HOME=/workspace/hf-cache
exec vllm serve Qwen/Qwen3.5-27B --host 127.0.0.1 --port 8000 --language-model-only --max-model-len 8192 --gpu-memory-utilization 0.85 --quantization bitsandbytes --load-format bitsandbytes
EOF
chmod +x /workspace/independent-ai/start-model.sh
echo 'Installed vLLM and created model launch script; model not yet downloaded or started.'
