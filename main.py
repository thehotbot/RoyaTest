import os
import logging
import time
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_session import Session
from functools import wraps
from openai import OpenAI
from openai_helpers import get_assistants, create_thread, add_message_to_thread, run_assistant, get_messages

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logging.error("OPENAI_API_KEY is not set in the environment variables")
    raise ValueError("OPENAI_API_KEY is not set")

client = OpenAI(api_key=OPENAI_API_KEY)

# Session configuration
app.config['SECRET_KEY'] = 'your_secret_key_here'  # Replace with a real secret key
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'authenticated' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == 'your_password_here':  # Replace with a real password
            session['authenticated'] = True
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Invalid password')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('authenticated', None)
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/get_assistants', methods=['GET'])
@login_required
def fetch_assistants():
    assistants = get_assistants(client)
    return jsonify(assistants)

@app.route('/create_thread', methods=['POST'])
@login_required
def new_thread():
    thread = create_thread(client)
    return jsonify({"thread_id": thread.id})

@app.route('/send_message', methods=['POST'])
@login_required
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

        # Get all messages
        messages = get_messages(client, thread_id)
        logging.debug(f"All messages retrieved: {messages}")

        # Get the last assistant message
        last_assistant_message = next((msg for msg in messages if msg['role'] == 'assistant'), None)

        if not last_assistant_message:
            logging.error("No assistant message found in the thread")
            return jsonify({"error": "No response from assistant"}), 500

        logging.debug(f"Last assistant message: {last_assistant_message}")

        return jsonify({"message": last_assistant_message})

    except Exception as e:
        logging.error(f"Error in send_message: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
