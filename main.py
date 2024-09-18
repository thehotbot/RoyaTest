import os
import logging
import time
from flask import Flask, render_template, request, jsonify
from openai import OpenAI
from openai_helpers import get_assistants, create_thread, add_message_to_thread, run_assistant, get_messages

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logging.error("OPENAI_API_KEY is not set in the environment variables")
    raise ValueError("OPENAI_API_KEY is not set")

client = OpenAI(api_key=OPENAI_API_KEY)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_assistants', methods=['GET'])
def fetch_assistants():
    assistants = get_assistants(client)
    return jsonify(assistants)

@app.route('/create_thread', methods=['POST'])
def new_thread():
    thread = create_thread(client)
    return jsonify({"thread_id": thread.id})

@app.route('/send_message', methods=['POST'])
def send_message():
    try:
        data = request.json
        thread_id = data['thread_id']
        message = data['message']
        assistant_id = data['assistant_id']

        logging.debug(f"Received message: {message} for thread: {thread_id} and assistant: {assistant_id}")

        # Add user message to thread
        user_message = add_message_to_thread(client, thread_id, message)
        logging.debug(f"Added user message: {user_message}")

        # Run the assistant
        run = run_assistant(client, thread_id, assistant_id)
        logging.debug(f"Assistant run completed: {run}")

        # Add a small delay
        time.sleep(2)

        # Get all messages
        messages = get_messages(client, thread_id)
        logging.debug(f"All messages: {messages}")
        for msg in messages:
            logging.debug(f"Message: {msg}")

        if not any(msg['role'] == 'assistant' for msg in messages):
            logging.error("No assistant message found in the thread")
            return jsonify({"error": "No response from assistant"}), 500

        last_assistant_message = next((msg for msg in messages if msg['role'] == 'assistant'), None)
        if last_assistant_message:
            logging.debug(f"Last assistant message: {last_assistant_message}")
            return jsonify({"message": last_assistant_message})
        else:
            logging.error("Unexpected state: assistant message not found after check")
            return jsonify({"error": "Unexpected response from assistant"}), 500

    except Exception as e:
        logging.error(f"Error in send_message: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
