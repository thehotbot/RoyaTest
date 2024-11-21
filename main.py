import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_session import Session
from openai import OpenAI
import logging
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from openai_helpers import get_assistants, create_thread, add_message_to_thread, run_assistant, get_messages
import dotenv
import socket

from utils.logging_config import setup_logging, RequestLoggingMiddleware

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)
setup_logging(app)
app.wsgi_app = RequestLoggingMiddleware(app.wsgi_app)

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB max file size
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Create upload folder with error handling
try:
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.logger.info(f"Upload directory created/verified at {app.config['UPLOAD_FOLDER']}")
except Exception as e:
    app.logger.error(f"Failed to create upload directory: {e}")
    raise

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('0.0.0.0', port))
            return False
        except socket.error:
            return True

def find_available_port(start_port, max_attempts=10):
    """Find an available port with retry mechanism and better logging"""
    port = start_port
    attempt = 0
    
    while attempt < max_attempts:
        if not is_port_in_use(port):
            app.logger.info(f"Found available port: {port}")
            return port
        
        attempt += 1
        port += 1
        app.logger.warning(f"Port {port-1} is in use, trying port {port} (attempt {attempt}/{max_attempts})")
    
    app.logger.error(f"Failed to find available port after {max_attempts} attempts")
    # Return the initial port and let the server handle the error
    return start_port

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_openai_client():
    api_key = session.get('openai_api_key') or os.environ.get('OPENAI_API_KEY')
    return OpenAI(api_key=api_key)

def update_env_var(key, value):
    """Update environment variable in .env file and current session"""
    env_path = '.env'
    try:
        # Read existing .env file
        env_vars = {}
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                for line in f:
                    if '=' in line:
                        k, v = line.strip().split('=', 1)
                        env_vars[k] = v

        # Update the variable
        env_vars[key] = value

        # Write back to .env file
        with open(env_path, 'w') as f:
            for k, v in env_vars.items():
                f.write(f'{k}={v}\n')

        # Update runtime environment
        os.environ[key] = value
        
        return True
    except Exception as e:
        logging.error(f"Failed to update environment variable: {e}")
        return False

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        stored_password = os.environ.get('LOGIN_PASSWORD')
        if password == stored_password:
            session['authenticated'] = True
            # Set default colors if not already set
            if 'bg_color' not in session:
                session['bg_color'] = '#141E33'
            if 'accent_color' not in session:
                session['accent_color'] = '#FD4C00'
            return redirect(url_for('index'))
        else:
            return render_template('login.html', 
                                error='Invalid password',
                                bg_color=session.get('bg_color', '#141E33'),
                                accent_color=session.get('accent_color', '#FD4C00'))
    return render_template('login.html',
                         bg_color=session.get('bg_color', '#141E33'),
                         accent_color=session.get('accent_color', '#FD4C00'))

@app.route('/logout')
def logout():
    session.pop('authenticated', None)
    return redirect(url_for('login'))

@app.route('/')
def index():
    if not session.get('authenticated'):
        return redirect(url_for('login'))
    return render_template('index.html', 
                         bg_color=session.get('bg_color', '#141E33'),
                         accent_color=session.get('accent_color', '#FD4C00'))

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if not session.get('authenticated'):
        return redirect(url_for('login'))
    
    # Get API key from session or environment
    current_api_key = session.get('openai_api_key') or os.environ.get('OPENAI_API_KEY', '')
    
    if request.method == 'POST':
        settings_updated = False

        # Handle Password Change
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if current_password and new_password and confirm_password:
            stored_password = os.environ.get('LOGIN_PASSWORD')
            
            # Verify current password
            if current_password != stored_password:
                flash('Current password is incorrect.', 'error')
                return redirect(url_for('settings'))

            # Verify new password confirmation
            if new_password != confirm_password:
                flash('New passwords do not match.', 'error')
                return redirect(url_for('settings'))

            # Update password in environment and .env file
            if update_env_var('LOGIN_PASSWORD', new_password):
                flash('Password updated successfully!', 'success')
                settings_updated = True
            else:
                flash('Failed to update password. Please try again.', 'error')
                return redirect(url_for('settings'))

        # Update OpenAI API Key
        openai_api_key = request.form.get('openai_api_key')
        if openai_api_key:
            try:
                # Test the API key by making a simple API call
                test_client = OpenAI(api_key=openai_api_key)
                test_client.models.list()  # Simple API call to verify the key
                session['openai_api_key'] = openai_api_key
                settings_updated = True
                flash('OpenAI API key updated successfully!', 'success')
            except Exception as e:
                flash('Invalid OpenAI API key. Please check and try again.', 'error')
                return redirect(url_for('settings'))

        # Update Colors
        bg_color = request.form.get('bg_color')
        accent_color = request.form.get('accent_color')
        
        if bg_color:
            session['bg_color'] = bg_color
            settings_updated = True
        if accent_color:
            session['accent_color'] = accent_color
            settings_updated = True

        # Handle Logo Upload
        if 'logo' in request.files:
            file = request.files['logo']
            # Only validate if a file is actually uploaded (has content)
            if file and file.filename:
                # Validate file type
                if not allowed_file(file.filename):
                    flash('Invalid file type. Please upload a valid image file (PNG, JPG, JPEG, or GIF).', 'error')
                    return redirect(url_for('settings'))
                
                try:
                    # Check file size
                    file_content = file.read()
                    file.seek(0)  # Reset file pointer after reading
                    
                    if len(file_content) > MAX_CONTENT_LENGTH:
                        flash('File size too large. Maximum size is 5MB.', 'error')
                        return redirect(url_for('settings'))

                    filename = secure_filename(file.filename)
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)
                    session['logo_path'] = f'uploads/{filename}'
                    settings_updated = True
                except Exception as e:
                    logging.error(f"File upload error: {e}")
                    flash('Failed to upload logo. Please try again.', 'error')
                    return redirect(url_for('settings'))

        # Show success message only if any setting was updated
        if settings_updated:
            flash('Settings updated successfully!', 'success')
        
        return redirect(url_for('settings'))

    return render_template('settings.html',
                         bg_color=session.get('bg_color', '#141E33'),
                         accent_color=session.get('accent_color', '#FD4C00'),
                         openai_api_key=current_api_key)

@app.route('/get_assistants')
def get_assistants_route():
    if not session.get('authenticated'):
        return jsonify({"error": "Not authenticated"}), 401
    client = get_openai_client()
    assistants = get_assistants(client)
    return jsonify(assistants)

@app.route('/create_thread', methods=['POST'])
def create_thread_route():
    if not session.get('authenticated'):
        return jsonify({"error": "Not authenticated"}), 401
    client = get_openai_client()
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

        client = get_openai_client()
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
    # Load environment variables
    dotenv.load_dotenv()
    
    # Configure port
    default_port = int(os.environ.get('PORT', 5000))
    port = find_available_port(default_port)
    
    if port != default_port:
        app.logger.info(f"Default port {default_port} was in use, using port {port} instead")
    
    # Log startup information
    app.logger.info(f"Starting Flask server on port {port}")
    app.logger.info(f"Server will be accessible at http://0.0.0.0:{port}")
    
    try:
        app.run(
            host='0.0.0.0',
            port=port,
            debug=False,
            use_reloader=False  # Disable reloader to prevent double startup
        )
    except Exception as e:
        app.logger.error(f"Failed to start server: {e}")
        raise