import os
from dotenv import load_dotenv

load_dotenv()

for key in ("API_BASE", "API_KEY", "BRAIN_MODEL"):
    if not os.getenv(key):
        raise ValueError(
            f"{key} is not set. Please copy .env.example to .env and fill in your configuration."
        )

os.makedirs("data", exist_ok=True)
os.makedirs("cache", exist_ok=True)

import gradio as gr
from llm_client import LLMClient
from brain import Brain
from page_functions import *

os.environ["NO_PROXY"] = "127.0.0.1,localhost,::1"
os.environ["no_proxy"] = "127.0.0.1,localhost,::1"
for k in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"]:
    os.environ.pop(k, None)

brain_client = LLMClient(os.getenv("API_BASE"), os.getenv("API_KEY"), os.getenv("BRAIN_MODEL"))
brain = Brain(brain_client)
with gr.Blocks(title="Filtering Agent") as demo:
    webpage_title ="""
    <div style="text-align: center; margin: 20px 0;">
        <span style="font-size: 2.5em; font-weight: bold; color: #2c3e50;">
            Filtering Agent
        </span>
    </div>
    """
    gr.Markdown(webpage_title)
    arg_brain = gr.State({"brain":brain})
    arg_paras = gr.State({ "mode":"_FILTER" })
    chat = gr.Chatbot(height=520, label="Filtering Agent", value=[("Start chat!","Please enter the database download requirements.")])
    user_msg = gr.Textbox(
        placeholder="Enter the data download requirements.",
        label="Chat with Filtering Agent",
    )
    file_output = gr.File(label="Download the result file.")
    clear_file_btn = gr.Button("🗑️ Delete")
    user_msg.submit(
        text_submit,
        [chat, user_msg, arg_brain, arg_paras],
        [chat, user_msg, arg_brain, arg_paras, file_output]
    )
    def clear_file():
        return None 
    clear_file_btn.click(
        clear_file,
        inputs=None,
        outputs=file_output
    )
demo.launch(server_name="localhost", server_port=8080, share=False, show_error=True) 