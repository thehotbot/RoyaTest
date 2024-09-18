import os
from flask import Flask, render_template, request, jsonify
from openai import OpenAI
from openai_helpers import get_assistants, create_thread, add_message_to_thread, run_assistant, get_messages

app = Flask(__name__)

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
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
    data = request.json
    thread_id = data['thread_id']
    message = data['message']
    assistant_id = data['assistant_id']

    # Add user message to thread
    add_message_to_thread(client, thread_id, message)

    # Run the assistant
    run_assistant(client, thread_id, assistant_id)

    # Get updated messages
    messages = get_messages(client, thread_id)

    return jsonify({"messages": messages})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
