#!/usr/bin/env bash
set -Eeuo pipefail
exec > >(tee -a /workspace/independent-ai-boot.log) 2>&1
set -x
echo "BOOTSTRAP_BEGIN $(date -u)"
# Avoid git clone on RunPod network volume: its chmod operations are unsupported.
mkdir -p /workspace/independent-ai
cd /workspace/independent-ai
curl -fL --retry 3 --connect-timeout 15 https://github.com/pinglom6-tech/independent-ai/archive/refs/heads/main.tar.gz -o /tmp/independent-ai.tar.gz
tar -xzf /tmp/independent-ai.tar.gz -C /workspace/independent-ai --strip-components=1
echo PROJECT_EXTRACTED
python3 -m venv --system-site-packages /workspace/independent-ai-venv
source /workspace/independent-ai-venv/bin/activate
python -m pip install -U pip
python -m pip install -U gradio openai
export CHAT_UI_PASSWORD="${JUPYTER_PASSWORD:-}"
if [ -z "$CHAT_UI_PASSWORD" ]; then echo "ERROR: JUPYTER_PASSWORD missing"; exit 1; fi
export MODEL_ID="Qwen/Qwen3.5-27B-FP8"
export MODEL_URL="http://127.0.0.1:8000/v1"
# Start UI independently so it is reachable while the model downloads and loads.
sed -i 's/server_port=7860/server_port=8888/' chat-ui/app.py
python -u chat-ui/app.py > /workspace/chat-ui.log 2>&1 &
UI_PID=$!
echo "CHAT_UI_STARTED pid=$UI_PID"
python -m pip install -U 'vllm>=0.15.0'
echo "STARTING_MODEL"
export HF_HOME=/workspace/hf-cache
python -m vllm.entrypoints.openai.api_server --model "$MODEL_ID" --served-model-name "$MODEL_ID" --host 127.0.0.1 --port 8000 --max-model-len 8192 --gpu-memory-utilization 0.88
