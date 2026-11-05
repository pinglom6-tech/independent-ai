import os
import gradio as gr
from openai import OpenAI

client = OpenAI(base_url=os.getenv("MODEL_URL", "http://127.0.0.1:8000/v1"), api_key="local")
MODEL = os.getenv("MODEL_ID", "Qwen/Qwen3.5-27B")

def respond(message, history):
    messages = []
    for item in history:
        if item.get("role") in ("user", "assistant") and isinstance(item.get("content"), str):
            messages.append({"role": item["role"], "content": item["content"]})
    messages.append({"role": "user", "content": message})
    result = client.chat.completions.create(model=MODEL, messages=messages, max_tokens=1024, temperature=0.7)
    return result.choices[0].message.content or ""

app = gr.ChatInterface(fn=respond, type="messages", title="Independent AI", description="Private Qwen chatbot", chatbot=gr.Chatbot(type="messages", height=520))
if __name__ == "__main__":
    app.launch(server_name="0.0.0.0", server_port=7860, show_error=True)
