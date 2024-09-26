import os
import logging
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_session import Session
from werkzeug.security import check_password_hash
from openai import OpenAI
import openai_helpers
from functools import wraps

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logging.error("OPENAI_API_KEY is not set in the environment variables")
    raise ValueError("OPENAI_API_KEY is not set")

LOGIN_PASSWORD = os.environ.get("LOGIN_PASSWORD")
if not LOGIN_PASSWORD:
    logging.error("LOGIN_PASSWORD is not set in the environment variables")
    raise ValueError("LOGIN_PASSWORD is not set")

app.config['SECRET_KEY'] = os.urandom(24)
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

client = OpenAI(api_key=OPENAI_API_KEY)

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
        if check_password_hash(LOGIN_PASSWORD, password):
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
    assistants = openai_helpers.get_assistants(client)
    return jsonify(assistants)

@app.route('/create_thread', methods=['POST'])
@login_required
def new_thread():
    thread = openai_helpers.create_thread(client)
    return jsonify({"thread_id": thread.id})

@app.route('/send_message', methods=['POST'])
@login_required
def send_message():
    try:
        data = request.json
        thread_id = data['thread_id']
        message = data['message']
        assistant_id = data['assistant_id']

        logging.info(f"Received message for thread: {thread_id} and assistant: {assistant_id}")

        user_message = openai_helpers.add_message_to_thread(client, thread_id, message)
        logging.info(f"Added user message: {user_message}")

        run = openai_helpers.run_assistant(client, thread_id, assistant_id)
        logging.info(f"Assistant run completed: {run}")

        messages = openai_helpers.get_messages(client, thread_id)
        logging.info(f"All messages retrieved: {len(messages)}")

        last_assistant_message = next((msg for msg in messages if msg['role'] == 'assistant'), None)

        if not last_assistant_message:
            logging.error("No assistant message found in the thread")
            return jsonify({"error": "No response from assistant"}), 500

        logging.info(f"Last assistant message retrieved")

        return jsonify({"message": last_assistant_message})

    except Exception as e:
        logging.exception(f"Error in send_message: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3001))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    logging.info(f"Starting Flask server on port {port} with debug={debug}")
    app.run(host='0.0.0.0', port=port, debug=debug)