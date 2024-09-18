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

        # Get only the last message
        messages = get_messages(client, thread_id)
        logging.debug(f"Retrieved messages: {messages}")
        last_message = messages[0] if messages else None
        logging.debug(f"Last message: {last_message}")

        if last_message is None:
            logging.error("No messages retrieved from the thread")
            return jsonify({"error": "No response from assistant"}), 500

        if last_message['role'] != 'assistant':
            logging.error(f"Last message is not from assistant: {last_message}")
            return jsonify({"error": "Unexpected response from assistant"}), 500

        logging.debug(f"Sending assistant response: {last_message}")
        return jsonify({"message": last_message})
    except Exception as e:
        logging.error(f"Error in send_message: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
