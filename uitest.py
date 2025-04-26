import gradio as gr
import requests
from src.core.init_repo import process_repo_link


def init_repo(repo_link):
    """Send repository link to server and get initialization parameter"""
    try:
        cache_name = process_repo_link(repo_link)
        return {
            "repo_name": repo_link.split("/")[-1],
            "cache_id": cache_name,
        }, ""  # Return empty string for status message
    except Exception as e:
        return "", f"Error initializing repository: {str(e)}"


def respond(
    message, chat_history, model_name, repo_param={"repo_name": "", "cache_id": ""}
):
    history_text = ""
    if chat_history:
        for user_msg, bot_msg in chat_history:
            history_text += f"User: {user_msg}\nYou: {bot_msg}\n"
    else:
        chat_history = []

    history_text += f"User: {message}\n"
    payload = {
        "message": history_text,
        "model_name": model_name,
        "cache_id": repo_param["cache_id"],
        "repo_name": repo_param["repo_name"],
    }
    endpoint_url = "http://localhost:8000/generate"

    try:
        response = requests.post(endpoint_url, json=payload)
        response.raise_for_status()
        reply_text = response.json().get("response", "")
    except Exception as e:
        reply_text = "Error: Unable to get a response from the server."

    chat_history.append((message, reply_text))
    return chat_history


# Keep your original CSS configuration
custom_css = """
body {
    margin: 0 !important;
    padding: 0 !important;
}

#component-0 {
    max-width: 100% !important;
    padding: 0 !important;
    margin: 0 !important;
    background-color: #1a1a1a !important;
}

.main-container {
    height: 100vh !important;
    padding: 0 !important;
    margin: 0 !important;
}

/* Model selector styling */
#model-selector {
    position: fixed !important;
    top: 1rem !important;
    left: 1rem !important;
    z-index: 1000 !important;
    width: 200px !important;
    background-color: #252525 !important;
    border-radius: 8px !important;
    border: 1px solid #3a3a3a !important;
}

#model-selector select {
    background-color: #252525 !important;
    color: white !important;
    border: none !important;
    padding: 0.5rem !important;
}

#chatbot {
    height: calc(100vh - 160px) !important;
    background-color: #1a1a1a !important;
    border: none !important;
    border-radius: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
    margin-top: 80px !important;
}

#chatbot .message {
    padding: 1rem !important;
    margin: 0.5rem 1rem !important;
    border-radius: 8px !important;
    line-height: 1.6 !important;
    font-size: 15px !important;
    color: white !important;
    max-width: 80% !important;
}

#chatbot .user-message {
    background-color: #2d2d2d !important;
    margin-left: auto !important;
    margin-right: 1rem !important;
}

#chatbot .assistant-message {
    background-color: #252525 !important;
    margin-right: auto !important;
    margin-left: 1rem !important;
}

#input-container {
    position: fixed !important;
    bottom: 0 !important;
    left: 0 !important;
    right: 0 !important;
    padding: 1rem !important;
    background-color: #1a1a1a !important;
    border-top: 1px solid #252525 !important;
    z-index: 1000 !important;
    height: auto !important;
    box-sizing: border-box !important;
}

#input-box {
    height: 45px !important;
    border-radius: 8px !important;
    border: 1px solid #252525 !important;
    padding: 0.5rem 1rem !important;
    font-size: 15px !important;
    background-color: #252525 !important;
    color: white !important;
    transition: all 0.2s ease-in-out !important;
}

#input-box:focus {
    border-color: #3a3a3a !important;
    background-color: #2d2d2d !important;
}

#input-box::placeholder {
    color: #888888 !important;
}

#submit-btn {
    height: 45px !important;
    border-radius: 8px !important;
    padding: 0.5rem 1.5rem !important;
    font-size: 15px !important;
    background-color: #252525 !important;
    color: white !important;
    border: none !important;
    transition: all 0.2s ease-in-out !important;
}

#submit-btn:hover {
    background-color: #2d2d2d !important;
}

/* Scrollbar styling */
#chatbot::-webkit-scrollbar {
    width: 8px !important;
}

#chatbot::-webkit-scrollbar-track {
    background: #1a1a1a !important;
}

#chatbot::-webkit-scrollbar-thumb {
    background-color: #252525 !important;
    border-radius: 4px !important;
}

#chatbot::-webkit-scrollbar-thumb:hover {
    background-color: #2d2d2d !important;
}

/* Hide gradio elements we don't need */
footer {
    display: none !important;
}

/* Add minimal styling for repo input */
#repo-container {
    position: fixed !important;
    top: 1rem !important;
    left: 220px !important;
    right: 1rem !important;
    z-index: 1000 !important;
    background-color: #252525 !important;
    border-radius: 8px !important;
    border: 1px solid #3a3a3a !important;
    padding: 0.5rem !important;
}

/* Style for repo status message */
#repo-status {
    margin-top: 0.5rem !important;
    color: white !important;
    font-size: 14px !important;
    background-color: #2d2d2d !important;
    border-radius: 4px !important;
    padding: 0.5rem !important;
}
"""

# Create the Gradio interface
with gr.Blocks(css=custom_css, theme=gr.themes.Base()) as demo:
    repo_param = gr.State("")  # Store repo parameter

    with gr.Column(elem_id="main-container"):
        # Add model selector dropdown
        model_selector = gr.Dropdown(
            choices=[
                "gemini-1.5-flash-8b-001",
                "gemini-1.5-flash-002",
                "gemini-1.5-pro-002",
                "Custume Documentalist",
            ],
            value="gemini-1.5-flash-8b-001",
            label="Select Model",
            elem_id="model-selector",
        )

        # Add repository input
        with gr.Row(elem_id="repo-container"):
            repo_input = gr.Textbox(
                show_label=False, placeholder="Enter repository link", scale=8
            )
            repo_submit = gr.Button("Initialize", scale=1)

        chatbot = gr.Chatbot(
            elem_id="chatbot",
            label="Chat",
            height=None,
        )

        with gr.Column(elem_id="input-container"):
            with gr.Row():
                msg = gr.Textbox(
                    show_label=False,
                    placeholder="Message",
                    elem_id="input-box",
                    scale=9,
                )
                send_btn = gr.Button("Send", elem_id="submit-btn", scale=1)

            # Add repository status message under the input
            repo_message = gr.Textbox(
                show_label=False, interactive=False, elem_id="repo-status"
            )

    def user_input(user_message, chat_history, model_name, current_repo_param):
        if not user_message.strip():
            return "", chat_history
        return "", respond(
            user_message, chat_history or [], model_name, current_repo_param
        )

    # Handle repository initialization
    repo_submit.click(
        init_repo, inputs=[repo_input], outputs=[repo_param, repo_message]
    )

    # Update chat handlers to include repo parameter
    send_btn.click(
        user_input,
        inputs=[msg, chatbot, model_selector, repo_param],
        outputs=[msg, chatbot],
    )
    msg.submit(
        user_input,
        inputs=[msg, chatbot, model_selector, repo_param],
        outputs=[msg, chatbot],
    )

# Launch the app
demo.launch(
    share=False, debug=True, show_error=True, server_name="0.0.0.0", server_port=7865
)
