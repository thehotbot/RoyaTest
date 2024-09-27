import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_session import Session
from openai import OpenAI
import logging
from werkzeug.security import generate_password_hash, check_password_hash
from openai_helpers import get_assistants, create_thread, add_message_to_thread, run_assistant, get_messages

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

logging.basicConfig(level=logging.DEBUG)

client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        stored_password = os.environ.get('LOGIN_PASSWORD')
        if password == stored_password:
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
def index():
    if not session.get('authenticated'):
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/get_assistants')
def get_assistants_route():
    if not session.get('authenticated'):
        return jsonify({"error": "Not authenticated"}), 401
    assistants = get_assistants(client)
    return jsonify(assistants)

@app.route('/create_thread', methods=['POST'])
def create_thread_route():
    if not session.get('authenticated'):
        return jsonify({"error": "Not authenticated"}), 401
    thread = create_thread(client)
    return jsonify({"thread_id": thread.id})

@app.route('/send_message', methods=['POST'])
def send_message():
    if not session.get('authenticated'):
        return jsonify({"error": "Not authenticated"}), 401
    try:
        data = request.json
        thread_id = data.get('thread_id')
        message = data.get('message')
        assistant_id = data.get('assistant_id')

        if not thread_id or not message or not assistant_id:
            return jsonify({"error": "Missing required parameters"}), 400

        add_message_to_thread(client, thread_id, message)
        run = run_assistant(client, thread_id, assistant_id)
        messages = get_messages(client, thread_id)

        if messages:
            return jsonify({"message": messages[0]})
        else:
            return jsonify({"error": "No messages found"}), 404
    except Exception as e:
        logging.exception(f"Error in send_message: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3001))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    logging.info(f"Starting Flask server on port {port} with debug={debug}")
    app.run(host='0.0.0.0', port=port, debug=debug)
