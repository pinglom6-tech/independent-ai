#!/usr/bin/env bash
set -Eeuo pipefail
mkdir -p /workspace
exec > >(tee -a /workspace/independent-ai-boot.log) 2>&1
echo "BOOTSTRAP_BEGIN $(date -u)"
export CHAT_UI_PASSWORD="${JUPYTER_PASSWORD:-}"
if [ -z "$CHAT_UI_PASSWORD" ]; then echo "ERROR: JUPYTER_PASSWORD missing"; exit 1; fi
export MODEL_ID="Qwen/Qwen3.5-27B-FP8"
export HF_HOME=/workspace/hf-cache
mkdir -p /tmp/independent-ai
curl -fsSL --retry 2 https://raw.githubusercontent.com/pinglom6-tech/independent-ai/main/chat-ui/gateway.py -o /tmp/independent-ai/gateway.py
curl -fsSL --retry 2 https://raw.githubusercontent.com/pinglom6-tech/independent-ai/main/chat-ui/index.html -o /tmp/independent-ai/index.html
python3 -u /tmp/independent-ai/gateway.py > /workspace/chat-ui.log 2>&1 &
echo "HTML_GATEWAY_STARTED port=8888"
# Never reinstall packages automatically: report missing runtime clearly.
if ! python3 -c 'import vllm' >/dev/null 2>&1; then
  echo "ERROR: vLLM is not installed in the existing Python environment. No installation attempted."
  exit 1
fi
echo "STARTING_EXISTING_MODEL_RUNTIME"
exec python3 -m vllm.entrypoints.openai.api_server --model "$MODEL_ID" --served-model-name "$MODEL_ID" --host 127.0.0.1 --port 8000 --max-model-len 8192 --gpu-memory-utilization 0.88
